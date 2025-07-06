"""Tests for domain models."""

from datetime import datetime

import pytest

from nexar.enums import RegionV4
from nexar.models import RiotAccount, Summoner


class TestRiotAccount:
    """Test the RiotAccount model."""

    def test_riot_account_creation(self):
        """Test RiotAccount can be created directly."""
        account = RiotAccount(
            puuid="test-puuid",
            game_name="TestPlayer",
            tag_line="TEST",
        )

        assert account.puuid == "test-puuid"
        assert account.game_name == "TestPlayer"
        assert account.tag_line == "TEST"

    async def test_riot_account_from_api_response(self, async_client):
        """Test RiotAccount creation from real API response."""
        # Get real API data and test the model parsing
        account = await async_client.get_riot_account("bexli", "bex")

        assert account.puuid is not None
        assert account.game_name == "bexli"
        assert account.tag_line == "bex"

    def test_riot_account_immutable(self):
        """Test that RiotAccount is immutable."""
        account = RiotAccount(
            puuid="test-puuid",
            game_name="TestPlayer",
            tag_line="TEST",
        )

        with pytest.raises(AttributeError):
            account.puuid = "new-puuid"


class TestSummoner:
    """Test the Summoner model."""

    def test_summoner_creation(self):
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

    async def test_summoner_from_api_response(self, async_client):
        """Test Summoner creation from real API response."""
        # Use hardcoded PUUID to reduce API calls during testing
        test_puuid = "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA"
        summoner = await async_client.get_summoner_by_puuid(test_puuid, region=RegionV4.NA1)

        assert summoner.id is not None
        assert summoner.profile_icon_id is not None
        assert summoner.puuid == test_puuid
        assert summoner.summoner_level > 0

    def test_summoner_immutable(self):
        """Test that Summoner is immutable."""
        summoner = Summoner(
            id="test-summoner-id",
            puuid="test-puuid",
            profile_icon_id=1234,
            revision_date=datetime.fromtimestamp(1609459200),
            summoner_level=150,
        )

        with pytest.raises(AttributeError):
            summoner.puuid = "new-puuid"
