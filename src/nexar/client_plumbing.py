"""Session, cache, retry, and stats machinery for NexarClient."""

import asyncio
import json
import logging
import math
import os
import re
import sqlite3
from dataclasses import dataclass
from typing import Any

import aiohttp
from aiohttp_client_cache.session import CachedSession

from .cache import create_cache_backend
from .core import NexarCore
from .enums import Region
from .exceptions import (
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)

logger = logging.getLogger("nexar")


HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429
HTTP_BAD_GATEWAY = 502
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_GATEWAY_TIMEOUT = 504


# Fallback 429 block duration when Riot omits or garbles Retry-After.
DEFAULT_RETRY_AFTER_SECONDS = 5.0

# Riot's edge serves 502/503/504 as transient Cloudflare pages: retried
# per call with backoff, never through the region ledger — no Retry-After
# exists on 5xx, and blocking the region would stall every other call for
# a blip the next attempt clears.
RETRYABLE_SERVER_ERRORS = (HTTP_BAD_GATEWAY, HTTP_SERVICE_UNAVAILABLE, HTTP_GATEWAY_TIMEOUT)

# First-attempt backoff for a retried 5xx; doubles per attempt within the
# call's max_retries budget.
SERVER_ERROR_BACKOFF_SECONDS = 0.5

_HTML_TAG_RE = re.compile(r"<[^>]+>")
_ERROR_BODY_PREVIEW_CHARS = 200


def _body_preview(body: str) -> str:
    """A bounded, structure-free preview of a non-JSON error body.

    Riot's 5xx responses are Cloudflare HTML pages: the tags carry nothing a
    caller needs, so they are stripped and whitespace collapsed before
    truncating — the exception text and the log line stay readable and
    small instead of carrying the whole page.
    """
    text = " ".join(_HTML_TAG_RE.sub(" ", body).split())
    if len(text) <= _ERROR_BODY_PREVIEW_CHARS:
        return text
    return f"{text[:_ERROR_BODY_PREVIEW_CHARS]} [truncated]"


async def _response_body_preview(response: aiohttp.ClientResponse) -> str:
    """Preview of a response body that survives undecodable bytes.

    ``response.text()`` raises UnicodeDecodeError on a garbled body, which
    would escape a retryable 5xx (and the error-mapping path) as a raw
    untyped exception with nothing in the stats; reading the bytes and
    decoding with replacement keeps the call typed and the preview bounded.
    """
    return _body_preview((await response.read()).decode(errors="replace"))


@dataclass(frozen=True)
class CallStats:
    """Statistics about API calls made by the client."""

    cache_hits: int
    """Number of responses served from cache."""

    fresh_calls: int
    """Number of responses fetched from the Riot API."""

    retries: int
    """Number of retry attempts (429 rate limits or transient network errors)."""

    errors: int
    """Number of non-retryable errors."""

    @property
    def total_calls(self) -> int:
        """Total number of API call attempts."""
        return self.cache_hits + self.fresh_calls + self.retries + self.errors


class PlumbingMixin(NexarCore):
    """Session, cache, retry, and stats machinery."""

    async def close(self) -> None:
        """Close the underlying HTTP session. Safe to call when already closed."""
        if self._session and not self._session.closed:
            await self._session.close()

    # --------------------------------------------------------------------------
    # Public Utility Methods
    # --------------------------------------------------------------------------

    async def clear_cache(self) -> None:
        """Delete every cached response. No-op when the session has no active cache."""
        if isinstance(self._session, CachedSession) and self._session.cache:
            await self._session.cache.clear()
            logger.info("Cache cleared")

    async def get_cache_info(self) -> dict[str, Any]:
        """Report the cache configuration and the number of stored rows.

        ``cached_responses`` is a best-effort count: a storage that cannot be
        counted (e.g. a locked sqlite file) reports 0 rather than raising.
        """
        info: dict[str, Any] = {
            "enabled": self.cache_config.enabled,
            "backend": self.cache_config.backend,
            "cache_name": self.cache_config.cache_name,
            "default_expire_after": self.cache_config.expire_after,
            "cached_responses": 0,
        }

        session = self._session
        if isinstance(session, CachedSession) and session.cache:
            try:
                # Row count via the storage's size(): every BaseCache implements
                # it, while CacheBackend itself defines no __len__ in this
                # aiohttp-client-cache version.
                info["cached_responses"] = await session.cache.responses.size()
            except (OSError, sqlite3.Error) as exc:
                logger.debug("Cache row count failed: %s", exc)

        return info

    def get_api_call_stats(self) -> CallStats:
        """Snapshot the call counters as a ``CallStats`` instance."""
        return CallStats(**self._call_stats)

    def print_api_call_summary(self) -> None:
        """Log a one-line summary of the call counters at INFO level."""
        stats = self.get_api_call_stats()
        if stats.total_calls > 0:
            cache_hit_rate = (stats.cache_hits / stats.total_calls) * 100
            logger.info(
                "API Stats: %d calls total, %d fresh, %d cached (%.1f%% cache hit rate), %d retries, %d errors",
                stats.total_calls,
                stats.fresh_calls,
                stats.cache_hits,
                cache_hit_rate,
                stats.retries,
                stats.errors,
            )
        else:
            logger.info("No API calls made yet.")

    # --------------------------------------------------------------------------
    # Internal Methods
    # --------------------------------------------------------------------------

    async def _ensure_session(self) -> CachedSession | aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session

        timeout = aiohttp.ClientTimeout(total=self.cache_config.timeout)

        if self.cache_config.enabled:
            self._session = CachedSession(
                cache=create_cache_backend(self.cache_config, self.riot_api_key),
                timeout=timeout,
            )
        else:
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _try_cache_response(
        self,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        endpoint: str,
    ) -> dict[str, Any] | None:
        """Try to return a cached response. Returns data on hit, None on miss.

        Load-bearing, not redundant with CachedSession's own interception: this
        read happens before ``rate_limiter.acquire``, so cache hits skip the
        limiter instead of burning a rate-limit slot. The library's interception
        (which cannot skip the limiter) stays unreachable for 200-only rows
        because this path returns them first.
        """
        if not isinstance(self._session, CachedSession) or not self._session.cache:
            return None
        cache_key = self._session.cache.create_key("GET", url, params=params, headers=headers)
        cached_response = await self._session.cache.get_response(cache_key)
        if cached_response and cached_response.ok:
            response_data = await cached_response.json()
            if response_data is None:
                # An empty body is unreadable: drop the row, or the session's own
                # interception serves it again on the wire call that follows.
                await self._session.cache.delete(cache_key)
                return None
            self._call_stats["cache_hits"] += 1
            logger.info("  Success (Status: %d, from cache)", cached_response.status)
            self._debug_print_response(
                endpoint=endpoint,
                url=url,
                status=cached_response.status,
                from_cache=True,
                response_data=response_data,
                params=params,
            )
            return response_data
        return None

    async def _record_fresh_response(
        self,
        response: aiohttp.ClientResponse,
        platform_region: str,
        url: str,
        endpoint: str,
        params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Orient the limiter, record stats, and return response data.

        ``from_cache`` is read to keep limiter orientation off replayed rows,
        even though only fresh wire responses reach this method: the manual
        cache read above preempts the library's own cache interception.
        """
        if not getattr(response, "from_cache", False):
            counts = self._parse_rate_limit_counts(response.headers.get("X-App-Rate-Limit-Count"))
            if counts:
                # Orient from the server's own usage ledger (no-op after the
                # first seed per region) so a restarted client doesn't
                # re-burst into a partially spent window.
                self.rate_limiter.seed_from_counts(platform_region, counts)
        await self._handle_response_errors(response)
        response_data: dict[str, Any] = await response.json()
        self._call_stats["fresh_calls"] += 1
        logger.info("  Success (Status: %d, fresh)", response.status)
        self._debug_print_response(
            endpoint=endpoint,
            url=url,
            status=response.status,
            from_cache=False,
            response_data=response_data,
            params=params,
        )
        return response_data

    async def _make_api_call(
        self,
        endpoint: str,
        platform_region: str,
        routing_region: str | None = None,
        params: dict[str, Any] | None = None,
        max_retries: int = 5,
    ) -> dict[str, Any]:
        if routing_region is None:
            routing_region = platform_region

        endpoint = "/" + endpoint.lstrip("/")
        url = f"https://{routing_region}.api.riotgames.com{endpoint}"
        headers = {"X-Riot-Token": self.riot_api_key}

        session = await self._ensure_session()

        for _attempt in range(max_retries):
            self._api_call_count += 1
            logger.info("API Call #%d: %s (region: %s)", self._api_call_count, endpoint, platform_region)

            try:
                cached_data = await self._try_cache_response(url, headers, params, endpoint)
                if cached_data is not None:
                    return cached_data

                await self.rate_limiter.acquire(platform_region)

                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == HTTP_TOO_MANY_REQUESTS:
                        retry_after = self._parse_retry_after(response.headers.get("Retry-After"))
                        self._call_stats["retries"] += 1
                        logger.warning(
                            "429 on attempt %d/%d for %s (region: %s). Blocking region for %.1fs",
                            _attempt + 1,
                            max_retries,
                            endpoint,
                            platform_region,
                            retry_after,
                        )
                        self.rate_limiter.block(platform_region, retry_after)
                        continue

                    if response.status in RETRYABLE_SERVER_ERRORS and _attempt < max_retries - 1:
                        body = await _response_body_preview(response)
                        self._call_stats["retries"] += 1
                        backoff = SERVER_ERROR_BACKOFF_SECONDS * 2**_attempt
                        logger.warning(
                            "HTTP %d on attempt %d/%d for %s (region: %s). Retrying in %.1fs. Body: %s",
                            response.status,
                            _attempt + 1,
                            max_retries,
                            endpoint,
                            platform_region,
                            backoff,
                            body,
                        )
                        await asyncio.sleep(backoff)
                        continue

                    return await self._record_fresh_response(
                        response,
                        platform_region,
                        url,
                        endpoint,
                        params,
                    )

            except (TimeoutError, aiohttp.ClientConnectionError) as e:
                if _attempt < max_retries - 1:
                    self._call_stats["retries"] += 1
                    backoff = 2**_attempt
                    logger.warning(
                        "Request failed (attempt %d/%d): %s. Retrying in %ds...",
                        _attempt + 1,
                        max_retries,
                        e,
                        backoff,
                    )
                    await asyncio.sleep(backoff)
                    continue
                raise RiotAPIError(0, f"Request failed after {max_retries} attempts: {e}") from e
            except aiohttp.ClientError as e:
                self._call_stats["errors"] += 1
                logger.exception("Request failed")
                raise RiotAPIError(0, f"Request failed: {e}") from e
            except RiotAPIError as e:
                # 4xx responses are routine control flow: log without a traceback.
                logger.warning("API error: %s", e)
                raise

        msg = f"Max attempts ({max_retries}) exceeded for rate-limited requests."
        raise RateLimitError(HTTP_TOO_MANY_REQUESTS, msg)

    async def _handle_response_errors(self, response: aiohttp.ClientResponse) -> None:
        if response.ok:
            return

        try:
            error_data = await response.json()
            message = error_data.get("status", {}).get("message", "Unknown error")
        except (ValueError, aiohttp.ContentTypeError):
            # Non-JSON body (a Cloudflare HTML page on 5xx, plain text on
            # garbled 4xx): keep a bounded, decode-safe preview, never the
            # whole body.
            message = await _response_body_preview(response) or f"HTTP {response.status}"

        error_map = {
            HTTP_UNAUTHORIZED: UnauthorizedError,
            HTTP_FORBIDDEN: ForbiddenError,
            HTTP_NOT_FOUND: NotFoundError,
        }
        error_class = error_map.get(response.status, RiotAPIError)
        self._call_stats["errors"] += 1
        raise error_class(response.status, message)

    def _resolve_region(self, region: Region | None) -> Region:
        resolved_region = region or self.default_region
        if resolved_region is None:
            msg = "A region must be provided either as a default or as an argument."
            raise ValueError(msg)
        return resolved_region

    @staticmethod
    def _parse_retry_after(value: str | None) -> float:
        """Parse a Retry-After header (seconds). Falls back to a conservative default."""
        if value is None:
            return DEFAULT_RETRY_AFTER_SECONDS
        try:
            seconds = float(value)
        except ValueError:
            logger.warning(
                "Invalid Retry-After header %r. Using default of %.0f seconds",
                value,
                DEFAULT_RETRY_AFTER_SECONDS,
            )
            return DEFAULT_RETRY_AFTER_SECONDS
        if not math.isfinite(seconds):
            # float("nan")/float("inf") parse but block(region, nan) would never block.
            logger.warning(
                "Non-finite Retry-After header %r. Using default of %.0f seconds",
                value,
                DEFAULT_RETRY_AFTER_SECONDS,
            )
            return DEFAULT_RETRY_AFTER_SECONDS
        return seconds

    @staticmethod
    def _parse_rate_limit_counts(value: str | None) -> dict[int, int]:
        """Parse X-App-Rate-Limit-Count ("5:1,90:120") into {window: count}."""
        counts: dict[int, int] = {}
        if not value:
            return counts
        for segment in value.split(","):
            try:
                count_str, window_str = segment.split(":")
                counts[int(window_str)] = int(count_str)
            except ValueError:
                logger.debug("Unparsable rate limit count segment %r; skipping orientation", segment)
        return counts

    def _debug_print_response(
        self,
        endpoint: str,
        url: str,
        status: int,
        *,
        from_cache: bool,
        response_data: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> None:
        if not os.getenv("NEXAR_DEBUG_RESPONSES"):
            return

        print(f"\n{'=' * 60}")
        print(f"DEBUG: API Response for {endpoint}")
        print(f"URL: {url}")
        print(f"Status: {status}")
        print(f"From Cache: {from_cache}")
        if params:
            print(f"Params: {params}")
        print("Response Data:")
        print(json.dumps(response_data, indent=2))
        print(f"{'=' * 60}\n")
