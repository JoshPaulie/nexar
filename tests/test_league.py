"""Tests for league-related functionality."""

from typing import TYPE_CHECKING

import pytest

from nexar import LeagueEntry, MiniSeries
from nexar.enums import Queue, RankDivision, RankTier

if TYPE_CHECKING:
    from nexar.client import NexarClient


def payload(**overrides: object) -> dict[str, object]:
    """A recorded-shape league entry payload (Riot omits empty values)."""
    data: dict[str, object] = {
        "leagueId": "test-league-id",
        "puuid": "test-puuid",
        "queueType": "RANKED_SOLO_5x5",
        "hotStreak": False,
        "veteran": True,
        "freshBlood": False,
        "inactive": False,
    }
    data.update(overrides)
    return data


class TestLeagueEntries:
    """Test league entry functionality."""

    async def test_get_league_entries_by_puuid_returns_recorded_entry(self, client: "NexarClient") -> None:
        """The recorded by-puuid entries payload parses to its exact entry."""
        test_puuid = "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA"

        result = await client.get_league_entries_by_puuid(test_puuid, None)

        assert result == [
            LeagueEntry(
                league_id="73c68388-3721-3944-b054-d92e5959954d",
                puuid=test_puuid,
                queue_type=Queue.RANKED_SOLO_5x5,
                queue_type_raw="RANKED_SOLO_5x5",
                tier=RankTier.SILVER,
                division=RankDivision.FOUR,
                league_points=54,
                wins=53,
                losses=46,
                hot_streak=False,
                veteran=False,
                fresh_blood=False,
                inactive=False,
                mini_series=None,
            ),
        ]


class TestLeagueModels:
    """Test league model parsing."""

    def test_mini_series_creation(self) -> None:
        """Test MiniSeries model creation from API response."""
        api_data = {"losses": 1, "progress": "WWN", "target": 3, "wins": 2}

        mini_series = MiniSeries.from_api_response(api_data)

        assert mini_series.losses == 1
        assert mini_series.progress == "WWN"
        assert mini_series.target == 3
        assert mini_series.wins == 2

    @pytest.mark.parametrize(
        ("overrides", "expected"),
        [
            (
                {"tier": "GOLD", "rank": "III", "leaguePoints": 75, "wins": 50, "losses": 30},
                LeagueEntry(
                    league_id="test-league-id",
                    puuid="test-puuid",
                    queue_type=Queue.RANKED_SOLO_5x5,
                    queue_type_raw="RANKED_SOLO_5x5",
                    tier=RankTier.GOLD,
                    division=RankDivision.THREE,
                    league_points=75,
                    wins=50,
                    losses=30,
                    hot_streak=False,
                    veteran=True,
                    fresh_blood=False,
                    inactive=False,
                ),
            ),
            (
                {
                    "tier": "SILVER",
                    "rank": "I",
                    "leaguePoints": 85,
                    "wins": 25,
                    "losses": 20,
                    "hotStreak": True,
                    "veteran": False,
                    "freshBlood": True,
                    "miniSeries": {"losses": 0, "progress": "WW", "target": 3, "wins": 2},
                },
                LeagueEntry(
                    league_id="test-league-id",
                    puuid="test-puuid",
                    queue_type=Queue.RANKED_SOLO_5x5,
                    queue_type_raw="RANKED_SOLO_5x5",
                    tier=RankTier.SILVER,
                    division=RankDivision.ONE,
                    league_points=85,
                    wins=25,
                    losses=20,
                    hot_streak=True,
                    veteran=False,
                    fresh_blood=True,
                    inactive=False,
                    mini_series=MiniSeries(losses=0, progress="WW", target=3, wins=2),
                ),
            ),
        ],
        ids=["without-mini-series", "with-mini-series"],
    )
    def test_league_entry_from_payload(self, overrides: dict, expected: LeagueEntry) -> None:
        assert LeagueEntry.from_api_response(payload(**overrides)) == expected

    def test_unknown_queue_type_maps_to_unknown(self) -> None:
        """A queueType string Riot added maps to the UNKNOWN sentinel, raw string preserved."""
        entry = LeagueEntry.from_api_response(
            payload(queueType="RANKED_NEW_THING", tier="GOLD", rank="III"),
        )

        assert entry.queue_type is Queue.UNKNOWN
        assert entry.queue_type_raw == "RANKED_NEW_THING"

    @pytest.mark.parametrize(
        ("overrides", "expected_win_rate", "expected_total_games"),
        [
            (
                {"tier": "GOLD", "rank": "II", "leaguePoints": 50, "wins": 60, "losses": 40, "veteran": False},
                0.6,
                100,
            ),
            (
                {"tier": "IRON", "rank": "IV", "leaguePoints": 0, "wins": 0, "losses": 0, "veteran": False},
                0.0,
                0,
            ),
            (
                {
                    "tier": "PLATINUM",
                    "rank": "I",
                    "leaguePoints": 75,
                    "wins": 45,
                    "losses": 35,
                    "hotStreak": True,
                    "veteran": False,
                },
                0.5625,
                80,
            ),
        ],
        ids=["gold-ii-60-percent", "no-games", "platinum-i"],
    )
    def test_league_entry_derived_values(
        self,
        overrides: dict,
        expected_win_rate: float,
        expected_total_games: int,
    ) -> None:
        entry = LeagueEntry.from_api_response(payload(**overrides))
        assert entry.win_rate == expected_win_rate
        assert entry.total_games == expected_total_games


class TestLeagueEntryOmittedFields:
    """Riot omits empty values from responses, so apex/decayed entries lose fields."""

    def test_apex_entry_without_rank_or_league_points(self) -> None:
        """Master+ entries have no division, and 0 LP is omitted."""
        entry = LeagueEntry.from_api_response(
            payload(tier="MASTER", wins=120, losses=90),
        )

        assert entry.division is RankDivision.EMPTY
        assert entry.league_points == 0
        assert entry.wins == 120
        assert entry.losses == 90
        assert entry.total_games == 210

    def test_decayed_entry_with_empty_rank_string(self) -> None:
        """Decayed/inactive entries can send an empty 'rank' string."""
        entry = LeagueEntry.from_api_response(
            payload(tier="MASTER", rank="", leaguePoints=0),
        )

        assert entry.division is RankDivision.EMPTY
        assert entry.league_points == 0

    def test_live_by_puuid_entry_without_league_id(self) -> None:
        """The live by-puuid entries endpoint no longer returns leagueId (verified 2026-11-18)."""
        entry = LeagueEntry.from_api_response(
            {
                "freshBlood": False,
                "hotStreak": False,
                "inactive": False,
                "leaguePoints": 0,
                "losses": 20,
                "puuid": "test-puuid",
                "queueType": "RANKED_SOLO_5x5",
                "rank": "IV",
                "tier": "GOLD",
                "veteran": False,
                "wins": 30,
            },
        )

        assert entry.league_id == ""
        assert entry.tier is RankTier.GOLD
        assert entry.league_points == 0

    def test_entry_with_every_omitted_integer(self) -> None:
        """Zero wins/losses/LP are all omitted from the payload."""
        entry = LeagueEntry.from_api_response(
            payload(tier="CHALLENGER", rank=""),
        )

        assert entry.division is RankDivision.EMPTY
        assert entry.league_points == 0
        assert entry.wins == 0
        assert entry.losses == 0
        assert entry.win_rate == 0.0

    def test_apex_rank_tuple_handles_empty_division(self) -> None:
        """rank_tuple must not raise on an EMPTY division and must sort apex above Diamond."""
        apex = LeagueEntry.from_api_response(
            payload(tier="MASTER", wins=120, losses=90),
        )
        diamond = LeagueEntry.from_api_response(
            payload(tier="DIAMOND", rank="I", leaguePoints=0, wins=10, losses=10),
        )

        assert apex.rank_tuple[1] == 0
        assert apex.rank_tuple > diamond.rank_tuple
        assert apex.is_higher_rank_than(diamond)

    def test_rank_tuple_scores_unchanged_for_standard_entries(self) -> None:
        """Adding RankDivision.EMPTY must not renumber existing rank scores."""
        diamond = LeagueEntry.from_api_response(
            payload(tier="DIAMOND", rank="I", leaguePoints=0, wins=1, losses=1),
        )

        assert diamond.rank_tuple == (33, 0)

    def test_apex_entries_sort_by_league_points(self) -> None:
        low = LeagueEntry.from_api_response(payload(tier="MASTER", wins=1, losses=1))
        high = LeagueEntry.from_api_response(
            payload(tier="MASTER", leaguePoints=1500, wins=1, losses=1),
        )

        assert low.rank_tuple < high.rank_tuple
        assert sorted([high, low]) == [low, high]
