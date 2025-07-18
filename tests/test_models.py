"""Tests for domain models."""

from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from nexar.enums import Region
from nexar.models import RiotAccount, Summoner

if TYPE_CHECKING:
    from nexar.client import NexarClient


class TestRiotAccount:
    """Test the RiotAccount model."""

    def test_riot_account_creation(self) -> None:
        """Test RiotAccount can be created directly."""
        account = RiotAccount(
            puuid="test-puuid",
            game_name="TestPlayer",
            tag_line="TEST",
        )

        assert account.puuid == "test-puuid"
        assert account.game_name == "TestPlayer"
        assert account.tag_line == "TEST"

    async def test_riot_account_from_api_response(self, client: "NexarClient") -> None:
        """Test RiotAccount creation from real API response."""
        # Get real API data and test the model parsing
        account = await client.get_riot_account("bexli", "bex")

        assert account.puuid is not None
        assert account.game_name == "bexli"
        assert account.tag_line == "bex"

    def test_riot_account_immutable(self) -> None:
        """Test that RiotAccount is immutable."""
        account = RiotAccount(
            puuid="test-puuid",
            game_name="TestPlayer",
            tag_line="TEST",
        )

        with pytest.raises(AttributeError):
            account.puuid = "new-puuid"  # type: ignore[misc]


class TestSummoner:
    """Test the Summoner model."""

    def test_summoner_creation(self) -> None:
        """Test Summoner can be created directly."""
        summoner = Summoner(
            id="test-summoner-id",
            puuid="test-puuid",
            profile_icon_id=1234,
            revision_date=datetime.fromtimestamp(1609459200),
            summoner_level=150,
        )

        assert summoner.id == "test-summoner-id"
        assert summoner.puuid == "test-puuid"
        assert summoner.summoner_level == 150

    async def test_summoner_from_api_response(self, client: "NexarClient") -> None:
        """Test Summoner creation from real API response."""
        # Use hardcoded PUUID to reduce API calls during testing
        test_puuid = "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA"
        summoner = await client.get_summoner_by_puuid(test_puuid, region=Region.NA1)

        assert summoner.id is not None
        assert summoner.profile_icon_id is not None
        assert summoner.puuid == test_puuid
        assert summoner.summoner_level > 0

    def test_summoner_immutable(self) -> None:
        """Test that Summoner is immutable."""
        summoner = Summoner(
            id="test-summoner-id",
            puuid="test-puuid",
            profile_icon_id=1234,
            revision_date=datetime.fromtimestamp(1609459200),
            summoner_level=150,
        )

        with pytest.raises(AttributeError):
            summoner.puuid = "new-puuid"  # type: ignore[misc]
