from enum import Enum, auto

import requests


class Region:
    class v4(Enum):
        NA1 = auto()

    class v5(Enum):
        AMERICAS = auto()


class NexarClient:
    def __init__(
        self,
        riot_api_key: str,
        default_v4_region: Region.v4,
        default_v5_region: Region.v5,
    ) -> None:
        self.riot_api_key = riot_api_key
        self.default_v4_region = default_v4_region
        self.default_v5_region = default_v5_region

    def _make_api_call(self, endpoint: str, region_type: Region.v4 | Region.v5):
        """
        Make an API call to the Riot Games API.

        Args:
            endpoint: The API endpoint path (e.g., "/riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}")

        Returns:
            dict: JSON response from the API

        Raises:
            requests.HTTPError: If the API returns an error status code
        """
        # Construct the full URL with the region
        url = (
            f"https://{self.default_v4_region.name}.api.riotgames.com{endpoint}"
            if region_type is Region.v4
            else f"https://{self.default_v5_region.name}.api.riotgames.com{endpoint}"
        )

        # Set required headers for Riot API
        headers = {
            "X-Riot-Token": self.riot_api_key,
            "User-Agent": "nexar-python-sdk/1.0.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Make the API request
        response = requests.get(url, headers=headers)

        # Raise an exception for bad status codes
        response.raise_for_status()

        return response.json()

    # Account v1
    # /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}
    def get_riot_account(self, game_name: str, tag_line: str):
        """
        Example response:
        {
            'puuid': '0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA',
            'gameName': 'bexli',
            'tagLine': 'bex'
        }
        """
        return self._make_api_call(
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}",
            region_type=Region.v5,
        )
