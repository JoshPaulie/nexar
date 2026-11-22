"""Tests for league-related functionality."""

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from nexar import LeagueEntry, LeagueItem, LeagueList, MiniSeries
from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Queue, RankDivision, RankTier, Region
from tests.helpers import register_exact_url

if TYPE_CHECKING:
    from aioresponses import aioresponses


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


class TestLeagueEntryStr:
    """__str__ prints the compact rank; its edge forms follow the wire shapes."""

    def test_str_prints_tier_division_and_lp(self) -> None:
        entry = LeagueEntry.from_api_response(
            payload(tier="GOLD", rank="IV", leaguePoints=27, wins=30, losses=20),
        )

        assert str(entry) == "Gold IV 27LP"

    def test_str_apex_entry_omits_the_empty_division(self) -> None:
        """Master+ entries carry RankDivision.EMPTY: no division in the output."""
        apex = LeagueEntry.from_api_response(
            payload(tier="MASTER", leaguePoints=512, wins=120, losses=90),
        )

        assert str(apex) == "Master 512LP"

    def test_str_decayed_entry_omits_rank_and_zero_lp(self) -> None:
        """The decayed wire shape sends an empty rank string and omits LP."""
        decayed = LeagueEntry.from_api_response(
            payload(tier="MASTER", rank="", leaguePoints=0),
        )

        assert str(decayed) == "Master 0LP"

    def test_unranked_queue_is_an_absent_entry_not_a_tier(self) -> None:
        """There is no unranked form to print, by fixture shape.

        The by-puuid wire sends entries only for queues the player is ranked
        in (no UNRANKED tier exists on it, and RankTier deliberately carries
        no such member), so an unranked player has no solo row at all:
        Player.get_solo_rank scans the entries, finds none, and returns
        None, and the caller prints its own unranked label.
        """
        assert "UNRANKED" not in {tier.value for tier in RankTier}


def apex_league_payload(tier: str = "CHALLENGER", queue: str = "RANKED_SOLO_5x5") -> dict[str, object]:
    """Apex league list in the recorded live shape (2026-11-21 NA1 challenger).

    The live container carries only tier/queue/entries — leagueId and name are
    measured absent on every apex queue — and entries are puuid-keyed with no
    summoner-era fields and no queueType (the queue lives on the container).
    """
    return {
        "tier": tier,
        "queue": queue,
        "entries": [
            {
                "puuid": "apex-puuid-1",
                "rank": "I",
                "leaguePoints": 4417,
                "wins": 610,
                "losses": 390,
                "veteran": True,
                "inactive": False,
                "freshBlood": False,
                "hotStreak": True,
            },
            # Riot omits zero/false values: a stripped entry parses via defaults.
            {"puuid": "apex-puuid-2", "wins": 1},
        ],
    }


def ladder_entries_payload(
    queue: str = "RANKED_SOLO_5x5",
    tier: str = "GOLD",
    rank: str = "I",
) -> list[dict[str, object]]:
    """Division ladder page in the recorded live shape: no leagueId, no summoner-era fields."""
    return [
        {
            "queueType": queue,
            "tier": tier,
            "rank": rank,
            "puuid": "ladder-puuid-1",
            "leaguePoints": 40,
            "wins": 10,
            "losses": 13,
            "veteran": False,
            "inactive": False,
            "freshBlood": False,
            "hotStreak": False,
        },
    ]


@pytest_asyncio.fixture
async def fresh_client() -> AsyncGenerator[NexarClient]:
    """Client with no conftest catch-alls, so exact-URL registrations are the only matches."""
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
    yield client
    await client.close()


class TestApexLeagueModels:
    """Apex league-list and league-item parsing."""

    def test_league_list_parses_recorded_container(self) -> None:
        """The recorded NA challenger container, field for field."""
        league = LeagueList.from_api_response(apex_league_payload())

        assert league == LeagueList(
            league_id="",
            tier=RankTier.CHALLENGER,
            name="",
            queue=Queue.RANKED_SOLO_5x5,
            queue_raw="RANKED_SOLO_5x5",
            entries=(
                LeagueItem(
                    puuid="apex-puuid-1",
                    division=RankDivision.ONE,
                    league_points=4417,
                    wins=610,
                    losses=390,
                    hot_streak=True,
                    veteran=True,
                    fresh_blood=False,
                    inactive=False,
                    mini_series=None,
                ),
                LeagueItem(
                    puuid="apex-puuid-2",
                    division=RankDivision.EMPTY,
                    league_points=0,
                    wins=1,
                    losses=0,
                    hot_streak=False,
                    veteran=False,
                    fresh_blood=False,
                    inactive=False,
                    mini_series=None,
                ),
            ),
        )

    def test_league_list_unknown_queue_degrades_to_unknown(self) -> None:
        """A queue string Riot added maps to the UNKNOWN sentinel, raw preserved."""
        league = LeagueList.from_api_response(apex_league_payload() | {"queue": "RANKED_NEW_THING"})

        assert league.queue is Queue.UNKNOWN
        assert league.queue_raw == "RANKED_NEW_THING"

    def test_league_item_unknown_rank_degrades_to_empty(self) -> None:
        item = LeagueItem.from_api_response({"puuid": "p", "rank": "VI"})

        assert item.division is RankDivision.EMPTY

    def test_league_item_parses_a_mini_series_value(self) -> None:
        """The DTO declares miniSeries even though live apex entries never carry it."""
        item = LeagueItem.from_api_response(
            {"puuid": "p", "miniSeries": {"losses": 1, "progress": "WLN", "target": 3, "wins": 1}},
        )

        assert item.mini_series == MiniSeries(losses=1, progress="WLN", target=3, wins=1)

    def test_league_list_explicit_null_entries_parse_empty(self) -> None:
        """A null entries array must parse like an omitted one — tuple(None) would raise."""
        league = LeagueList.from_api_response({"tier": "CHALLENGER", "entries": None})

        assert league.entries == ()
        assert league.tier is RankTier.CHALLENGER

    def test_unknown_tier_raises_by_design(self) -> None:
        """Tier is a direct identity read: an unknown string fails loudly, not silently.

        Unknown queue strings degrade to Queue.UNKNOWN (pinned above); an
        unknown tier would mean Riot invented a tier the enum does not know,
        which should surface rather than half-parse a ladder.
        """
        with pytest.raises(ValueError, match="UNMAPPED"):
            LeagueList.from_api_response({"tier": "UNMAPPED"})


class TestApexLeagueClient:
    """Apex by-queue ops against exact-URL registrations (routing and path pinning)."""

    @pytest.mark.parametrize(
        ("method_name", "path_segment", "expected_tier"),
        [
            ("get_challenger_league", "challengerleagues", RankTier.CHALLENGER),
            ("get_grandmaster_league", "grandmasterleagues", RankTier.GRANDMASTER),
            ("get_master_league", "masterleagues", RankTier.MASTER),
        ],
    )
    async def test_apex_ladder_methods_hit_their_exact_paths(
        self,
        method_name: str,
        path_segment: str,
        expected_tier: RankTier,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """Each apex method routes its own league-v4 path on the platform host."""
        register_exact_url(
            mock_aioresponse,
            f"https://na1.api.riotgames.com/lol/league/v4/{path_segment}/by-queue/RANKED_SOLO_5x5",
            apex_league_payload(expected_tier.value),
        )

        league = await getattr(fresh_client, method_name)(Queue.RANKED_SOLO_5x5)

        assert league.tier is expected_tier
        assert league.queue is Queue.RANKED_SOLO_5x5
        assert len(league.entries) == 2

    async def test_flex_queue_spells_the_path_string(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """The Queue enum's numeric value (440) must not leak into the path."""
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_FLEX_SR",
            apex_league_payload(queue="RANKED_FLEX_SR"),
        )

        league = await fresh_client.get_challenger_league(Queue.RANKED_FLEX_SR)

        assert league.queue is Queue.RANKED_FLEX_SR
        assert league.queue_raw == "RANKED_FLEX_SR"

    async def test_non_ranked_queue_raises_before_any_request(self, fresh_client: NexarClient) -> None:
        with pytest.raises(ValueError, match="ranked ladder queue"):
            await fresh_client.get_challenger_league(Queue.ARAM)


class TestDivisionLadderClient:
    """Division entries ops against exact-URL registrations (routing, path, and page wiring)."""

    async def test_get_league_entries_default_page_sends_no_query(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """Page 1 is the reference default, so the wire call carries no query string."""
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/GOLD/I",
            ladder_entries_payload(),
        )

        entries = await fresh_client.get_league_entries(Queue.RANKED_SOLO_5x5, RankTier.GOLD, RankDivision.ONE)

        assert entries == [
            LeagueEntry(
                league_id="",
                puuid="ladder-puuid-1",
                queue_type=Queue.RANKED_SOLO_5x5,
                queue_type_raw="RANKED_SOLO_5x5",
                tier=RankTier.GOLD,
                division=RankDivision.ONE,
                league_points=40,
                wins=10,
                losses=13,
                hot_streak=False,
                veteran=False,
                fresh_blood=False,
                inactive=False,
                mini_series=None,
            ),
        ]

    async def test_get_league_entries_page_lands_in_the_query_string(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/GOLD/I?page=2",
            ladder_entries_payload(),
        )

        entries = await fresh_client.get_league_entries(
            Queue.RANKED_SOLO_5x5,
            RankTier.GOLD,
            RankDivision.ONE,
            page=2,
        )

        assert len(entries) == 1

    async def test_get_league_exp_entries_hits_the_expanded_league_route(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """league-exp-v4 serves its own route and parses with the same by-puuid model."""
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/league-exp/v4/entries/RANKED_FLEX_SR/SILVER/II?page=3",
            ladder_entries_payload(queue="RANKED_FLEX_SR", tier="SILVER", rank="II"),
        )

        entries = await fresh_client.get_league_exp_entries(
            Queue.RANKED_FLEX_SR,
            RankTier.SILVER,
            RankDivision.TWO,
            page=3,
        )

        assert entries[0].queue_type is Queue.RANKED_FLEX_SR
        assert entries[0].tier is RankTier.SILVER
        assert entries[0].division is RankDivision.TWO

    async def test_division_ladder_region_override_routes_the_platform_host(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://euw1.api.riotgames.com/lol/league/v4/entries/RANKED_SOLO_5x5/IRON/IV",
            ladder_entries_payload(tier="IRON", rank="IV"),
        )

        entries = await fresh_client.get_league_entries(
            Queue.RANKED_SOLO_5x5,
            RankTier.IRON,
            RankDivision.FOUR,
            Region.EUW1,
        )

        assert entries[0].tier is RankTier.IRON


class TestLadderValidation:
    """Path values the division ladders do not serve raise before any wire call."""

    @pytest.mark.parametrize(
        "tier",
        [RankTier.MASTER, RankTier.GRANDMASTER, RankTier.CHALLENGER],
        ids=["master", "grandmaster", "challenger"],
    )
    async def test_apex_tier_raises(self, tier: RankTier, fresh_client: NexarClient) -> None:
        with pytest.raises(ValueError, match="division tier"):
            await fresh_client.get_league_entries(Queue.RANKED_SOLO_5x5, tier, RankDivision.ONE)

    async def test_empty_division_raises(self, fresh_client: NexarClient) -> None:
        with pytest.raises(ValueError, match="real division"):
            await fresh_client.get_league_entries(Queue.RANKED_SOLO_5x5, RankTier.GOLD, RankDivision.EMPTY)

    async def test_page_zero_raises(self, fresh_client: NexarClient) -> None:
        with pytest.raises(ValueError, match="page must be 1 or greater"):
            await fresh_client.get_league_entries(Queue.RANKED_SOLO_5x5, RankTier.GOLD, RankDivision.ONE, page=0)

    async def test_non_ranked_queue_raises_on_the_division_ladder(self, fresh_client: NexarClient) -> None:
        with pytest.raises(ValueError, match="ranked ladder queue"):
            await fresh_client.get_league_exp_entries(Queue.CUSTOM, RankTier.GOLD, RankDivision.ONE)


class TestLiveLadderCanaries:
    """Live canaries: the five ladder ops against the real API (one region)."""

    @pytest.mark.slow
    async def test_live_apex_ladders_return_sorted_ladders(self, real_client: NexarClient) -> None:
        challenger = await real_client.get_challenger_league(Queue.RANKED_SOLO_5x5)
        assert challenger.tier is RankTier.CHALLENGER
        assert 0 < len(challenger.entries) <= 300

        grandmaster = await real_client.get_grandmaster_league(Queue.RANKED_SOLO_5x5)
        assert grandmaster.tier is RankTier.GRANDMASTER
        assert 0 < len(grandmaster.entries) <= 700

        master = await real_client.get_master_league(Queue.RANKED_SOLO_5x5)
        assert master.tier is RankTier.MASTER
        assert master.entries

        # All three apex docstrings claim pre-sorted entries — pin each ladder.
        for league in (challenger, grandmaster, master):
            points = [entry.league_points for entry in league.entries]
            assert points == sorted(points, reverse=True)

    @pytest.mark.slow
    async def test_live_division_pages_paginate(self, real_client: NexarClient) -> None:
        """Division pages are unordered on the wire (measured), so pin size and disjointness, not order."""
        page_one = await real_client.get_league_entries(Queue.RANKED_SOLO_5x5, RankTier.GOLD, RankDivision.ONE)
        assert len(page_one) == 205  # page size measured from the live wire
        assert {entry.tier for entry in page_one} == {RankTier.GOLD}
        assert {entry.division for entry in page_one} == {RankDivision.ONE}

        page_two = await real_client.get_league_entries(
            Queue.RANKED_SOLO_5x5,
            RankTier.GOLD,
            RankDivision.ONE,
            page=2,
        )
        assert 0 < len(page_two) <= 205
        assert {entry.puuid for entry in page_two} != {entry.puuid for entry in page_one}

        exp_page = await real_client.get_league_exp_entries(Queue.RANKED_SOLO_5x5, RankTier.GOLD, RankDivision.ONE)
        # Exact page size is pinned once, on the league-v4 page above; the exp
        # row only needs to prove the same op shape, not re-pin Riot's constant.
        assert 0 < len(exp_page) <= 205
