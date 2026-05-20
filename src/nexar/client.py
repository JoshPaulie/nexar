"""Main client for the Nexar SDK."""

import asyncio
import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from types import TracebackType
from typing import Any, cast
from urllib.parse import quote

import aiohttp
from aiohttp_client_cache.session import CachedSession

from .cache import DEFAULT_CACHE_CONFIG, CacheConfig, create_cache_backend
from .enums import MatchType, Queue, Region
from .exceptions import (
    BatchError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)
from .models import LeagueEntry, Match, Player, RiotAccount, Summoner
from .rate_limiter import PERSONAL_LIMITS, RateLimiter

logger = logging.getLogger("nexar")

HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429

MAX_MATCH_ID_COUNT = 100
DEFAULT_MATCH_ID_COUNT = 20


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


class NexarClient:
    """Client for interacting with the Riot Games API."""

    def __init__(
        self,
        riot_api_key: str,
        default_region: Region | None = None,
        cache_config: CacheConfig | None = None,
        app_rate_limits: tuple[tuple[int, int], ...] = PERSONAL_LIMITS,
        rate_limit_safety_margin: float = 0.01,
    ) -> None:
        """
        Initialize the Nexar client.

        Args:
            riot_api_key: Your Riot Games API key.
            default_region: Default region for API calls.
            cache_config: Cache configuration (uses DEFAULT_CACHE_CONFIG if None).
            app_rate_limits: Application-level rate limits as (count, window_seconds) tuples.
                Defaults to PERSONAL_LIMITS (20 req/1s + 100 req/120s).
                For production keys use PRODUCTION_LIMITS: ((500, 10), (30000, 600)).
            rate_limit_safety_margin: Fraction of quota to reserve (0.01 = 1%).
                Reduces effective limits to avoid precise boundary 429s.
                Effective limit = floor(limit_val * (1 - safety_margin)).

        """
        self.riot_api_key = riot_api_key
        self.default_region = default_region
        self.cache_config = cache_config or DEFAULT_CACHE_CONFIG
        self.rate_limiter = RateLimiter(app_rate_limits, safety_margin=rate_limit_safety_margin)

        self._api_call_count = 0
        self._call_stats: dict[str, int] = {
            "cache_hits": 0,
            "fresh_calls": 0,
            "retries": 0,
            "errors": 0,
        }
        self._session: CachedSession | aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "NexarClient":
        await self._ensure_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    # --------------------------------------------------------------------------
    # Public API Methods
    # --------------------------------------------------------------------------

    # Account API
    async def get_riot_account(
        self,
        game_name: str,
        tag_line: str,
        region: Region | None = None,
    ) -> RiotAccount:
        """Get a Riot account by game name and tag line."""
        game_name = game_name.strip()
        tag_line = tag_line.strip()
        resolved_region = self._resolve_region(region)
        endpoint = f"/riot/account/v1/accounts/by-riot-id/{quote(game_name)}/{quote(tag_line)}"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.account_region)
        return RiotAccount.from_api_response(data)

    async def get_riot_account_by_puuid(
        self,
        puuid: str,
        *,
        region: Region | None = None,
    ) -> RiotAccount:
        """Get a Riot account by PUUID."""
        resolved_region = self._resolve_region(region)
        endpoint = f"/riot/account/v1/accounts/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.account_region)
        return RiotAccount.from_api_response(data)

    # Summoner API
    async def get_summoner_by_puuid(self, puuid: str, region: Region | None = None) -> Summoner:
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        return Summoner.from_api_response(data)

    # League API
    async def get_league_entries_by_puuid(
        self,
        puuid: str,
        region: Region | None = None,
    ) -> list[LeagueEntry]:
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/league/v4/entries/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        entries_list = cast("list[dict[str, Any]]", data)
        return [LeagueEntry.from_api_response(entry) for entry in entries_list]

    # Match API
    async def get_match(self, match_id: str, region: Region | None = None) -> Match:
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/match/v5/matches/{match_id}"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.v5_region)
        return Match.from_api_response(data)

    async def get_match_ids_by_puuid(
        self,
        puuid: str,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: Queue | int | None = None,
        match_type: MatchType | str | None = None,
        start: int = 0,
        count: int = DEFAULT_MATCH_ID_COUNT,
        region: Region | None = None,
    ) -> list[str]:
        if start < 0:
            msg = f"start must be non-negative, got {start}"
            raise ValueError(msg)
        if not 0 <= count <= MAX_MATCH_ID_COUNT:
            msg = f"count must be between 0 and {MAX_MATCH_ID_COUNT}"
            raise ValueError(msg)

        resolved_region = self._resolve_region(region)
        params = self._build_match_ids_params(start_time, end_time, queue, match_type, start, count)
        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        data = await self._make_api_call(endpoint, resolved_region.value, resolved_region.v5_region, params=params)
        return cast("list[str]", data)

    # --------------------------------------------------------------------------
    # High-Level Convenience Methods
    # --------------------------------------------------------------------------

    async def get_player(
        self,
        *,
        game_name: str | None = None,
        tag_line: str | None = None,
        puuid: str | None = None,
        riot_id: str | None = None,
        region: Region | None = None,
    ) -> "Player":
        """
        Get a Player by game name + tag line, PUUID, or Riot ID string.

        Exactly one identification pattern must be provided (all keyword-only):

        Args:
            game_name: Player's game name (without #). Must be paired with tag_line.
            tag_line: Player's tag line (without #). Must be paired with game_name.
            puuid: Player's PUUID for direct lookup.
            riot_id: Riot ID in "gameName#tagLine" format (e.g. "bexli#bex").
            region: The player's region (defaults to client default).

        Returns:
            Player instance with riot account data pre-fetched.

        Raises:
            ValueError: If none or an ambiguous combination of identifiers is provided.

        """
        from .models.player import Player

        resolved_region = self._resolve_region(region)

        if game_name is not None and tag_line is not None:
            return await Player.create(
                client=self,
                game_name=game_name,
                tag_line=tag_line,
                region=resolved_region,
            )
        if puuid is not None:
            return await Player.create(
                client=self,
                puuid=puuid,
                region=resolved_region,
            )
        if riot_id is not None:
            return await Player.create(
                client=self,
                riot_id=riot_id,
                region=resolved_region,
            )
        msg = "Either game_name + tag_line, puuid, or riot_id must be provided."
        raise ValueError(msg)

    async def get_players(
        self,
        riot_ids: list[str],
        region: Region | None = None,
    ) -> list["Player"]:
        from .models.player import Player

        resolved_region = self._resolve_region(region)

        async def create_player(riot_id: str) -> Player:
            return await Player.by_riot_id(
                client=self,
                riot_id=riot_id,
                region=resolved_region,
            )

        results = await asyncio.gather(
            *(create_player(riot_id) for riot_id in riot_ids),
            return_exceptions=True,
        )

        players: list[Player] = []
        errors: list[tuple[str, Exception]] = []

        for riot_id, result in zip(riot_ids, results, strict=False):
            if isinstance(result, Exception):
                errors.append((riot_id, result))
            else:
                players.append(cast("Player", result))

        if errors:
            raise BatchError(errors, successful_results=players)

        return players

    # --------------------------------------------------------------------------
    # Public Utility Methods
    # --------------------------------------------------------------------------

    async def clear_cache(self) -> None:
        if isinstance(self._session, CachedSession) and self._session.cache:
            await self._session.cache.clear()
            logger.info("Cache cleared")

    async def get_cache_info(self) -> dict[str, Any]:
        info: dict[str, Any] = {
            "enabled": self.cache_config.enabled,
            "backend": self.cache_config.backend,
            "cache_name": self.cache_config.cache_name,
            "default_expire_after": self.cache_config.expire_after,
            "cached_responses": 0,
        }

        if isinstance(self._session, CachedSession) and self._session.cache:
            try:
                cache = self._session.cache
                if hasattr(cache, "__len__"):
                    info["cached_responses"] = len(cache)
                if hasattr(cache, "size"):
                    info["cache_size"] = cache.size
            except (AttributeError, KeyError, TypeError) as exc:
                logger.debug("Cache info check failed: %s", exc)

        return info

    def get_api_call_stats(self) -> CallStats:
        return CallStats(
            cache_hits=self._call_stats["cache_hits"],
            fresh_calls=self._call_stats["fresh_calls"],
            retries=self._call_stats["retries"],
            errors=self._call_stats["errors"],
        )

    def print_api_call_summary(self) -> None:
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

    async def _ensure_session(self) -> None:
        if self._session and not self._session.closed:
            return

        timeout = aiohttp.ClientTimeout(total=self.cache_config.timeout)

        if self.cache_config.enabled:
            self._session = CachedSession(
                cache=create_cache_backend(self.cache_config),
                timeout=timeout,
            )
        else:
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def _try_cache_response(
        self,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        endpoint: str,
    ) -> dict[str, Any] | None:
        """Try to return a cached response. Returns data on hit, None on miss."""
        if not isinstance(self._session, CachedSession) or not self._session.cache:
            return None
        cache_key = self._session.cache.create_key("GET", url, params=params, headers=headers)
        cached_response = await self._session.cache.get_response(cache_key)
        if cached_response and cached_response.ok:
            response_data: dict[str, Any] = await cached_response.json()
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

    async def _record_success_response(
        self,
        response: aiohttp.ClientResponse,
        platform_region: str,
        method_id: str,
        url: str,
        endpoint: str,
        params: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Update rate limiter, handle errors, record stats, and return response data."""
        await self.rate_limiter.update_from_headers(
            dict(response.headers),
            platform_region,
            method_id,
        )
        await self._handle_response_errors(response)
        response_data: dict[str, Any] = await response.json()
        from_cache = getattr(response, "from_cache", False)
        if from_cache:
            self._call_stats["cache_hits"] += 1
        else:
            self._call_stats["fresh_calls"] += 1
        logger.info("  Success (Status: %d, %s)", response.status, "from cache" if from_cache else "fresh")
        self._debug_print_response(
            endpoint=endpoint,
            url=url,
            status=response.status,
            from_cache=from_cache,
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

        await self._ensure_session()
        if not self._session:
            msg = "Client session not initialized."
            raise RuntimeError(msg)

        for _attempt in range(max_retries):
            self._api_call_count += 1
            logger.info("API Call #%d: %s (region: %s)", self._api_call_count, endpoint, platform_region)

            try:
                cached_data = await self._try_cache_response(url, headers, params, endpoint)
                if cached_data is not None:
                    return cached_data

                method_id = self._extract_method_id(endpoint)
                await self.rate_limiter.acquire(platform_region, method_id)

                async with self._session.get(url, headers=headers, params=params) as response:
                    if response.status == HTTP_TOO_MANY_REQUESTS:
                        retry_after = response.headers.get("Retry-After", "?")
                        logger.warning(
                            "429 on attempt %d/%d for %s (region: %s). Retry-After: %ss",
                            _attempt + 1,
                            max_retries,
                            endpoint,
                            platform_region,
                            retry_after,
                        )
                        self._call_stats["retries"] += 1
                        await self.rate_limiter.update_from_headers(
                            dict(response.headers),
                            platform_region,
                            method_id,
                        )
                        continue

                    return await self._record_success_response(
                        response,
                        platform_region,
                        method_id,
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
                raise RiotAPIError(0, f"Request failed after {max_retries} retries: {e}") from e
            except aiohttp.ClientError as e:
                self._call_stats["errors"] += 1
                logger.exception("Request failed")
                raise RiotAPIError(0, f"Request failed: {e}") from e
            except RiotAPIError:
                logger.exception("API error")
                raise

        msg = f"Max retries ({max_retries}) exceeded for rate-limited requests."
        raise RateLimitError(HTTP_TOO_MANY_REQUESTS, msg)

    async def _handle_response_errors(self, response: aiohttp.ClientResponse) -> None:
        if response.ok:
            return

        try:
            error_data = await response.json()
            message = error_data.get("status", {}).get("message", "Unknown error")
        except (ValueError, aiohttp.ContentTypeError):
            message = await response.text() or f"HTTP {response.status}"

        error_map = {
            HTTP_UNAUTHORIZED: UnauthorizedError,
            HTTP_FORBIDDEN: ForbiddenError,
            HTTP_NOT_FOUND: NotFoundError,
            HTTP_TOO_MANY_REQUESTS: RateLimitError,
        }
        error_class = error_map.get(response.status, RiotAPIError)
        raise error_class(response.status, message)

    def _build_match_ids_params(
        self,
        start_time: int | datetime | None,
        end_time: int | datetime | None,
        queue: Queue | int | None,
        match_type: MatchType | str | None,
        start: int,
        count: int,
    ) -> dict[str, int | str]:
        params: dict[str, int | str] = {}
        if start_time is not None:
            params["startTime"] = self._to_epoch(start_time)
        if end_time is not None:
            params["endTime"] = self._to_epoch(end_time)
        if queue is not None:
            params["queue"] = queue.value if isinstance(queue, Queue) else queue
        if match_type is not None:
            params["type"] = match_type.value if isinstance(match_type, MatchType) else match_type
        if start != 0:
            params["start"] = start
        if count != DEFAULT_MATCH_ID_COUNT:
            params["count"] = count
        return params

    def _resolve_region(self, region: Region | None) -> Region:
        resolved_region = region or self.default_region
        if resolved_region is None:
            msg = "A region must be provided either as a default or as an argument."
            raise ValueError(msg)
        return resolved_region

    @staticmethod
    def _to_epoch(value: int | datetime) -> int:
        """
        Convert int or datetime to UTC epoch seconds.

        Naive datetimes are treated as UTC.
        """
        if isinstance(value, int):
            return value
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return int(value.timestamp())

    @staticmethod
    def _extract_method_id(endpoint: str) -> str:
        parts = endpoint.lstrip("/").split("/")

        if len(parts) < 2:
            logger.debug("_extract_method_id: short endpoint '%s', returning 'unknown'", endpoint)
            return "unknown"

        if len(parts) >= 3 and re.match(r"^v\d+$", parts[2]):
            method = parts[1]
            version = parts[2]
            return f"{method}-{version}"

        if parts[0] == "static-data" and len(parts) >= 3:
            resource = parts[2]
            return f"{resource}-static"

        for i, part in enumerate(parts):
            if re.match(r"^v\d+$", part) and i > 0:
                method = parts[i - 1]
                version = part
                logger.debug(
                    "_extract_method_id: used fallback regex match for '%s' -> %s-%s",
                    endpoint,
                    method,
                    version,
                )
                return f"{method}-{version}"

        if len(parts) >= 2:
            service = parts[0]
            method = parts[1]
            result = f"{method}-{service}" if len(parts) >= 3 else f"{service}-{method}"
            logger.debug(
                "_extract_method_id: fell through to low-confidence heuristic for '%s' -> %s",
                endpoint,
                result,
            )
            return result

        logger.debug("_extract_method_id: no match for '%s', returning 'unknown'", endpoint)
        return "unknown"

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
