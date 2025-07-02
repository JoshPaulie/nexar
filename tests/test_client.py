"""Tests for client functionality."""

import pytest

from nexar import (
    NexarClient,
    NotFoundError,
    RegionV4,
    RegionV5,
    RiotAccount,
    Summoner,
)


class TestNexarClient:
    """Test the main NexarClient class."""

    def test_client_initialization(self, riot_api_key):
        """Test client initializes correctly."""
        client = NexarClient(
            riot_api_key=riot_api_key,
            default_v4_region=RegionV4.NA1,
            default_v5_region=RegionV5.AMERICAS,
        )

        assert client.riot_api_key == riot_api_key
        assert client.default_v4_region == RegionV4.NA1
        assert client.default_v5_region == RegionV5.AMERICAS

    def test_get_riot_account_success(self, client):
        """Test successful riot account retrieval."""
        result = client.get_riot_account("bexli", "bex")

        assert isinstance(result, RiotAccount)
        assert result.puuid is not None
        assert result.game_name == "bexli"
        assert result.tag_line == "bex"

    def test_get_riot_account_with_custom_region(self, client):
        """Test riot account retrieval with custom region."""
        result = client.get_riot_account("bexli", "bex", region=RegionV5.AMERICAS)

        assert isinstance(result, RiotAccount)
        assert result.puuid is not None
        assert result.game_name == "bexli"
        assert result.tag_line == "bex"

    def test_get_summoner_by_puuid_success(self, client):
        """Test successful summoner retrieval by PUUID."""
        # First get a riot account to get a real PUUID
        account = client.get_riot_account("bexli", "bex")

        # Use NA1 region for summoner lookup
        result = client.get_summoner_by_puuid(account.puuid, region=RegionV4.NA1)

        assert isinstance(result, Summoner)
        assert result.puuid == account.puuid
        assert result.id is not None
        assert result.summoner_level > 0

    def test_not_found_error(self, client):
        """Test handling of 404 Not Found error."""
        with pytest.raises(NotFoundError) as exc_info:
            client.get_riot_account("NonExistentPlayer999", "FAKE")

        assert exc_info.value.status_code == 404
