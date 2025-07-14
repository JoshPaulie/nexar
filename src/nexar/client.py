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
from .enums import MatchType, Queue, RegionV4, RegionV5
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

    def __init__(
        self,
        riot_api_key: str,
        default_v4_region: RegionV4 | None = None,
        default_v5_region: RegionV5 | None = None,
        cache_config: CacheConfig | None = None,
        per_second_limit: tuple[int, int] = (20, 1),
        per_minute_limit: tuple[int, int] = (100, 2),
    ) -> None:
        """
        Initialize the Nexar client.

        Args:
            riot_api_key: Your Riot Games API key
            default_v4_region: Default region for platform-specific endpoints
            default_v5_region: Default region for regional endpoints
            cache_config: Cache configuration (uses default if None)
            per_second_limit: (Requests, per second) for rate limiting
            per_minute_limit: (Requests, per minute) for rate limiting

        """
        self.riot_api_key = riot_api_key
        self.default_v4_region = default_v4_region
        self.default_v5_region = default_v5_region
        self.cache_config = cache_config or DEFAULT_CACHE_CONFIG
        self._per_second_limit = per_second_limit
        self._per_minute_limit = per_minute_limit
        self.rate_limiter = RateLimiter(
            per_second_limit=self._per_second_limit,
            per_minute_limit=self._per_minute_limit,
        )
        self._logger = get_logger()

        # API call tracking (always enabled, debug display is conditional)
        self._api_call_count = 0

        # Session will be created when needed
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
        if self._session:
            await self._session.close()

    async def _ensure_session(self) -> None:
        """Ensure the session is created and configured."""
        if self._session:
            return

        # Initialize caching if enabled
        if self.cache_config.enabled:
            # Create per-URL expiration mapping
            urls_expire_after = {}
            for endpoint_pattern, config in self.cache_config.endpoint_config.items():
                if isinstance(config, dict) and config.get("enabled", True):
                    expire_time = config.get(
                        "expire_after",
                        self.cache_config.expire_after,
                    )
                    # Map pattern to actual URLs that might match
                    urls_expire_after[f"*{endpoint_pattern}*"] = expire_time

            # Create cached session
            self._session = CachedSession(
                cache=create_cache_backend(self.cache_config),
                urls_expire_after=urls_expire_after if urls_expire_after else None,
            )
        else:
            # Create regular session
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)

        self._setup_caching()

    async def _make_api_call(
        self,
        endpoint: str,
        region: RegionV4 | RegionV5,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Make an async API call to the Riot Games API.

        Args:
            endpoint: The API endpoint path
            region: The region to use for the request
            params: Optional query parameters dict

        Returns:
            JSON response from the API

        Raises:
            RiotAPIError: If the API returns an error status code

        """
        await self._ensure_session()

        # Always increment API call counter
        self._api_call_count += 1

        # Log API call start
        self._logger.log_api_call_start(
            self._api_call_count,
            endpoint,
            region.value,
            params,
        )

        # Construct the full URL with the region
        url = f"https://{region.value}.api.riotgames.com{endpoint}"

        # Set required headers for Riot API
        headers = {
            "X-Riot-Token": self.riot_api_key,
            "User-Agent": "nexar-python-sdk/0.1.0",
            "Accept": "application/json",
        }

        try:
            # Apply rate limiting for actual API calls
            await self.rate_limiter.async_wait_if_needed()

            # Make the request (cached or not)
            if self._session is None:
                msg = "Session is not initialized."
                raise RuntimeError(msg)
            async with self._session.get(
                url,
                headers=headers,
                params=params,
            ) as response:
                # Check if this request was served from cache
                from_cache = getattr(response, "from_cache", False)

                await self._handle_response_errors(response)

                # Log successful response
                self._logger.log_api_call_success(response.status, from_cache=from_cache)

                response_data = await response.json()

                # Debug: Print API response if environment variable is set
                if os.getenv("NEXAR_DEBUG_RESPONSES"):
                    print(f"\n{'=' * 60}")
                    print(f"DEBUG: API Response for {endpoint}")
                    print(f"URL: {url}")
                    print(f"Status: {response.status}")
                    print(f"From Cache: {from_cache}")
                    if params:
                        print(f"Params: {params}")
                    print("Response Data:")
                    print(json.dumps(response_data, indent=2))
                    print(f"{'=' * 60}\n")

                return response_data  # type: ignore[no-any-return]

        except aiohttp.ClientError as e:
            self._logger.log_api_call_error(e)
            raise RiotAPIError(0, f"Request failed: {e}") from e
        except (RateLimitError, RiotAPIError) as e:
            self._logger.log_api_call_error(e)
            raise

    def _get_api_call_count(self) -> int:
        """
        Get the current number of API calls made by this client.

        Returns:
            Number of API calls made since client initialization

        """
        return self._api_call_count

    def _reset_api_call_count(self) -> None:
        """Reset the API call counter to zero."""
        self._api_call_count = 0
        self._logger.reset_stats()

    def get_rate_limit_status(self) -> dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dictionary with current rate limit usage and remaining requests

        """
        return self.rate_limiter.get_status()

    def reset_rate_limiter(self) -> None:
        """Reset the rate limiter state to the initial configuration."""
        self.rate_limiter = RateLimiter(
            per_second_limit=self._per_second_limit,
            per_minute_limit=self._per_minute_limit,
        )

    def get_api_call_stats(self) -> dict[str, int]:
        """
        Get API call statistics.

        Returns:
            Dictionary with call statistics including total calls, cache hits, and fresh calls

        """
        return self._logger.get_stats()

    def print_api_call_summary(self) -> None:
        """Print a summary of API calls made so far."""
        self._logger.log_stats_summary()

    async def _handle_response_errors(self, response: aiohttp.ClientResponse) -> None:
        """Handle HTTP errors from the API response."""
        if response.status == HTTP_OK:
            return

        try:
            error_data = await response.json()
            message = error_data.get("status", {}).get("message", "Unknown error")
        except (ValueError, aiohttp.ContentTypeError):
            message = await response.text() or "Unknown error"

        if response.status == HTTP_UNAUTHORIZED:
            raise UnauthorizedError(response.status, message)
        if response.status == HTTP_FORBIDDEN:
            raise ForbiddenError(response.status, message)
        if response.status == HTTP_NOT_FOUND:
            raise NotFoundError(response.status, message)
        if response.status == HTTP_TOO_MANY_REQUESTS:
            raise RateLimitError(response.status, message)
        raise RiotAPIError(response.status, message)

    def _setup_caching(self) -> None:
        """Set up caching for the HTTP session if enabled."""
        if not self.cache_config.enabled:
            return

        # Log cache setup information
        has_cache = isinstance(self._session, CachedSession) and hasattr(self._session, "cache")
        cache_type = None
        if has_cache and isinstance(self._session, CachedSession) and self._session.cache:
            cache_type = type(self._session.cache)

        self._logger.log_cache_setup(
            cache_name=self.cache_config.cache_name,
            backend=self.cache_config.backend,
            has_cache=has_cache,
            cache_type=cache_type,
        )

        if has_cache and isinstance(self._session, CachedSession):
            # Log cache configuration details
            expire_after = self.cache_config.expire_after
            if expire_after is not None:
                self._logger.log_cache_config(
                    expire_after=expire_after,
                    has_url_expiration=bool(getattr(self._session, "urls_expire_after", None)),
                )

    async def clear_cache(self) -> None:
        """Clear all cached responses."""
        if isinstance(self._session, CachedSession) and hasattr(self._session, "cache") and self._session.cache:
            await self._session.cache.clear()
            self._logger.log_cache_cleared()

    async def get_cache_info(self) -> dict[str, Any]:
        """
        Get information about the current cache state.

        Returns:
            Dictionary with cache statistics and configuration

        """
        info = {
            "enabled": self.cache_config.enabled,
            "backend": self.cache_config.backend,
            "cache_name": self.cache_config.cache_name,
            "default_expire_after": self.cache_config.expire_after,
        }

        if isinstance(self._session, CachedSession) and hasattr(self._session, "cache") and self._session.cache:
            try:
                # Try to get cache size if the backend supports it
                cache = self._session.cache
                if hasattr(cache, "__len__"):
                    info["cached_responses"] = len(cache)
                if hasattr(cache, "size"):
                    info["cache_size"] = cache.size
            except (AttributeError, KeyError, TypeError) as exc:
                # Some backends might not support these operations
                self._logger.logger.debug("Cache info check failed: %s", exc)

        return info

    # Account API
    async def get_riot_account(
        self,
        game_name: str,
        tag_line: str,
        region: RegionV5 | None = None,
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
        region = region or self.default_v5_region
        if region is None:
            msg = "A v5 region must be provided either as a default in the client or as an argument to this method."
            raise ValueError(msg)
        data = await self._make_api_call(
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}",
            region=region,
        )
        return RiotAccount.from_api_response(data)

    # Summoner API
    async def get_summoner_by_puuid(
        self,
        puuid: str,
        region: RegionV4 | None,
    ) -> Summoner:
        """
        Get a summoner by PUUID.

        Args:
            puuid: The summoner's PUUID
            region: Region to use (defaults to client's default)

        Returns:
            Summoner with summoner information

        """
        region = region or self.default_v4_region
        if region is None:
            msg = "A v4 region must be provided either as a default in the client or as an argument to this method."
            raise ValueError(msg)
        data = await self._make_api_call(
            f"/lol/summoner/v4/summoners/by-puuid/{puuid}",
            region=region,
        )
        return Summoner.from_api_response(data)

    # League API
    async def get_league_entries_by_puuid(
        self,
        puuid: str,
        region: RegionV4 | None,
    ) -> list[LeagueEntry]:
        """
        Get league entries by PUUID.

        Args:
            puuid: The summoner's PUUID
            region: Region to use (defaults to client's default)

        Returns:
            List of league entries for the summoner

        """
        region = region or self.default_v4_region
        if region is None:
            msg = "A v4 region must be provided either as a default in the client or as an argument to this method."
            raise ValueError(msg)
        data = await self._make_api_call(
            f"/lol/league/v4/entries/by-puuid/{puuid}",
            region=region,
        )
        # The league API returns a list, not the usual dict
        entries_list: list[dict[str, Any]] = data  # type: ignore[assignment]
        return [LeagueEntry.from_api_response(entry) for entry in entries_list]

    # Match API
    async def get_match(self, match_id: str, region: RegionV5 | None = None) -> Match:
        """
        Get match details by match ID.

        Args:
            match_id: The match ID
            region: Region to use (defaults to client's default)

        Returns:
            Match with detailed match information

        """
        region = region or self.default_v5_region
        if region is None:
            msg = "A v5 region must be provided either as a default in the client or as an argument to this method."
            raise ValueError(msg)
        data = await self._make_api_call(
            f"/lol/match/v5/matches/{match_id}",
            region=region,
        )
        return Match.from_api_response(data)

    async def get_match_ids_by_puuid(  # noqa: C901
        self,
        puuid: str,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: Queue | int | None = None,
        match_type: MatchType | str | None = None,
        start: int = 0,
        count: int = 20,
        region: RegionV5 | None = None,
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
            msg = "count must be between 0 and 100"
            raise ValueError(msg)

        region = region or self.default_v5_region
        if region is None:
            msg = "A v5 region must be provided either as a default in the client or as an argument to this method."
            raise ValueError(msg)

        # Convert datetime objects to epoch timestamps
        start_timestamp = None
        if start_time is not None:
            start_timestamp = int(start_time.timestamp()) if isinstance(start_time, datetime) else start_time

        end_timestamp = None
        if end_time is not None:
            end_timestamp = int(end_time.timestamp()) if isinstance(end_time, datetime) else end_time

        # Build query parameters dict
        params: dict[str, int | str] = {}
        if start_timestamp is not None:
            params["startTime"] = start_timestamp
        if end_timestamp is not None:
            params["endTime"] = end_timestamp
        if queue is not None:
            params["queue"] = queue.value if isinstance(queue, Queue) else queue
        if match_type is not None:
            params["type"] = match_type.value if isinstance(match_type, MatchType) else match_type
        if start != 0:
            params["start"] = start
        if count != DEFAULT_MATCH_ID_COUNT:
            params["count"] = count

        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        data = await self._make_api_call(endpoint, region=region, params=params)
        # The match IDs API returns a list of strings, not the usual dict
        match_ids: list[str] = data  # type: ignore[assignment]
        return match_ids

    # High-level convenience methods
    async def get_player(
        self,
        game_name: str,
        tag_line: str,
        v4_region: RegionV4 | None = None,
        v5_region: RegionV5 | None = None,
    ) -> "Player":
        """
        Create a Player object for convenient high-level access.

        Args:
            game_name: Player's game name (without #)
            tag_line: Player's tag line (without #)
            v4_region: Platform region for v4 endpoints (defaults to client default)
            v5_region: Regional region for v5 endpoints (defaults to client default)

        Returns:
            Player object providing high-level access to player data

        """
        # Import here to avoid circular imports
        from .models.player import Player

        return await Player.create(
            client=self,
            game_name=game_name,
            tag_line=tag_line,
            v4_region=v4_region,
            v5_region=v5_region,
        )

    async def get_players(
        self,
        riot_ids: list[str],
        v4_region: RegionV4 | None = None,
        v5_region: RegionV5 | None = None,
    ) -> list["Player"]:
        """
        Create multiple Player objects efficiently using parallel processing.

        Args:
            riot_ids: List of Riot IDs in "username#tagline" format (e.g., ["bexli#bex", "player2#tag"])
            v4_region: Platform region for v4 endpoints (defaults to client default)
            v5_region: Regional region for v5 endpoints (defaults to client default)

        Returns:
            List of Player objects providing high-level access to player data

        Raises:
            ValueError: If any riot_id is not in the correct format

        """
        # Import here to avoid circular imports
        from .models.player import Player

        async def create_player(riot_id: str) -> Player:
            """Helper function to create a single player."""
            return await Player.by_riot_id(
                client=self,
                riot_id=riot_id,
                v4_region=v4_region,
                v5_region=v5_region,
            )

        # Use asyncio.gather for efficient parallel processing
        return await asyncio.gather(*[create_player(riot_id) for riot_id in riot_ids])

    async def close(self) -> None:
        """Close the client session."""
        if self._session:
            await self._session.close()
