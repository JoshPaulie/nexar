"""Main client for the Nexar SDK."""

from datetime import datetime
from typing import Any

import requests

from .enums import MatchType, QueueId, RegionV4, RegionV5
from .exceptions import (
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)
from .models import Match, RiotAccount, Summoner


class NexarClient:
    """Main client for interacting with the Riot Games API."""

    def __init__(
        self,
        riot_api_key: str,
        default_v4_region: RegionV4,
        default_v5_region: RegionV5,
    ) -> None:
        """Initialize the Nexar client.

        Args:
            riot_api_key: Your Riot Games API key
            default_v4_region: Default region for platform-specific endpoints
            default_v5_region: Default region for regional endpoints
        """
        self.riot_api_key = riot_api_key
        self.default_v4_region = default_v4_region
        self.default_v5_region = default_v5_region

    def _make_api_call(
        self, endpoint: str, region: RegionV4 | RegionV5
    ) -> dict[str, Any]:
        """Make an API call to the Riot Games API.

        Args:
            endpoint: The API endpoint path
            region: The region to use for the request

        Returns:
            JSON response from the API

        Raises:
            RiotAPIError: If the API returns an error status code
        """
        # Construct the full URL with the region
        url = f"https://{region.value}.api.riotgames.com{endpoint}"

        # Set required headers for Riot API
        headers = {
            "X-Riot-Token": self.riot_api_key,
            "User-Agent": "nexar-python-sdk/0.1.0",
            "Accept": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)
            self._handle_response_errors(response)
            return response.json()
        except requests.RequestException as e:
            raise RiotAPIError(0, f"Request failed: {e}") from e

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

        # Build query parameters
        params = []
        if start_timestamp is not None:
            params.append(f"startTime={start_timestamp}")
        if end_timestamp is not None:
            params.append(f"endTime={end_timestamp}")
        if queue is not None:
            queue_id = queue.value if isinstance(queue, QueueId) else queue
            params.append(f"queue={queue_id}")
        if match_type is not None:
            type_value = (
                match_type.value if isinstance(match_type, MatchType) else match_type
            )
            params.append(f"type={type_value}")
        if start != 0:
            params.append(f"start={start}")
        if count != 20:
            params.append(f"count={count}")

        # Build endpoint with query string
        endpoint = f"/lol/match/v5/matches/by-puuid/{puuid}/ids"
        if params:
            endpoint += "?" + "&".join(params)

        data = self._make_api_call(endpoint, region=region)
        return data
