"""Tests for client functionality."""

import pytest

from nexar import (
    ForbiddenError,
    NexarClient,
    NotFoundError,
    RateLimitError,
    RegionV4,
    RegionV5,
    RiotAccount,
    RiotAPIError,
    Summoner,
    UnauthorizedError,
)


class TestNexarClient:
    """Test the main NexarClient class."""

    def test_client_initialization(self, mock_api_key):
        """Test client initializes correctly."""
        client = NexarClient(
            riot_api_key=mock_api_key,
            default_v4_region=RegionV4.NA1,
            default_v5_region=RegionV5.AMERICAS,
        )

        assert client.riot_api_key == mock_api_key
        assert client.default_v4_region == RegionV4.NA1
        assert client.default_v5_region == RegionV5.AMERICAS

    def test_get_riot_account_success(
        self, client, requests_mock_obj, mock_riot_account_response
    ):
        """Test successful riot account retrieval."""
        # Mock the API response
        requests_mock_obj.get(
            "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/TestPlayer/TEST",
            json=mock_riot_account_response,
        )

        result = client.get_riot_account("TestPlayer", "TEST")

        assert isinstance(result, RiotAccount)
        assert result.puuid == "test-puuid-123"
        assert result.game_name == "TestPlayer"
        assert result.tag_line == "TEST"

    def test_get_riot_account_with_custom_region(
        self, client, requests_mock_obj, mock_riot_account_response
    ):
        """Test riot account retrieval with custom region."""
        requests_mock_obj.get(
            "https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/TestPlayer/TEST",
            json=mock_riot_account_response,
        )

        result = client.get_riot_account("TestPlayer", "TEST", region=RegionV5.EUROPE)

        assert isinstance(result, RiotAccount)
        assert result.puuid == "test-puuid-123"

    def test_get_summoner_by_puuid_success(
        self, client, requests_mock_obj, mock_summoner_response
    ):
        """Test successful summoner retrieval by PUUID."""
        requests_mock_obj.get(
            "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/test-puuid-123",
            json=mock_summoner_response,
        )

        result = client.get_summoner_by_puuid("test-puuid-123")

        assert isinstance(result, Summoner)
        assert result.puuid == "test-puuid-123"
        assert result.id == "test-summoner-id"
        assert result.summoner_level == 150

    def test_get_summoner_by_name_success(
        self, client, requests_mock_obj, mock_summoner_response
    ):
        """Test successful summoner retrieval by name."""
        requests_mock_obj.get(
            "https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/TestPlayer",
            json=mock_summoner_response,
        )

        result = client.get_summoner_by_name("TestPlayer")

        assert isinstance(result, Summoner)
        assert result.id == "test-summoner-id"

    def test_unauthorized_error(self, client, requests_mock_obj):
        """Test handling of 401 Unauthorized error."""
        requests_mock_obj.get(
            "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/TestPlayer/TEST",
            status_code=401,
            json={"status": {"message": "Unauthorized"}},
        )

        with pytest.raises(UnauthorizedError) as exc_info:
            client.get_riot_account("TestPlayer", "TEST")

        assert exc_info.value.status_code == 401
        assert "Unauthorized" in str(exc_info.value)

    def test_forbidden_error(self, client, requests_mock_obj):
        """Test handling of 403 Forbidden error."""
        requests_mock_obj.get(
            "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/TestPlayer/TEST",
            status_code=403,
            json={"status": {"message": "Forbidden"}},
        )

        with pytest.raises(ForbiddenError) as exc_info:
            client.get_riot_account("TestPlayer", "TEST")

        assert exc_info.value.status_code == 403

    def test_not_found_error(self, client, requests_mock_obj):
        """Test handling of 404 Not Found error."""
        requests_mock_obj.get(
            "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/NonExistent/TEST",
            status_code=404,
            json={"status": {"message": "Data not found"}},
        )

        with pytest.raises(NotFoundError) as exc_info:
            client.get_riot_account("NonExistent", "TEST")

        assert exc_info.value.status_code == 404

    def test_rate_limit_error(self, client, requests_mock_obj):
        """Test handling of 429 Rate Limit error."""
        requests_mock_obj.get(
            "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/TestPlayer/TEST",
            status_code=429,
            json={"status": {"message": "Rate limit exceeded"}},
        )

        with pytest.raises(RateLimitError) as exc_info:
            client.get_riot_account("TestPlayer", "TEST")

        assert exc_info.value.status_code == 429

    def test_generic_api_error(self, client, requests_mock_obj):
        """Test handling of generic API errors."""
        requests_mock_obj.get(
            "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/TestPlayer/TEST",
            status_code=500,
            json={"status": {"message": "Internal server error"}},
        )

        with pytest.raises(RiotAPIError) as exc_info:
            client.get_riot_account("TestPlayer", "TEST")

        assert exc_info.value.status_code == 500

    def test_network_error(self, client, requests_mock_obj):
        """Test handling of network errors."""
        import requests

        requests_mock_obj.get(
            "https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/TestPlayer/TEST",
            exc=requests.exceptions.ConnectTimeout,
        )

        with pytest.raises(RiotAPIError) as exc_info:
            client.get_riot_account("TestPlayer", "TEST")

        assert "Request failed" in str(exc_info.value)
