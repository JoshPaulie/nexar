"""Main client for the Nexar SDK."""

from datetime import datetime
from typing import Any

import requests
import requests_cache

from .cache import DEFAULT_CACHE_CONFIG, CacheConfig
from .enums import MatchType, QueueId, RegionV4, RegionV5
from .exceptions import (
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)
from .logging import get_logger
from .models import LeagueEntry, Match, RiotAccount, Summoner
from .models.player import Player
from .rate_limiter import RateLimiter


class NexarClient:
    """Main client for interacting with the Riot Games API."""

    def __init__(
        self,
        riot_api_key: str,
        default_v4_region: RegionV4,
        default_v5_region: RegionV5,
        cache_config: CacheConfig | None = None,
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        """Initialize the Nexar client.

        Args:
            riot_api_key: Your Riot Games API key
            default_v4_region: Default region for platform-specific endpoints
            default_v5_region: Default region for regional endpoints
            cache_config: Cache configuration (uses default if None)
            rate_limiter: Rate limiter configuration (uses default if None)
        """
        self.riot_api_key = riot_api_key
        self.default_v4_region = default_v4_region
        self.default_v5_region = default_v5_region
        self.cache_config = cache_config or DEFAULT_CACHE_CONFIG
        self.rate_limiter = rate_limiter or RateLimiter.create_default()
        self._logger = get_logger()

        # API call tracking (always enabled, debug display is conditional)
        self._api_call_count = 0

        # Initialize caching if enabled
        if self.cache_config.enabled:
            # Create per-URL expiration mapping
            urls_expire_after = {}
            for endpoint_pattern, config in self.cache_config.endpoint_config.items():
                if isinstance(config, dict) and config.get("enabled", True):
                    expire_time = config.get(
                        "expire_after", self.cache_config.expire_after
                    )
                    # Map pattern to actual URLs that might match
                    urls_expire_after[f"*{endpoint_pattern}*"] = expire_time
                elif isinstance(config, dict) and not config.get("enabled", True):
                    # For disabled endpoints, we'll handle this differently
                    continue

            # Create cached session
            self._session = requests_cache.CachedSession(
                cache_name=self.cache_config.cache_name,
                backend=self.cache_config.backend,
                expire_after=self.cache_config.expire_after,
                urls_expire_after=urls_expire_after if urls_expire_after else None,
                allowable_codes=[200],  # Only cache successful responses
                allowable_methods=["GET"],  # Only cache GET requests
            )
        else:
            self._session = requests.Session()

        self._setup_caching()

    def _make_api_call(
        self,
        endpoint: str,
        region: RegionV4 | RegionV5,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API call to the Riot Games API.

        Args:
            endpoint: The API endpoint path
            region: The region to use for the request
            params: Optional query parameters dict

        Returns:
            JSON response from the API

        Raises:
            RiotAPIError: If the API returns an error status code
        """
        # Apply rate limiting before making the request
        self.rate_limiter.wait_if_needed()

        # Always increment API call counter
        self._api_call_count += 1

        # Log API call start
        self._logger.log_api_call_start(
            self._api_call_count, endpoint, region.value, params
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
            # Use the cached session for requests
            response = self._session.get(
                url, headers=headers, params=params, timeout=30
            )

            # Record the request after it's made
            self.rate_limiter.record_request()

            self._handle_response_errors(response)

            # Log successful response
            from_cache = getattr(response, "from_cache", False)
            self._logger.log_api_call_success(response.status_code, from_cache)

            return response.json()
        except requests.RequestException as e:
            # Still record the request even if it failed
            self.rate_limiter.record_request()
            self._logger.log_api_call_error(e)
            raise RiotAPIError(0, f"Request failed: {e}") from e
        except (RateLimitError, RiotAPIError) as e:
            # Still record the request even if it failed
            self.rate_limiter.record_request()
            self._logger.log_api_call_error(e)
            raise

    def _get_api_call_count(self) -> int:
        """Get the current number of API calls made by this client.

        Returns:
            Number of API calls made since client initialization
        """
        return self._api_call_count

    def _reset_api_call_count(self) -> None:
        """Reset the API call counter to zero."""
        self._api_call_count = 0
        self._logger.reset_stats()

    def get_rate_limit_status(self) -> dict[str, Any]:
        """Get current rate limit status.

        Returns:
            Dictionary with current rate limit usage and remaining requests
        """
        return self.rate_limiter.get_status()

    def reset_rate_limiter(self) -> None:
        """Reset the rate limiter state."""
        self.rate_limiter = RateLimiter.create_default()

    def get_api_call_stats(self) -> dict[str, int]:
        """Get API call statistics.

        Returns:
            Dictionary with call statistics including total calls, cache hits, and fresh calls
        """
        return self._logger.get_stats()

    def print_api_call_summary(self) -> None:
        """Print a summary of API calls made so far."""
        self._logger.log_stats_summary()

    def _handle_response_errors(self, response: requests.Response) -> None:
        """Handle HTTP errors from the API response."""
        if response.status_code == 200:
            return

        try:
            error_data = response.json()
            message = error_data.get("status", {}).get("message", "Unknown error")
        except ValueError:
            message = response.text or "Unknown error"

        if response.status_code == 401:
            raise UnauthorizedError(response.status_code, message)
        elif response.status_code == 403:
            raise ForbiddenError(response.status_code, message)
        elif response.status_code == 404:
            raise NotFoundError(response.status_code, message)
        elif response.status_code == 429:
            raise RateLimitError(response.status_code, message)
        else:
            raise RiotAPIError(response.status_code, message)

    def _setup_caching(self) -> None:
        """Set up caching for the HTTP session if enabled."""
        if not self.cache_config.enabled:
            return

        # Log cache setup information
        has_cache = hasattr(self._session, "cache")
        cache_type = type(self._session.cache) if has_cache else None
        self._logger.log_cache_setup(
            self.cache_config.cache_name,
            self.cache_config.backend,
            has_cache,
            cache_type,
        )

        if has_cache:
            # Log cache configuration details
            has_url_expiration = (
                hasattr(self._session, "settings")
                and hasattr(self._session.settings, "urls_expire_after")
                and bool(self._session.settings.urls_expire_after)
            )
            self._logger.log_cache_config(
                self.cache_config.expire_after, has_url_expiration
            )

    def clear_cache(self) -> None:
        """Clear all cached responses."""
        if hasattr(self._session, "cache") and self._session.cache:
            self._session.cache.clear()
            self._logger.log_cache_cleared()

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about the current cache state.

        Returns:
            Dictionary with cache statistics and configuration
        """
        info = {
            "enabled": self.cache_config.enabled,
            "backend": self.cache_config.backend,
            "cache_name": self.cache_config.cache_name,
            "default_expire_after": self.cache_config.expire_after,
        }

        if hasattr(self._session, "cache") and self._session.cache:
            try:
                # Try to get cache size if the backend supports it
                cache = self._session.cache
                if hasattr(cache, "__len__"):
                    info["cached_responses"] = len(cache)
                if hasattr(cache, "size"):
                    info["cache_size"] = cache.size
            except Exception:
                # Some backends might not support these operations
                pass

        return info

    # Account API
    def get_riot_account(
        self, game_name: str, tag_line: str, region: RegionV5 | None = None
    ) -> RiotAccount:
        """Get a Riot account by game name and tag line.

        Args:
            game_name: The game name (without #)
            tag_line: The tag line (without #)
            region: Region to use (defaults to client's default)

        Returns:
            RiotAccount with account information
        """
        region = region or self.default_v5_region
        data = self._make_api_call(
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}",
            region=region,
        )
        return RiotAccount.from_api_response(data)

    # Summoner API
    def get_summoner_by_puuid(
        self, puuid: str, region: RegionV4 | None = None
    ) -> Summoner:
        """Get a summoner by PUUID.

        Args:
            puuid: The summoner's PUUID
            region: Region to use (defaults to client's default)

        Returns:
            Summoner with summoner information
        """
        region = region or self.default_v4_region
        data = self._make_api_call(
            f"/lol/summoner/v4/summoners/by-puuid/{puuid}",
            region=region,
        )
        return Summoner.from_api_response(data)

    # League API
    def get_league_entries_by_puuid(
        self, puuid: str, region: RegionV4 | None = None
    ) -> list[LeagueEntry]:
        """Get league entries by PUUID.

        Args:
            puuid: The summoner's PUUID
            region: Region to use (defaults to client's default)

        Returns:
            List of league entries for the summoner
        """
        region = region or self.default_v4_region
        data = self._make_api_call(
            f"/lol/league/v4/entries/by-puuid/{puuid}",
            region=region,
        )
        return [LeagueEntry.from_api_response(entry) for entry in data]

    # Match API
    def get_match(self, match_id: str, region: RegionV5 | None = None) -> Match:
        """Get match details by match ID.

        Args:
            match_id: The match ID
            region: Region to use (defaults to client's default)

        Returns:
            Match with detailed match information
        """
        region = region or self.default_v5_region
        data = self._make_api_call(
            f"/lol/match/v5/matches/{match_id}",
            region=region,
        )
        return Match.from_api_response(data)

    def get_match_ids_by_puuid(
        self,
        puuid: str,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: QueueId | int | None = None,
        match_type: MatchType | str | None = None,
        start: int = 0,
        count: int = 20,
        region: RegionV5 | None = None,
    ) -> list[str]:
        """Get match IDs by PUUID with optional filters.

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
        if not 0 <= count <= 100:
            raise ValueError("count must be between 0 and 100")

        region = region or self.default_v5_region

        # Convert datetime objects to epoch timestamps
        start_timestamp = None
        if start_time is not None:
            start_timestamp = (
                int(start_time.timestamp())
                if isinstance(start_time, datetime)
                else start_time
            )

        end_timestamp = None
        if end_time is not None:
            end_timestamp = (
                int(end_time.timestamp())
                if isinstance(end_time, datetime)
                else end_time
            )

        # Build query parameters dict
        params = {}
        if start_timestamp is not None:
            params["startTime"] = start_timestamp
        if end_timestamp is not None:
            params["endTime"] = end_timestamp
        if queue is not None:
            params["queue"] = queue.value if isinstance(queue, QueueId) else queue
        if match_type is not None:
            params["type"] = (
                match_type.value if isinstance(match_type, MatchType) else match_type
            )
        if start != 0:
            params["start"] = start
        if count != 20:
            params["count"] = count

        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        data = self._make_api_call(endpoint, region=region, params=params)
        return data

    # High-level convenience methods
    def get_player(
        self,
        game_name: str,
        tag_line: str,
        v4_region: RegionV4 | None = None,
        v5_region: RegionV5 | None = None,
    ) -> Player:
        """Create a Player object for convenient high-level access.

        Args:
            game_name: Player's game name (without #)
            tag_line: Player's tag line (without #)
            v4_region: Platform region for v4 endpoints (defaults to client default)
            v5_region: Regional region for v5 endpoints (defaults to client default)

        Returns:
            Player object providing high-level access to player data
        """
        return Player(
            client=self,
            game_name=game_name,
            tag_line=tag_line,
            v4_region=v4_region,
            v5_region=v5_region,
        )
