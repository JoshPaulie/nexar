"""Tests for league-related functionality."""

from nexar import LeagueEntry, MiniSeries


class TestLeagueEntries:
    """Test league entry functionality."""

    def test_get_league_entries_by_puuid_success(self, client):
        """Test successful league entries retrieval by PUUID."""
        # First get a riot account to get a real PUUID
        account = client.get_riot_account("bexli", "bex")

        # Get league entries for the account
        result = client.get_league_entries_by_puuid(account.puuid)

        # Should return a list of league entries
        assert isinstance(result, list)

        # If the account has ranked entries, validate the structure
        if result:
            for entry in result:
                assert isinstance(entry, LeagueEntry)
                assert entry.puuid == account.puuid
                assert entry.league_id is not None
                assert entry.queue_type is not None
                assert entry.tier is not None
                assert entry.rank is not None
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

    def test_mini_series_creation(self):
        """Test MiniSeries model creation from API response."""
        api_data = {"losses": 1, "progress": "WWN", "target": 3, "wins": 2}

        mini_series = MiniSeries.from_api_response(api_data)

        assert mini_series.losses == 1
        assert mini_series.progress == "WWN"
        assert mini_series.target == 3
        assert mini_series.wins == 2

    def test_league_entry_creation_without_mini_series(self):
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
        assert entry.queue_type == "RANKED_SOLO_5x5"
        assert entry.tier == "GOLD"
        assert entry.rank == "III"
        assert entry.league_points == 75
        assert entry.wins == 50
        assert entry.losses == 30
        assert entry.hot_streak is False
        assert entry.veteran is True
        assert entry.fresh_blood is False
        assert entry.inactive is False
        assert entry.mini_series is None

    def test_league_entry_creation_with_mini_series(self):
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
        assert entry.queue_type == "RANKED_SOLO_5x5"
        assert entry.tier == "SILVER"
        assert entry.rank == "I"
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
