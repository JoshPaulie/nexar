"""In-memory rate limiting for Riot API requests."""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field, replace

logger = logging.getLogger("nexar")

# Standard Riot API rate limits: https://developer.riotgames.com/docs/portal
PERSONAL_LIMITS: tuple[tuple[int, int], ...] = ((20, 1), (100, 120))
PRODUCTION_LIMITS: tuple[tuple[int, int], ...] = ((500, 10), (30000, 600))


@dataclass
class RateLimitRecord:
    """One rate limit bucket (app, method, or service) for a region."""

    key: str
    type: str
    region: str
    count: int
    window_start: float
    limit_val: int
    window_seconds: int
    blocked_until: float
    request_times: deque[float] = field(default_factory=deque)
    """Timestamps of requests in the current window, used for accurate window_start tracking."""


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
    In-memory rate limiter supporting app, method, and service limits per region.

    Full Riot API rate limit details: meta/riot_rate_limits.md

    Parses Riot API response headers (X-App-Rate-Limit, X-Method-Rate-Limit,
    X-Service-Rate-Limit) to dynamically adjust limits and handles 429 responses
    with Retry-After blocking.

    **Service rate limits** are shared across all applications calling a given service.
    The server provides the authoritative count via headers, so this class simply
    mirrors what the server reports.

    **"Other" limits**: Some underlying services enforce their own rate limits
    independently of the API edge. In these cases, a 429 response will arrive
    *without* an X-Rate-Limit-Type header. When this happens, we cannot determine
    which bucket overflowed, so we fall back to blocking app-level records as the
    safest defensive posture.

    **Static data** endpoints (e.g., Data Dragon) do not count against app rate
    limits per Riot's documentation. Calls to such endpoints should skip the rate
    limiter via a bypass flag on the client.

    TODO: Add a bypass flag to skip rate limiting for static-data endpoints.

    State stored in `_limits` and `_locks` grows with unique (region, method)
    pairs. In practice the Riot API surface bounds this to a few hundred entries,
    so no pruning mechanism is needed.
    """

    def __init__(self, app_limits: tuple[tuple[int, int], ...]) -> None:
        """Initialize the rate limiter with default application limits."""
        for limit, window in app_limits:
            _validate_rate_limit(limit, window)
        self._app_limits = app_limits
        self._limits: dict[str, dict[str, RateLimitRecord]] = defaultdict(dict)
        self._locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, region: str) -> asyncio.Lock:
        """Get or create an asyncio Lock for a specific region."""
        if region not in self._locks:
            self._locks[region] = asyncio.Lock()
        return self._locks[region]

    def _get_or_create_region(self, region: str) -> dict[str, RateLimitRecord]:
        """Get the dictionary of rate limit records for a specific region."""
        return self._limits[region]

    async def acquire(self, region: str, method: str) -> None:
        """Acquire permission to make a request. Sleeps if limits are exceeded."""
        async with self._get_lock(region):
            now = time.time()
            limits = self._get_all_for_region(region, method)

            limits = self._ensure_initial_app_limits(region, method, now, limits)

            max_wait = self._calculate_max_wait(limits, now)
            if max_wait > 0:
                self._log_rate_limit_wait(limits, now, region, method, max_wait)
                await asyncio.sleep(max_wait)
                now = time.time()
                limits = self._get_all_for_region(region, method)
                limits = self._ensure_initial_app_limits(region, method, now, limits)

            self._increment_counters(region, limits, now)

    async def release(self, region: str, method: str) -> None:
        """Release a previously acquired request token (e.g., on 429 rollback)."""
        async with self._get_lock(region):
            self._sync_release(region, method)

    async def update_from_headers(self, headers: dict[str, str], region: str, method: str) -> None:
        """Update limits based on authoritative Riot response headers."""
        async with self._get_lock(region):
            self._sync_update_from_headers(headers, region, method)

    def _sync_update_from_headers(self, headers: dict[str, str], region: str, method: str) -> None:
        """Synchronously parse rate limit headers and update records."""
        now = time.time()

        self._parse_and_update(
            headers.get("X-App-Rate-Limit"),
            headers.get("X-App-Rate-Limit-Count"),
            "app",
            region,
        )

        self._parse_and_update(
            headers.get("X-Method-Rate-Limit"),
            headers.get("X-Method-Rate-Limit-Count"),
            "method",
            region,
            method,
        )

        self._parse_and_update(
            headers.get("X-Service-Rate-Limit"),
            headers.get("X-Service-Rate-Limit-Count"),
            "service",
            region,
        )

        if "Retry-After" in headers:
            try:
                wait_sec = float(headers["Retry-After"])
            except ValueError:
                logger.warning(
                    "Invalid Retry-After header value: %s. Using default of 5.0 seconds",
                    headers["Retry-After"],
                )
                wait_sec = 5.0

            storage_type = self._detect_rate_limit_type(headers)
            logger.warning(
                "429 Rate Limit (%s) for %s/%s. Blocking for %.1fs",
                storage_type, region, method, wait_sec,
            )
            logger.debug(
                "429 response headers: %s",
                {k: v for k, v in headers.items() if "rate" in k.lower() or k == "Retry-After"},
            )
            self._log_bucket_state(region, method)

            region_limits = self._get_or_create_region(region)
            method_param = method if storage_type == "method" else None

            for key, record in region_limits.items():
                if record.type != storage_type:
                    continue
                if storage_type == "method" and method_param and not key.startswith(f"method_{region}_{method_param}_"):
                    continue
                record.blocked_until = now + wait_sec

            if (storage_type == "service" and not headers.get("X-Service-Rate-Limit")) or (
                storage_type == "method" and not headers.get("X-Method-Rate-Limit")
            ):
                for record in region_limits.values():
                    if record.type == "app":
                        record.blocked_until = now + wait_sec

    def _sync_release(self, region: str, method: str) -> None:
        """Synchronously decrement counters for a failed request."""
        region_limits = self._get_or_create_region(region)
        method_prefix = f"method_{region}_{method}_" if method else ""
        for key, record in region_limits.items():
            is_app_or_service = record.type in {"app", "service"}
            is_matching_method = method and record.type == "method" and key.startswith(method_prefix)
            if not (is_app_or_service or is_matching_method):
                continue
            if record.request_times:
                record.request_times.pop()
            self._recount_from_times(record)

    def _get_all_for_region(self, region: str, method: str | None = None) -> list[RateLimitRecord]:
        """Retrieve all applicable rate limit records for a region and optional method."""
        region_limits = self._get_or_create_region(region)
        result: list[RateLimitRecord] = []

        method_prefix = f"method_{region}_{method}_" if method else ""
        for key, record in region_limits.items():
            is_service_or_app = record.type in {"app", "service"}
            is_matching_method = method and record.type == "method" and key.startswith(method_prefix)
            if is_service_or_app or is_matching_method:
                result.append(replace(record))

        return result

    def _ensure_initial_app_limits(
        self,
        region: str,
        method: str,
        now: float,
        limits: list[RateLimitRecord],
    ) -> list[RateLimitRecord]:
        """Ensure default app limits exist if no app limits are currently tracked."""
        if any(limit.type == "app" for limit in limits):
            return limits

        region_limits = self._get_or_create_region(region)
        for limit_val, window_sec in self._app_limits:
            key = f"app_{region}_{limit_val}:{window_sec}"
            if key not in region_limits:
                region_limits[key] = RateLimitRecord(
                    key=key,
                    type="app",
                    region=region,
                    count=0,
                    window_start=now,
                    limit_val=limit_val,
                    window_seconds=window_sec,
                    blocked_until=0.0,
                )

        return self._get_all_for_region(region, method)

    def _calculate_max_wait(self, limits: list[RateLimitRecord], now: float) -> float:
        """Calculate the maximum wait time required across all applicable limits."""
        max_wait = 0.0

        for limit in limits:
            if limit.blocked_until > now:
                max_wait = max(max_wait, limit.blocked_until - now)

        for limit in limits:
            elapsed = now - limit.window_start
            if elapsed < limit.window_seconds and limit.count >= limit.limit_val:
                max_wait = max(max_wait, limit.window_seconds - elapsed)

        return max_wait

    def _increment_counters(self, region: str, limits: list[RateLimitRecord], now: float) -> None:
        """Increment the request counters for all provided rate limit records."""
        region_limits = self._get_or_create_region(region)
        for limit in limits:
            key = limit.key
            if key not in region_limits:
                continue
            record = region_limits[key]
            window_cutoff = now - record.window_seconds

            # Prune timestamps outside the current window
            while record.request_times and record.request_times[0] <= window_cutoff:
                record.request_times.popleft()

            record.request_times.append(now)
            self._recount_from_times(record)

    def _detect_rate_limit_type(self, headers: dict[str, str]) -> str:
        """
        Determine the type of rate limit from the response headers.

        When X-Rate-Limit-Type is absent (underlying service rate limiting, not
        the API edge), we fall back to whichever limit header is present. If none
        are present, we default to "service" since the Riot docs note that backend
        services enforce their own limits independently.
        """
        raw_type = headers.get("X-Rate-Limit-Type", "").lower()
        if raw_type:
            return {"application": "app", "method": "method", "service": "service"}.get(raw_type, "app")

        if headers.get("X-Service-Rate-Limit"):
            return "service"
        if headers.get("X-App-Rate-Limit"):
            return "app"
        if headers.get("X-Method-Rate-Limit"):
            return "method"
        return "service"

    @staticmethod
    def _recount_from_times(record: RateLimitRecord) -> None:
        """Update count and window_start from the request_times deque."""
        record.count = len(record.request_times)
        record.window_start = record.request_times[0] if record.request_times else time.time()

    def _parse_limit_count_headers(
        self,
        limit_hdr: str,
        count_hdr: str,
        limit_type: str,
        region: str,
    ) -> list[tuple[int, int, int]] | None:
        """Parse limit and count headers into list of (limit_val, window_sec, count) tuples."""
        try:
            limits = [tuple(x.split(":")) for x in limit_hdr.split(",")]
            counts = [tuple(x.split(":")) for x in count_hdr.split(",")]
        except ValueError:
            logger.warning("Malformed rate limit headers: limit=%s count=%s", limit_hdr, count_hdr)
            return None

        if len(limits) != len(counts):
            logger.warning("Mismatched rate limit header counts: %d limits, %d counts", len(limits), len(counts))
            return None

        result: list[tuple[int, int, int]] = []
        for (limit_val_str, window_sec_str), (count_str, _) in zip(limits, counts, strict=True):
            try:
                limit_val = int(limit_val_str)
                window_sec = int(window_sec_str)
                count = int(count_str)
            except ValueError:
                logger.warning(
                    "Failed to parse rate limit values: limit=%s window=%s count=%s",
                    limit_val_str,
                    window_sec_str,
                    count_str,
                )
                continue

            if limit_val <= 0 or window_sec <= 0 or count < 0:
                logger.warning("Invalid rate limit value: limit=%s window=%s count=%s", limit_val, window_sec, count)
                continue

            if count > limit_val:
                logger.warning(
                    "Response count (%d) exceeds limit (%d) for %s/%s. Clamping to limit.",
                    count,
                    limit_val,
                    limit_type,
                    region,
                )
                count = limit_val

            result.append((limit_val, window_sec, count))

        return result

    def _parse_and_update(
        self,
        limit_hdr: str | None,
        count_hdr: str | None,
        limit_type: str,
        region: str,
        method: str | None = None,
    ) -> None:
        """Parse limit and count headers to update the internal rate limit records."""
        if not limit_hdr or not count_hdr:
            return

        parsed = self._parse_limit_count_headers(limit_hdr, count_hdr, limit_type, region)
        if parsed is None:
            return

        now = time.time()
        region_limits = self._get_or_create_region(region)

        for limit_val, window_sec, count in parsed:
            key_parts = [limit_type, region]
            if method:
                key_parts.append(method)
            key_parts.append(f"{limit_val}:{window_sec}")
            key = "_".join(key_parts)

            old_record = region_limits.get(key)
            old_blocked = old_record.blocked_until if old_record else 0.0

            # Reconcile local request timestamps with server count
            local_times = old_record.request_times if old_record else deque()
            cutoff = now - window_sec
            while local_times and local_times[0] <= cutoff:
                local_times.popleft()

            if len(local_times) == count:
                # Local tracking matches server — trust our window_start
                window_start = local_times[0] if local_times else now
            else:
                # Mismatch (other processes, bursty traffic, etc.): clear local times
                # and estimate window_start evenly distributing requests across the window
                local_times.clear()
                window_start = now - (count / max(limit_val, 1)) * window_sec

            region_limits[key] = RateLimitRecord(
                key=key,
                type=limit_type,
                region=region,
                count=count,
                window_start=window_start,
                limit_val=limit_val,
                window_seconds=window_sec,
                blocked_until=old_blocked,
                request_times=local_times,
            )

    # ------------------------------------------------------------------
    # Diagnostic helpers
    # ------------------------------------------------------------------

    def dump_state(self) -> dict[str, dict[str, dict[str, object]]]:
        """Return a snapshot of all rate limit buckets for diagnostics."""
        snapshot: dict[str, dict[str, dict[str, object]]] = {}
        now = time.time()
        for region, records in self._limits.items():
            snapshot[region] = {}
            for key, record in records.items():
                elapsed = now - record.window_start
                snapshot[region][key] = {
                    "type": record.type,
                    "count": record.count,
                    "limit": record.limit_val,
                    "window_s": record.window_seconds,
                    "elapsed_s": round(elapsed, 2),
                    "fill_pct": round(record.count / max(record.limit_val, 1) * 100, 1),
                    "blocked_remaining_s": round(max(record.blocked_until - now, 0), 1),
                }
        return snapshot

    def _log_bucket_state(self, region: str, method: str) -> None:
        """Log a human-readable snapshot of all buckets for a region."""
        now = time.time()
        limits = self._get_all_for_region(region, method)
        if not limits:
            return
        lines = ["  Current bucket state:"]
        for r in limits:
            fill_pct = r.count / max(r.limit_val, 1) * 100
            blocked = max(r.blocked_until - now, 0)
            parts = [f"    {r.key}", f"fill={r.count}/{r.limit_val} ({fill_pct:.0f}%)"]
            if blocked > 0:
                parts.append(f"blocked={blocked:.1f}s")
            lines.append(" | ".join(parts))
        logger.info("\n".join(lines))

    def _log_rate_limit_wait(
        self,
        limits: list[RateLimitRecord],
        now: float,
        region: str,
        method: str,
        max_wait: float,
    ) -> None:
        """Log which bucket triggered the rate limit wait."""
        for r in limits:
            if r.blocked_until > now:
                logger.info(
                    "Rate limit BLOCKED for %s/%s: %s blocked for %.1fs more. Sleeping %.2fs",
                    region, method, r.key, r.blocked_until - now, max_wait,
                )
                return
            elapsed = now - r.window_start
            if elapsed < r.window_seconds and r.count >= r.limit_val:
                fill_pct = r.count / max(r.limit_val, 1) * 100
                logger.info(
                    "Rate limit FULL for %s/%s: %s at %d/%d (%.0f%%). Sleeping %.2fs",
                    region, method, r.key, r.count, r.limit_val, fill_pct, max_wait,
                )
                return
        logger.info("Rate limit wait for %s/%s. Sleeping %.2fs", region, method, max_wait)
