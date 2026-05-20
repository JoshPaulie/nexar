"""Rate limiting for Riot API requests backed by aiolimiter leaky buckets."""

import asyncio
import logging
import time

from aiolimiter import AsyncLimiter

logger = logging.getLogger("nexar")

# Standard Riot API rate limits: https://developer.riotgames.com/docs/portal
PERSONAL_LIMITS: tuple[tuple[int, int], ...] = ((20, 1), (100, 120))
PRODUCTION_LIMITS: tuple[tuple[int, int], ...] = ((500, 10), (30000, 600))


def _validate_rate_limit(limit: int, window: int) -> None:
    """Validate that rate limit values are positive and within reasonable bounds."""
    if limit <= 0:
        msg = f"Rate limit must be positive, got {limit}"
        raise ValueError(msg)
    if window <= 0:
        msg = f"Window must be positive, got {window} seconds"
        raise ValueError(msg)
    if limit > 1_000_000:
        msg = f"Rate limit suspiciously high: {limit}"
        raise ValueError(msg)
    if window > 86400:
        msg = f"Window suspiciously long: {window} seconds (>24h)"
        raise ValueError(msg)


class RateLimiter:
    """
    Rate limiter for Riot API using aiolimiter's leaky bucket algorithm.

    Full Riot API rate limit details: meta/riot_rate_limits.md

    Parses Riot API response headers (X-App-Rate-Limit, X-Method-Rate-Limit,
    X-Service-Rate-Limit) to dynamically create method/service limiters and
    handles 429 responses with Retry-After blocking.

    **Service rate limits** are shared across all applications calling a given service.
    The server provides the authoritative count via headers; this class creates
    AsyncLimiter instances that mirror the server-defined limits.

    **"Other" limits**: Some underlying services enforce their own rate limits
    independently of the API edge. In these cases, a 429 response will arrive
    *without* an X-Rate-Limit-Type header. When this happens, we cannot determine
    which bucket overflowed, so we fall back to blocking all buckets for the region
    as the safest defensive posture.

    **Static data** endpoints (e.g., Data Dragon) do not count against app rate
    limits per Riot's documentation. Calls to such endpoints should skip the rate
    limiter via a bypass flag on the client.

    TODO: Add a bypass flag to skip rate limiting for static-data endpoints.
    """

    def __init__(
        self,
        app_limits: tuple[tuple[int, int], ...] = PERSONAL_LIMITS,
        safety_margin: float = 0.01,
    ) -> None:
        """
        Initialize the rate limiter with application-level limits.

        Args:
            app_limits: Application-level rate limits as (count, window_seconds) tuples.
                Defaults to PERSONAL_LIMITS (20 req/1s + 100 req/120s).
            safety_margin: Fraction of quota to reserve as headroom (0.01 = 1%).
                Effective limit = floor(limit_val * (1 - safety_margin)).

        """
        for limit, window in app_limits:
            _validate_rate_limit(limit, window)
        self._app_limits = app_limits
        self._safety_margin = safety_margin

        # Per-region app-level AsyncLimiter instances (lazily created)
        self._app_buckets: dict[str, list[AsyncLimiter]] = {}

        # Dynamic method/service limiters created from response headers
        self._dynamic: dict[str, AsyncLimiter] = {}

        # Per-region locks for serializing acquire and header updates
        self._locks: dict[str, asyncio.Lock] = {}

        # 429 Retry-After blocking: bucket_key → unblock timestamp
        self._blocked: dict[str, float] = {}

    # -- public API --------------------------------------------------------

    async def acquire(self, region: str, method: str) -> None:
        """Acquire permission to make a request. Blocks if limits are exceeded."""
        async with self._get_lock(region):
            while True:
                now = time.time()
                block_wait = self._calc_block_wait(region, method, now)

                buckets = self._collect_buckets(region, method)
                all_ready = all(b.has_capacity() for b in buckets)

                if block_wait <= 0 and all_ready:
                    break

                wait = max(block_wait, 0.1)
                self._log_wait(region, method, wait, blocked=block_wait > 0, full=not all_ready)
                await asyncio.sleep(wait)

            # All buckets have capacity; acquire atomically under the lock
            for bucket in self._collect_buckets(region, method):
                await bucket.acquire()

    async def update_from_headers(
        self,
        headers: dict[str, str],
        region: str,
        method: str,
    ) -> None:
        """Update limits based on authoritative Riot response headers."""
        async with self._get_lock(region):
            self._sync_update_from_headers(headers, region, method)

    def dump_state(self) -> dict[str, object]:
        """Return a snapshot of all rate limit buckets for diagnostics."""
        now = time.time()
        snapshot: dict[str, object] = {}

        for region, buckets in self._app_buckets.items():
            snapshot[region] = {
                "app_buckets": [self._bucket_info(b, f"app_{region}_{b.max_rate}:{b.time_period}") for b in buckets],
            }

        dynamic_info: dict[str, dict[str, object]] = {}
        for key, bucket in self._dynamic.items():
            dynamic_info[key] = self._bucket_info(bucket, key)
        if dynamic_info:
            snapshot["__dynamic__"] = dynamic_info

        blocked_info = {k: round(max(0, v - now), 1) for k, v in self._blocked.items() if v > now}
        if blocked_info:
            snapshot["__blocked__"] = blocked_info

        return snapshot

    # -- header detection --------------------------------------------------

    @staticmethod
    def _detect_rate_limit_type(headers: dict[str, str]) -> tuple[str, bool]:
        """
        Determine the type of rate limit from response headers.

        Returns (type_label, is_explicit) where is_explicit is False when
        the X-Rate-Limit-Type header was absent.
        """
        raw_type = headers.get("X-Rate-Limit-Type", "").lower()
        type_map = {"application": "app", "method": "method", "service": "service"}
        if raw_type:
            return type_map.get(raw_type, "app"), True

        # Ambiguous: no explicit type header.
        if headers.get("X-Service-Rate-Limit"):
            return "service", False
        if headers.get("X-App-Rate-Limit"):
            return "app", False
        if headers.get("X-Method-Rate-Limit"):
            return "method", False
        return "service", False

    # -- internals ---------------------------------------------------------

    def _get_lock(self, region: str) -> asyncio.Lock:
        """Get or create an asyncio Lock for a specific region."""
        if region not in self._locks:
            self._locks[region] = asyncio.Lock()
        return self._locks[region]

    def _effective_limit(self, limit: int) -> int:
        """Apply safety margin to limit value."""
        return max(1, int(limit * (1 - self._safety_margin)))

    def _get_or_create_app_buckets(self, region: str) -> list[AsyncLimiter]:
        """Lazily create app-level AsyncLimiter instances for a region."""
        if region not in self._app_buckets:
            self._app_buckets[region] = [
                AsyncLimiter(self._effective_limit(limit), window) for limit, window in self._app_limits
            ]
        return self._app_buckets[region]

    def _collect_buckets(self, region: str, method: str) -> list[AsyncLimiter]:
        """Collect all applicable AsyncLimiter instances for a request."""
        buckets = list(self._get_or_create_app_buckets(region))
        method_prefix = f"method_{region}_{method}_"
        service_prefix = f"service_{region}_"
        for key, bucket in self._dynamic.items():
            if key.startswith((method_prefix, service_prefix)):
                buckets.append(bucket)
        return buckets

    def _calc_block_wait(self, region: str, method: str, now: float) -> float:
        """Calculate seconds to wait due to 429 Retry-After blocking."""
        wait = 0.0
        for key, blocked_until in self._blocked.items():
            if blocked_until <= now:
                continue
            if key.startswith((f"app_{region}", f"method_{region}_{method}", f"service_{region}")):
                wait = max(wait, blocked_until - now)
        return wait

    # -- header parsing ----------------------------------------------------

    def _sync_update_from_headers(
        self,
        headers: dict[str, str],
        region: str,
        method: str,
    ) -> None:
        """Parse rate limit headers and update internal state."""
        # Handle 429 blocking first
        if "Retry-After" in headers:
            self._apply_retry_after_block(headers, region, method)

        # Parse method rate limits
        self._parse_and_apply(
            headers.get("X-Method-Rate-Limit"),
            headers.get("X-Method-Rate-Limit-Count"),
            "method",
            region,
            method,
        )

        # Parse service rate limits
        self._parse_and_apply(
            headers.get("X-Service-Rate-Limit"),
            headers.get("X-Service-Rate-Limit-Count"),
            "service",
            region,
            method=None,
        )

    def _apply_retry_after_block(
        self,
        headers: dict[str, str],
        region: str,
        method: str,
    ) -> None:
        """Apply Retry-After blocking to the appropriate buckets."""
        now = time.time()
        wait_sec = self._parse_retry_after(headers)
        limit_type, is_explicit = self._detect_rate_limit_type(headers)

        logger.warning(
            "429 Rate Limit (%s) for %s/%s. Blocking for %.1fs",
            limit_type,
            region,
            method,
            wait_sec,
        )
        logger.debug(
            "429 response headers: %s",
            {k: v for k, v in headers.items() if "rate" in k.lower() or k == "Retry-After"},
        )

        if not is_explicit:
            # Ambiguous 429 — block every bucket for this region.
            self._block_region(region, now, wait_sec)
            return

        self._block_by_type(limit_type, region, method, now, wait_sec)

        # When a service/method 429 lacks its own limit header, the app
        # bucket was also exhausted — block app records too.
        if self._missing_limit_header(limit_type, headers):
            self._block_app_limits(region, now, wait_sec)

    @staticmethod
    def _parse_retry_after(headers: dict[str, str]) -> float:
        try:
            return float(headers["Retry-After"])
        except ValueError:
            logger.warning(
                "Invalid Retry-After header value: %s. Using default of 5.0 seconds",
                headers["Retry-After"],
            )
            return 5.0

    @staticmethod
    def _missing_limit_header(limit_type: str, headers: dict[str, str]) -> bool:
        if limit_type == "service":
            return not bool(headers.get("X-Service-Rate-Limit"))
        if limit_type == "method":
            return not bool(headers.get("X-Method-Rate-Limit"))
        return False

    def _block_region(self, region: str, now: float, wait_sec: float) -> None:
        for key in self._collect_block_keys_for_region(region):
            self._blocked[key] = now + wait_sec

    def _block_by_type(
        self,
        limit_type: str,
        region: str,
        method: str,
        now: float,
        wait_sec: float,
    ) -> None:
        if limit_type == "app":
            self._block_app_limits(region, now, wait_sec)
        elif limit_type == "method":
            for key in self._dynamic:
                if key.startswith(f"method_{region}_{method}_"):
                    self._blocked[key] = now + wait_sec
        elif limit_type == "service":
            for key in self._dynamic:
                if key.startswith(f"service_{region}_"):
                    self._blocked[key] = now + wait_sec

    def _block_app_limits(self, region: str, now: float, wait_sec: float) -> None:
        for limit, window in self._app_limits:
            self._blocked[f"app_{region}_{limit}:{window}"] = now + wait_sec

    def _collect_block_keys_for_region(self, region: str) -> list[str]:
        """Collect all bucket keys associated with a region for blocking."""
        keys: list[str] = [f"app_{region}_{limit}:{window}" for limit, window in self._app_limits]
        keys.extend(k for k in self._dynamic if region in k)
        return keys

    def _parse_and_apply(
        self,
        limit_hdr: str | None,
        count_hdr: str | None,
        limit_type: str,
        region: str,
        method: str | None = None,
    ) -> None:
        """Parse limit/count headers and create/update dynamic AsyncLimiter instances."""
        if not limit_hdr or not count_hdr:
            return

        parsed = self._parse_limit_header(limit_hdr)
        if parsed is None:
            return

        for limit_val, window_sec in parsed:
            if limit_type == "method" and method:
                key = f"method_{region}_{method}_{limit_val}:{window_sec}"
            else:
                key = f"service_{region}_{limit_val}:{window_sec}"

            # Replace with a fresh limiter (AsyncLimiter.max_rate is immutable)
            self._dynamic[key] = AsyncLimiter(
                self._effective_limit(limit_val),
                window_sec,
            )

    @staticmethod
    def _parse_limit_header(limit_hdr: str) -> list[tuple[int, int]] | None:
        """Parse a rate limit header like '20:1,100:120' into (limit, window) pairs."""
        try:
            parts = [tuple(x.split(":")) for x in limit_hdr.split(",")]
        except ValueError:
            logger.warning("Malformed rate limit header: %s", limit_hdr)
            return None

        result: list[tuple[int, int]] = []
        for limit_str, window_str in parts:
            try:
                limit_val = int(limit_str)
                window_sec = int(window_str)
            except ValueError:
                logger.warning(
                    "Failed to parse rate limit values: limit=%s window=%s",
                    limit_str,
                    window_str,
                )
                continue
            if limit_val > 0 and window_sec > 0:
                result.append((limit_val, window_sec))
        return result if result else None

    # -- diagnostics -------------------------------------------------------

    @staticmethod
    def _bucket_info(bucket: AsyncLimiter, key: str) -> dict[str, object]:
        """Return diagnostic info for a single AsyncLimiter."""
        return {
            "key": key,
            "max_rate": bucket.max_rate,
            "time_period": bucket.time_period,
            "has_capacity": bucket.has_capacity(),
        }

    def _log_wait(
        self,
        region: str,
        method: str,
        wait: float,
        *,
        blocked: bool,
        full: bool,
    ) -> None:
        """Log the reason for a rate limit wait."""
        if blocked:
            logger.info(
                "Rate limit BLOCKED (429) for %s/%s. Sleeping %.2fs",
                region,
                method,
                wait,
            )
        elif full:
            logger.info(
                "Rate limit FULL for %s/%s. Sleeping %.2fs",
                region,
                method,
                wait,
            )
