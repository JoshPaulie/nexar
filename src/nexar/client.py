"""Main client for the Nexar SDK."""

import asyncio
import json
import os
from datetime import datetime
from types import TracebackType
from typing import Any

import aiohttp
from aiohttp_client_cache.session import CachedSession

from .cache import DEFAULT_CACHE_CONFIG, CacheConfig, create_cache_backend
from .enums import MatchType, Queue, Region
from .exceptions import (
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)
from .logging import get_logger
from .models import LeagueEntry, Match, Player, RiotAccount, Summoner
from .rate_limiter import RateLimiter

# HTTP status codes (module-level constants)
HTTP_OK = 200
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_TOO_MANY_REQUESTS = 429

# Constants for match id count
MAX_MATCH_ID_COUNT = 100
DEFAULT_MATCH_ID_COUNT = 20


class NexarClient:
    """Client for interacting with the Riot Games API."""

    # --------------------------------------------------------------------------
    # Initialization and Lifecycle
    # --------------------------------------------------------------------------

    def __init__(
        self,
        riot_api_key: str,
        default_region: Region | None = None,
        cache_config: CacheConfig | None = None,
        per_second_limit: tuple[int, int] = (20, 1),
        per_minute_limit: tuple[int, int] = (100, 2),
    ) -> None:
        """
        Initialize the Nexar client.

        Args:
            riot_api_key: Your Riot Games API key
            default_region: Default region for API calls
            cache_config: Cache configuration (uses default if None)
            per_second_limit: Tuple of (max_requests, seconds). E.g., (20, 1) for max 20 requests per 1 second.
            per_minute_limit: Tuple of (max_requests, minutes). E.g., (100, 2) for max 100 requests per 2 minutes.

        """
        self.riot_api_key = riot_api_key
        self.default_region = default_region
        self.cache_config = cache_config or DEFAULT_CACHE_CONFIG
        self._per_second_limit = per_second_limit
        self._per_minute_limit = per_minute_limit
        self.rate_limiter = RateLimiter(
            per_second_limit=self._per_second_limit,
            per_minute_limit=self._per_minute_limit,
        )
        self._logger = get_logger()
        self._api_call_count = 0
        self._session: CachedSession | aiohttp.ClientSession | None = None

    async def __aenter__(self) -> "NexarClient":
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the client session."""
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
        """
        Get a Riot account by game name and tag line.

        Args:
            game_name: The game name (without #)
            tag_line: The tag line (without #)
            region: Region to use (defaults to client's default)

        Returns:
            RiotAccount with account information

        """
        resolved_region = self._resolve_region(region)
        endpoint = f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        data = await self._make_api_call(endpoint, resolved_region.account_region)
        return RiotAccount.from_api_response(data)

    # Summoner API
    async def get_summoner_by_puuid(self, puuid: str, region: Region | None = None) -> Summoner:
        """
        Get a summoner by PUUID.

        Args:
            puuid: The summoner's PUUID
            region: Region to use (defaults to client's default)

        Returns:
            Summoner with summoner information

        """
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
        """
        Get league entries by PUUID.

        Args:
            puuid: The summoner's PUUID
            region: Region to use (defaults to client's default)

        Returns:
            List of league entries for the summoner

        """
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/league/v4/entries/by-puuid/{puuid}"
        data = await self._make_api_call(endpoint, resolved_region.value)
        entries_list: list[dict[str, Any]] = data  # type: ignore[assignment]
        return [LeagueEntry.from_api_response(entry) for entry in entries_list]

    # Match API
    async def get_match(self, match_id: str, region: Region | None = None) -> Match:
        """
        Get match details by match ID.

        Args:
            match_id: The match ID
            region: Region to use (defaults to client's default)

        Returns:
            Match with detailed match information

        """
        resolved_region = self._resolve_region(region)
        endpoint = f"/lol/match/v5/matches/{match_id}"
        data = await self._make_api_call(endpoint, resolved_region.v5_region)
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
        count: int = 20,
        region: Region | None = None,
    ) -> list[str]:
        """
        Get match IDs by PUUID with optional filters.

        Args:
            puuid: The player's PUUID
            start_time: Epoch timestamp in seconds or datetime for match start filter
            end_time: Epoch timestamp in seconds or datetime for match end filter
            queue: Queue ID filter (int or QueueId enum)
            match_type: Match type filter (str or MatchType enum)
            start: Start index (0-based)
            count: Number of match IDs to return (0-100)
            region: Region to use (defaults to client's default)

        Returns:
            List of match IDs

        """
        if not 0 <= count <= MAX_MATCH_ID_COUNT:
            msg = f"count must be between 0 and {MAX_MATCH_ID_COUNT}"
            raise ValueError(msg)

        resolved_region = self._resolve_region(region)
        params = self._build_match_ids_params(start_time, end_time, queue, match_type, start, count)
        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        data = await self._make_api_call(endpoint, resolved_region.v5_region, params=params)
        match_ids: list[str] = data  # type: ignore[assignment]
        return match_ids

    # --------------------------------------------------------------------------
    # High-Level Convenience Methods
    # --------------------------------------------------------------------------

    async def get_player(
        self,
        game_name: str,
        tag_line: str,
        region: Region | None = None,
    ) -> "Player":
        """
        Create a Player object for convenient high-level access.

        Args:
            game_name: Player's game name (without #)
            tag_line: Player's tag line (without #)
            region: The player's region (defaults to client default)

        Returns:
            Player object providing high-level access to player data

        """
        from .models.player import Player

        resolved_region = self._resolve_region(region)

        return await Player.create(
            client=self,
            game_name=game_name,
            tag_line=tag_line,
            region=resolved_region,
        )

    async def get_players(
        self,
        riot_ids: list[str],
        region: Region | None = None,
    ) -> list["Player"]:
        """
        Create multiple Player objects efficiently using parallel processing.

        Args:
            riot_ids: List of Riot IDs in "username#tagline" format.
            region: The players' region (defaults to client default)

        Returns:
            List of Player objects.

        """
        from .models.player import Player

        resolved_region = self._resolve_region(region)

        async def create_player(riot_id: str) -> Player:
            return await Player.by_riot_id(
                client=self,
                riot_id=riot_id,
                region=resolved_region,
            )

        return await asyncio.gather(*[create_player(riot_id) for riot_id in riot_ids])

    # --------------------------------------------------------------------------
    # Public Utility Methods
    # --------------------------------------------------------------------------

    # Caching
    async def clear_cache(self) -> None:
        """Clear all cached responses."""
        if isinstance(self._session, CachedSession) and self._session.cache:
            await self._session.cache.clear()
            self._logger.log_cache_cleared()

    async def get_cache_info(self) -> dict[str, Any]:
        """
        Get information about the current cache state.

        Returns:
            Dictionary with cache statistics and configuration.

        """
        info = {
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
                self._logger.logger.debug("Cache info check failed: %s", exc)

        return info

    # Stats and Rate Limiting
    def get_api_call_stats(self) -> dict[str, int]:
        """Get API call statistics."""
        return self._logger.get_stats()

    def print_api_call_summary(self) -> None:
        """Print a summary of API calls made so far."""
        self._logger.log_stats_summary()

    def reset_rate_limiter(self) -> None:
        """Reset the rate limiter state to the initial configuration."""
        self.rate_limiter = RateLimiter(
            per_second_limit=self._per_second_limit,
            per_minute_limit=self._per_minute_limit,
        )

    # --------------------------------------------------------------------------
    # Internal Methods
    # --------------------------------------------------------------------------

    # Session Management
    async def _ensure_session(self) -> None:
        """Ensure the session is created and configured."""
        if self._session and not self._session.closed:
            return

        if self.cache_config.enabled:
            urls_expire_after = {
                f"*{pattern}*": config.get("expire_after", self.cache_config.expire_after)
                for pattern, config in self.cache_config.endpoint_config.items()
                if isinstance(config, dict) and config.get("enabled", True)
            }
            self._session = CachedSession(
                cache=create_cache_backend(self.cache_config),
                urls_expire_after=urls_expire_after or None,
            )
        else:
            self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))

        self._setup_caching()

    def _setup_caching(self) -> None:
        """Set up caching for the HTTP session if enabled."""
        if not self.cache_config.enabled:
            return

        has_cache = isinstance(self._session, CachedSession) and self._session.cache is not None
        cache_type = type(self._session.cache) if has_cache and isinstance(self._session, CachedSession) else None

        self._logger.log_cache_setup(
            cache_name=self.cache_config.cache_name,
            backend=self.cache_config.backend,
            has_cache=has_cache,
            cache_type=cache_type,
        )

        if has_cache and isinstance(self._session, CachedSession) and self.cache_config.expire_after is not None:
            self._logger.log_cache_config(
                expire_after=self.cache_config.expire_after,
                has_url_expiration=bool(getattr(self._session, "urls_expire_after", None)),
            )

    # Core API Call Logic
    async def _make_api_call(
        self,
        endpoint: str,
        region_value: str,
        params: dict[str, Any] | None = None,
        max_retries: int = 5,
    ) -> dict[str, Any]:
        """Make an async API call, handling rate limits, retries, and caching."""
        url = f"https://{region_value}.api.riotgames.com{endpoint}"
        headers = {"X-Riot-Token": self.riot_api_key}

        for _ in range(max_retries):
            await self._ensure_session()
            if not self._session:
                msg = "Client session not initialized."
                raise RuntimeError(msg)

            self._api_call_count += 1
            self._logger.log_api_call_start(self._api_call_count, endpoint, region_value, params)

            try:
                # Try cache lookup
                if isinstance(self._session, CachedSession) and self._session.cache:
                    cache_key = self._session.cache.create_key("GET", url, params=params, headers=headers)
                    cached_response = await self._session.cache.get_response(cache_key)
                    if cached_response:
                        response_data: dict[str, Any] = await cached_response.json()
                        self._logger.log_api_call_success(cached_response.status, from_cache=True)
                        self._debug_print_response(
                            endpoint=endpoint,
                            url=url,
                            status=cached_response.status,
                            from_cache=True,
                            response_data=response_data,
                            params=params,
                        )
                        return response_data

                # Perform HTTP request
                async with (
                    self.rate_limiter.combined_limiters(),
                    self._session.get(
                        url,
                        headers=headers,
                        params=params,
                    ) as response,
                ):
                    if response.status == HTTP_TOO_MANY_REQUESTS:
                        retry_after = response.headers.get("Retry-After")
                        wait_time = float(retry_after) if retry_after else 120.0
                        self._logger.logger.warning("Rate limited (429). Retrying in %s seconds...", wait_time)
                        await asyncio.sleep(wait_time)
                        continue  # Retry

                    await self._handle_response_errors(response)
                    response_data = await response.json()
                    from_cache = getattr(response, "from_cache", False)
                    self._logger.log_api_call_success(response.status, from_cache=from_cache)
                    self._debug_print_response(
                        endpoint=endpoint,
                        url=url,
                        status=response.status,
                        from_cache=from_cache,
                        response_data=response_data,
                        params=params,
                    )
                    return response_data

            except aiohttp.ClientError as e:
                self._logger.log_api_call_error(e)
                raise RiotAPIError(0, f"Request failed: {e}") from e
            except RiotAPIError as e:
                self._logger.log_api_call_error(e)
                raise

        msg = "Max retries exceeded for rate-limited request."
        raise RiotAPIError(HTTP_TOO_MANY_REQUESTS, msg)

    async def _handle_response_errors(self, response: aiohttp.ClientResponse) -> None:
        """Raise appropriate exceptions for HTTP error status codes."""
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

    # Parameter Building and Resolution
    def _build_match_ids_params(
        self,
        start_time: int | datetime | None,
        end_time: int | datetime | None,
        queue: Queue | int | None,
        match_type: MatchType | str | None,
        start: int,
        count: int,
    ) -> dict[str, int | str]:
        """Build the query parameter dictionary for the get_match_ids_by_puuid endpoint."""
        params: dict[str, int | str] = {}
        if start_time is not None:
            params["startTime"] = int(start_time.timestamp()) if isinstance(start_time, datetime) else start_time
        if end_time is not None:
            params["endTime"] = int(end_time.timestamp()) if isinstance(end_time, datetime) else end_time
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
        """Resolve the region, using the client's default if None."""
        resolved_region = region or self.default_region
        if resolved_region is None:
            msg = "A region must be provided either as a default or as an argument."
            raise ValueError(msg)
        return resolved_region

    # Debugging and Stats
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
        """Print API response for debugging if NEXAR_DEBUG_RESPONSES is set."""
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

    def _get_api_call_count(self) -> int:
        """Get the current number of API calls made."""
        return self._api_call_count

    def _reset_api_call_count(self) -> None:
        """Reset the API call counter to zero."""
        self._api_call_count = 0
        self._logger.reset_stats()
