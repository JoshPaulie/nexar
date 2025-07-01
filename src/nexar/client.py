"""Main client for the Nexar SDK."""

from typing import Any

import requests

from .enums import RegionV4, RegionV5
from .exceptions import (
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)
from .models import RiotAccount, Summoner


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

    def get_summoner_by_name(
        self, summoner_name: str, region: RegionV4 | None = None
    ) -> Summoner:
        """Get a summoner by summoner name.

        Args:
            summoner_name: The summoner's name
            region: Region to use (defaults to client's default)

        Returns:
            Summoner with summoner information
        """
        region = region or self.default_v4_region
        data = self._make_api_call(
            f"/lol/summoner/v4/summoners/by-name/{summoner_name}",
            region=region,
        )
        return Summoner.from_api_response(data)
