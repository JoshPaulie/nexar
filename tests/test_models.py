"""Tests for domain models."""

import pytest

from nexar.models import RiotAccount, Summoner


class TestRiotAccount:
    """Test the RiotAccount model."""

    def test_riot_account_creation(self):
        """Test RiotAccount can be created directly."""
        account = RiotAccount(
            puuid="test-puuid", game_name="TestPlayer", tag_line="TEST"
        )

        assert account.puuid == "test-puuid"
        assert account.game_name == "TestPlayer"
        assert account.tag_line == "TEST"

    def test_riot_account_from_api_response(self, mock_riot_account_response):
        """Test RiotAccount creation from API response."""
        account = RiotAccount.from_api_response(mock_riot_account_response)

        assert account.puuid == "test-puuid-123"
        assert account.game_name == "TestPlayer"
        assert account.tag_line == "TEST"

    def test_riot_account_immutable(self):
        """Test that RiotAccount is immutable."""
        account = RiotAccount(
            puuid="test-puuid", game_name="TestPlayer", tag_line="TEST"
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
            revision_date=1609459200000,
            summoner_level=150,
        )

        assert summoner.id == "test-summoner-id"
        assert summoner.puuid == "test-puuid"
        assert summoner.summoner_level == 150

    def test_summoner_from_api_response(self, mock_summoner_response):
        """Test Summoner creation from API response."""
        summoner = Summoner.from_api_response(mock_summoner_response)

        assert summoner.id == "test-summoner-id"
        assert summoner.profile_icon_id == 1234
        assert summoner.puuid == "test-puuid-123"
        assert summoner.summoner_level == 150

    def test_summoner_immutable(self):
        """Test that Summoner is immutable."""
        summoner = Summoner(
            id="test-summoner-id",
            puuid="test-puuid",
            profile_icon_id=1234,
            revision_date=1609459200000,
            summoner_level=150,
        )

        with pytest.raises(AttributeError):
            summoner.puuid = "new-puuid"
