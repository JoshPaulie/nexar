"""Tests for client functionality."""

from typing import TYPE_CHECKING

import pytest

from nexar import (
    NexarClient,
    NotFoundError,
    RateLimit,
    RateLimiter,
    RegionV4,
    RegionV5,
    RiotAccount,
    Summoner,
)

if TYPE_CHECKING:
    from nexar.client import NexarClient


class TestNexarClient:
    """Test the main NexarClient class."""

    def test_client_initialization(self, riot_api_key: str) -> None:
        """Test client initializes correctly."""
        client = NexarClient(
            riot_api_key=riot_api_key,
            default_v4_region=RegionV4.NA1,
            default_v5_region=RegionV5.AMERICAS,
        )

        assert client.riot_api_key == riot_api_key
        assert client.default_v4_region == RegionV4.NA1
        assert client.default_v5_region == RegionV5.AMERICAS

    def test_client_initialization_with_rate_limiter(self, riot_api_key: str) -> None:
        """Test client initializes with custom rate limiter."""
        custom_rate_limiter = RateLimiter([RateLimit(requests=5, window_seconds=10)])

        client = NexarClient(
            riot_api_key=riot_api_key,
            default_v4_region=RegionV4.NA1,
            default_v5_region=RegionV5.AMERICAS,
            rate_limiter=custom_rate_limiter,
        )

        assert client.rate_limiter is custom_rate_limiter

    def test_client_default_rate_limiter(self, riot_api_key: str) -> None:
        """Test client uses default rate limiter when none provided."""
        client = NexarClient(
            riot_api_key=riot_api_key,
            default_v4_region=RegionV4.NA1,
            default_v5_region=RegionV5.AMERICAS,
        )

        assert client.rate_limiter is not None
        assert len(client.rate_limiter.rate_limits) == 2
        assert client.rate_limiter.rate_limits[0].requests == 20
        assert client.rate_limiter.rate_limits[0].window_seconds == 1
        assert client.rate_limiter.rate_limits[1].requests == 100
        assert client.rate_limiter.rate_limits[1].window_seconds == 120

    def test_get_rate_limit_status(self, client: "NexarClient") -> None:
        """Test rate limit status retrieval."""
        status = client.get_rate_limit_status()

        assert "limit_1" in status
        assert "limit_2" in status
        assert status["limit_1"]["requests"] == 20
        assert status["limit_1"]["window_seconds"] == 1
        assert status["limit_2"]["requests"] == 100
        assert status["limit_2"]["window_seconds"] == 120

    def test_reset_rate_limiter(self, client: "NexarClient") -> None:
        """Test rate limiter reset functionality."""
        # Reset rate limiter
        client.reset_rate_limiter()

        # Get status after reset
        status_after = client.get_rate_limit_status()

        # Should have fresh state
        assert status_after["limit_1"]["current_usage"] == 0
        assert status_after["limit_2"]["current_usage"] == 0

    async def test_get_riot_account_success(self, client: "NexarClient") -> None:
        """Test successful riot account retrieval."""
        result = await client.get_riot_account("bexli", "bex")

        assert isinstance(result, RiotAccount)
        assert result.puuid is not None
        assert result.game_name == "bexli"
        assert result.tag_line == "bex"

    async def test_get_riot_account_with_custom_region(self, client: "NexarClient") -> None:
        """Test riot account retrieval with custom region."""
        result = await client.get_riot_account(
            "bexli", "bex", region=RegionV5.AMERICAS
        )

        assert isinstance(result, RiotAccount)
        assert result.puuid is not None
        assert result.game_name == "bexli"
        assert result.tag_line == "bex"

    async def test_get_summoner_by_puuid_success(self, client: "NexarClient") -> None:
        """Test successful summoner retrieval by PUUID."""
        # Use hardcoded PUUID to reduce API calls during testing
        test_puuid = "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA"

        # Use NA1 region for summoner lookup
        result = await client.get_summoner_by_puuid(test_puuid, region=RegionV4.NA1)

        assert isinstance(result, Summoner)
        assert result.puuid == test_puuid
        assert result.id is not None
        assert result.summoner_level > 0

    async def test_not_found_error(self, real_client: "NexarClient") -> None:
        """Test handling of 404 Not Found error."""
        with pytest.raises(NotFoundError) as exc_info:
            await real_client.get_riot_account("NonExistentPlayer999", "FAKE")

        assert exc_info.value.status_code == 404

    async def test_get_players_success(self, client: "NexarClient") -> None:
        """Test successful multiple player retrieval."""
        riot_ids = ["bexli#bex", "bexli#bex"]  # Use the mocked data

        players = await client.get_players(riot_ids)

        assert isinstance(players, list)
        assert len(players) == 2

        # Check first player
        assert players[0].game_name == "bexli"
        assert players[0].tag_line == "bex"

        # Check second player
        assert players[1].game_name == "bexli"
        assert players[1].tag_line == "bex"

        # Verify that riot accounts were pre-fetched
        for player in players:
            # Should not make additional API calls since accounts were pre-fetched
            assert player.riot_account.puuid is not None

    async def test_get_players_with_invalid_riot_id(self, client: "NexarClient") -> None:
        """Test get_players with invalid riot ID format."""
        invalid_riot_ids = ["bexli#bex", "invalid_format"]

        with pytest.raises(ValueError) as exc_info:
            await client.get_players(invalid_riot_ids)

        assert "Invalid Riot ID format" in str(exc_info.value)

    async def test_get_players_empty_list(self, client: "NexarClient") -> None:
        """Test get_players with empty list."""
        players = await client.get_players([])

        assert isinstance(players, list)
        assert len(players) == 0

    async def test_get_players_single_player(self, client: "NexarClient") -> None:
        """Test get_players with single player."""
        players = await client.get_players(["bexli#bex"])

        assert isinstance(players, list)
        assert len(players) == 1
        assert players[0].game_name == "bexli"
        assert players[0].tag_line == "bex"
