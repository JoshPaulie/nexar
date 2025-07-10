"""Tests for league-related functionality."""

from typing import TYPE_CHECKING

from nexar import LeagueEntry, MiniSeries
from nexar.enums import QueueId, RankDivision, RankTier

if TYPE_CHECKING:
    from nexar.client import NexarClient


class TestLeagueEntries:
    """Test league entry functionality."""

    async def test_get_league_entries_by_puuid_success(self, client: "NexarClient") -> None:
        """Test successful league entries retrieval by PUUID."""
        # Use hardcoded PUUID to reduce API calls during testing
        test_puuid = "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA"

        # Get league entries for the account
        result = await client.get_league_entries_by_puuid(test_puuid, None)

        # Should return a list of league entries
        assert isinstance(result, list)

        # If the account has ranked entries, validate the structure
        if result:
            for entry in result:
                assert isinstance(entry, LeagueEntry)
                assert entry.puuid == test_puuid
                assert entry.league_id is not None
                assert entry.queue_type is not None
                assert entry.tier is not None
                assert entry.division is not None
                assert isinstance(entry.league_points, int)
                assert isinstance(entry.wins, int)
                assert isinstance(entry.losses, int)
                assert isinstance(entry.hot_streak, bool)
                assert isinstance(entry.veteran, bool)
                assert isinstance(entry.fresh_blood, bool)
                assert isinstance(entry.inactive, bool)

                # Mini series may or may not be present
                if entry.mini_series:
                    assert isinstance(entry.mini_series, MiniSeries)
                    assert isinstance(entry.mini_series.losses, int)
                    assert isinstance(entry.mini_series.progress, str)
                    assert isinstance(entry.mini_series.target, int)
                    assert isinstance(entry.mini_series.wins, int)


class TestLeagueModels:
    """Test league model creation."""

    def test_mini_series_creation(self) -> None:
        """Test MiniSeries model creation from API response."""
        api_data = {"losses": 1, "progress": "WWN", "target": 3, "wins": 2}

        mini_series = MiniSeries.from_api_response(api_data)

        assert mini_series.losses == 1
        assert mini_series.progress == "WWN"
        assert mini_series.target == 3
        assert mini_series.wins == 2

    def test_league_entry_creation_without_mini_series(self) -> None:
        """Test LeagueEntry model creation without mini series."""
        api_data = {
            "leagueId": "test-league-id",
            "puuid": "test-puuid",
            "queueType": "RANKED_SOLO_5x5",
            "tier": "GOLD",
            "rank": "III",
            "leaguePoints": 75,
            "wins": 50,
            "losses": 30,
            "hotStreak": False,
            "veteran": True,
            "freshBlood": False,
            "inactive": False,
        }

        entry = LeagueEntry.from_api_response(api_data)

        assert entry.league_id == "test-league-id"
        assert entry.puuid == "test-puuid"
        assert entry.queue_type == QueueId.RANKED_SOLO_5x5
        assert entry.tier == RankTier.GOLD
        assert entry.division == RankDivision.THREE
        assert entry.league_points == 75
        assert entry.wins == 50
        assert entry.losses == 30
        assert entry.hot_streak is False
        assert entry.veteran is True
        assert entry.fresh_blood is False
        assert entry.inactive is False
        assert entry.mini_series is None

    def test_league_entry_creation_with_mini_series(self) -> None:
        """Test LeagueEntry model creation with mini series."""
        api_data = {
            "leagueId": "test-league-id",
            "puuid": "test-puuid",
            "queueType": "RANKED_SOLO_5x5",
            "tier": "SILVER",
            "rank": "I",
            "leaguePoints": 85,
            "wins": 25,
            "losses": 20,
            "hotStreak": True,
            "veteran": False,
            "freshBlood": True,
            "inactive": False,
            "miniSeries": {"losses": 0, "progress": "WW", "target": 3, "wins": 2},
        }

        entry = LeagueEntry.from_api_response(api_data)

        assert entry.league_id == "test-league-id"
        assert entry.puuid == "test-puuid"
        assert entry.queue_type == QueueId.RANKED_SOLO_5x5
        assert entry.tier == RankTier.SILVER
        assert entry.division == RankDivision.ONE
        assert entry.league_points == 85
        assert entry.wins == 25
        assert entry.losses == 20
        assert entry.hot_streak is True
        assert entry.veteran is False
        assert entry.fresh_blood is True
        assert entry.inactive is False

        # Check mini series
        assert entry.mini_series is not None
        assert entry.mini_series.losses == 0
        assert entry.mini_series.progress == "WW"
        assert entry.mini_series.target == 3
        assert entry.mini_series.wins == 2

    def test_league_entry_win_rate_calculation(self) -> None:
        """Test LeagueEntry win rate calculation."""
        api_data = {
            "leagueId": "test-league-id",
            "puuid": "test-puuid",
            "queueType": "RANKED_SOLO_5x5",
            "tier": "GOLD",
            "rank": "II",
            "leaguePoints": 50,
            "wins": 60,
            "losses": 40,
            "hotStreak": False,
            "veteran": False,
            "freshBlood": False,
            "inactive": False,
        }

        entry = LeagueEntry.from_api_response(api_data)

        # 60 wins out of 100 total games = 60% win rate
        assert entry.win_rate == 60.0

    def test_league_entry_win_rate_no_games(self) -> None:
        """Test LeagueEntry win rate with no games played."""
        api_data = {
            "leagueId": "test-league-id",
            "puuid": "test-puuid",
            "queueType": "RANKED_SOLO_5x5",
            "tier": "IRON",
            "rank": "IV",
            "leaguePoints": 0,
            "wins": 0,
            "losses": 0,
            "hotStreak": False,
            "veteran": False,
            "freshBlood": False,
            "inactive": False,
        }

        entry = LeagueEntry.from_api_response(api_data)

        # No games played should return 0% win rate
        assert entry.win_rate == 0.0

    def test_league_entry_total_games(self) -> None:
        """Test LeagueEntry total games calculation."""
        api_data = {
            "leagueId": "test-league-id",
            "puuid": "test-puuid",
            "queueType": "RANKED_SOLO_5x5",
            "tier": "PLATINUM",
            "rank": "I",
            "leaguePoints": 75,
            "wins": 45,
            "losses": 35,
            "hotStreak": True,
            "veteran": False,
            "freshBlood": False,
            "inactive": False,
        }

        entry = LeagueEntry.from_api_response(api_data)

        # 45 wins + 35 losses = 80 total games
        assert entry.total_games == 80
        # And verify win rate still works
        assert entry.win_rate == 56.25  # 45/80 * 100
