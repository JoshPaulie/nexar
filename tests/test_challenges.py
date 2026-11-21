"""Tests for the challenge system API (lol-challenges-v1).

Distinct from the match payload's per-match ``Challenges`` stats model —
everything here is the account-wide challenge system. Offline rows pin the
exact URLs (per-platform routing) and the recorded live shapes; the live
canary walks all six ops on one region behind a single account lookup.
"""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import pytest
import pytest_asyncio

from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import ChallengeLevel, Region
from nexar.models import (
    ChallengeConfig,
    ChallengeLeaderboardEntry,
    ChallengePoints,
    ChallengePreferences,
    ChallengeProgress,
    LocalizedChallengeNames,
    PlayerChallengeData,
)
from tests.helpers import register_exact_url

if TYPE_CHECKING:
    from aioresponses import aioresponses

# Recorded from the live wire, 2026-11-21 NA1. Challenge 0 is CRYSTAL; 302101
# is "Level 1 Fiesta". Locales are trimmed to the ones asserted; thresholds,
# percentiles, and leaderboard rows are verbatim.
_CONFIG_0 = {
    "id": 0,
    "localizedNames": {
        "en_US": {"description": "", "name": "CRYSTAL", "shortDescription": "Special rules for Crystal"},
        "de_DE": {"description": "", "name": "KRISTALL", "shortDescription": "Sonderregeln für „Kristall“"},
    },
    "state": "ENABLED",
    "leaderboard": True,
    "thresholds": {
        "CHALLENGER": 26500.0,
        "GOLD": 4300.0,
        "DIAMOND": 13800.0,
        "GRANDMASTER": 25000.0,
        "IRON": 0.0,
        "SILVER": 1650.0,
        "BRONZE": 750.0,
        "PLATINUM": 8600.0,
        "MASTER": 24500.0,
    },
}

_CONFIG_302101 = {
    "id": 302101,
    "localizedNames": {
        "en_US": {
            "description": "Get takedowns on enemy champions before jungle camps spawn (1:30)",
            "name": "Level 1 Fiesta",
            "shortDescription": "Get takedowns before jungle camps spawn",
        },
    },
    "state": "ENABLED",
    "leaderboard": True,
    "thresholds": {
        "DIAMOND": 75.0,
        "GRANDMASTER": 200.0,
        "SILVER": 7.0,
        "BRONZE": 3.0,
        "MASTER": 130.0,
        "PLATINUM": 35.0,
        "CHALLENGER": 300.0,
        "GOLD": 15.0,
        "IRON": 1.0,
    },
}

_PERCENTILES_0 = {
    "BRONZE": 0.307,
    "CHALLENGER": 0.0,
    "GRANDMASTER": 0.0,
    "DIAMOND": 0.022,
    "MASTER": 0.0,
    "NONE": 1.0,
    "PLATINUM": 0.061,
    "GOLD": 0.127,
    "SILVER": 0.228,
    "IRON": 0.988,
}

_PERCENTILES_302101 = {
    "BRONZE": 0.195,
    "DIAMOND": 0.038,
    "SILVER": 0.148,
    "GOLD": 0.109,
    "GRANDMASTER": 0.005,
    "PLATINUM": 0.07,
    "CHALLENGER": 0.001,
    "IRON": 0.263,
    "MASTER": 0.02,
}

_LEADERBOARD_MASTER: list[dict[str, Any]] = [
    {
        "position": 58,
        "puuid": "ykg7hEYDSa4GL77CAy8Op0ux5qfGkOO0-CLL-O6Kd6PGL3Dm0aTkvT_R6kTnlcGaeNKXUSXhw7KNPw",
        "value": 27175,
    },
    {
        "position": 59,
        "puuid": "HWXyyr542DQQemClponub-ehSEXtcEoujH61AjgJA6m-cC5R5NBvXex6dJDQkJDsSDMtrNxKxcHvng",
        "value": 27160,
    },
    {
        "position": 60,
        "puuid": "gzB1pm04l5RNLpdDO4CzbkqduDBcH7r68d8DqvX5t7CiajcaXJos7ZWhN37y_ggCB89_VcIJTy8kkw",
        "value": 27145,
    },
]


def configs_payload() -> list[dict[str, Any]]:
    """All-configs response in the recorded live shape, trimmed to two rows."""
    return [_CONFIG_0, _CONFIG_302101]


def expected_config(config_payload: dict[str, Any]) -> ChallengeConfig:
    """The model the client must parse a config row into."""
    end_ms = config_payload.get("endTimestamp")
    return ChallengeConfig(
        id=config_payload["id"],
        localized_names={
            locale: LocalizedChallengeNames(
                name=names["name"],
                description=names.get("description", ""),
                short_description=names.get("shortDescription", ""),
            )
            for locale, names in config_payload["localizedNames"].items()
        },
        state=config_payload["state"],
        leaderboard=config_payload["leaderboard"],
        thresholds=config_payload["thresholds"],
        end_timestamp=datetime.fromtimestamp(end_ms / 1000, tz=UTC) if end_ms else None,
    )


@pytest_asyncio.fixture
async def fresh_client() -> AsyncGenerator[NexarClient]:
    """Client with no conftest catch-alls, so the exact-URL registration is the only match."""
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
    yield client
    await client.close()


class TestChallengeClientOps:
    """The six ops against exact-URL registrations (routing and path pinning).

    Every URL is the per-platform host na1.api.riotgames.com — the regional
    hosts answer 403 for this family (measured 2026-11-21), so a registration
    under americas/europe/asia would never match.
    """

    async def test_get_all_challenge_configs(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/challenges/v1/challenges/config",
            configs_payload(),
        )

        configs = await fresh_client.get_all_challenge_configs()

        assert configs == [expected_config(_CONFIG_0), expected_config(_CONFIG_302101)]

    async def test_get_challenge_config(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/challenges/v1/challenges/0/config",
            _CONFIG_0,
        )

        config = await fresh_client.get_challenge_config(0)

        assert config == expected_config(_CONFIG_0)
        assert config.localized_names["en_US"].name == "CRYSTAL"

    async def test_get_all_challenge_percentiles(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/challenges/v1/challenges/percentiles",
            {"0": _PERCENTILES_0, "302101": _PERCENTILES_302101},
        )

        percentiles = await fresh_client.get_all_challenge_percentiles()

        assert percentiles == {"0": _PERCENTILES_0, "302101": _PERCENTILES_302101}

    async def test_get_challenge_percentiles(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/challenges/v1/challenges/302101/percentiles",
            _PERCENTILES_302101,
        )

        percentiles = await fresh_client.get_challenge_percentiles(302101)

        assert percentiles == _PERCENTILES_302101

    async def test_get_challenge_leaderboard(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/challenges/v1/challenges/0/leaderboards/by-level/MASTER",
            _LEADERBOARD_MASTER,
        )

        entries = await fresh_client.get_challenge_leaderboard(0, ChallengeLevel.MASTER)

        assert entries == [
            ChallengeLeaderboardEntry(puuid=row["puuid"], value=row["value"], position=row["position"])
            for row in _LEADERBOARD_MASTER
        ]

    async def test_get_challenge_leaderboard_limit_is_sent(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/challenges/v1/challenges/0/leaderboards/by-level/GRANDMASTER?limit=3",
            _LEADERBOARD_MASTER[:3],
        )

        entries = await fresh_client.get_challenge_leaderboard(0, "GRANDMASTER", Region.NA1, limit=3)

        assert len(entries) == 3

    async def test_get_challenge_leaderboard_raw_string_level_passes_through(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """A raw string level is not enum-validated — Riot's own 400 is the backstop."""
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/challenges/v1/challenges/0/leaderboards/by-level/GOLD",
            [],
        )

        entries = await fresh_client.get_challenge_leaderboard(0, "GOLD")

        assert entries == []

    async def test_get_challenge_leaderboard_rejects_non_apex_enum_level(self, fresh_client: NexarClient) -> None:
        """The other ten ChallengeLevel values buy a 400 on this path (measured).

        An enum input therefore fails before any wire call.
        """
        with pytest.raises(ValueError, match="MASTER, GRANDMASTER or CHALLENGER"):
            await fresh_client.get_challenge_leaderboard(0, ChallengeLevel.GOLD)

        with pytest.raises(ValueError, match="MASTER, GRANDMASTER or CHALLENGER"):
            await fresh_client.get_challenge_leaderboard(0, ChallengeLevel.NONE)

    async def test_get_challenge_leaderboard_rejects_non_positive_limit(self, fresh_client: NexarClient) -> None:
        with pytest.raises(ValueError, match="limit must be positive"):
            await fresh_client.get_challenge_leaderboard(0, ChallengeLevel.MASTER, limit=0)

    async def test_get_player_challenge_data(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
        mock_responses: dict[str, Any],
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/challenges/v1/player-data/0wKS4sQQTcA6mAmu",
            mock_responses["challenge_player_data"],
        )

        data = await fresh_client.get_player_challenge_data("0wKS4sQQTcA6mAmu")

        assert data.total_points == ChallengePoints(level="DIAMOND", current=15165, max=29680, percentile=0.022)
        assert set(data.category_points) == {"IMAGINATION", "COLLECTION"}
        assert data.category_points["COLLECTION"].percentile == 0.108
        assert data.preferences == ChallengePreferences(
            banner_accent="1",
            title="40220104",
            challenge_ids=(402409, 203404, 402201),
            crest_border="1",
            prestige_crest_border_level=225,
        )


class TestChallengeModels:
    """Challenge model parsing, including the omission-hardening rules."""

    def test_config_strips_to_identity(self) -> None:
        """Riot omits empty values: an id-only row parses with defaults."""
        config = ChallengeConfig.from_api_response({"id": 7})

        assert config == ChallengeConfig(
            id=7, localized_names={}, state="", leaderboard=False, thresholds={}, end_timestamp=None
        )

    def test_config_explicit_nulls_parse_empty(self) -> None:
        """A null must parse like an omitted key — dict(None) would raise."""
        config = ChallengeConfig.from_api_response(
            {"id": 7, "localizedNames": None, "thresholds": None, "endTimestamp": None}
        )

        assert config.localized_names == {}
        assert config.thresholds == {}
        assert config.end_timestamp is None

    def test_config_parses_the_one_timed_entry(self) -> None:
        """Challenge 600012 is the only catalog entry carrying endTimestamp.

        Measured 2026-11-21: 404/405 rows send the plain five keys, 600012
        ("Challenges are Here!") adds endTimestamp — the review pass surfaced
        it after the model claimed timestamps never appear. The timestamp is
        epoch milliseconds, same as every other Riot timestamp.
        """
        timed = ChallengeConfig.from_api_response({"id": 600012, "endTimestamp": 1666234800000})

        assert timed.end_timestamp == datetime.fromtimestamp(1666234800000 / 1000, tz=UTC)

        open_ended = ChallengeConfig.from_api_response({"id": 0})
        assert open_ended.end_timestamp is None

    def test_progress_parses_all_three_wire_shapes(self) -> None:
        """The wire sends three key shapes (measured).

        Fully placed rows, progressed rows, and untouched rows each carry a
        different key set; all three must parse.
        """
        placed = ChallengeProgress.from_api_response(
            {
                "challengeId": 302101,
                "percentile": 0.003,
                "position": 73196,
                "playersInLevel": 109586,
                "level": "GRANDMASTER",
                "value": 295.0,
                "achievedTime": 1737630019432,
            }
        )
        progressed = ChallengeProgress.from_api_response(
            {
                "challengeId": 0,
                "percentile": 0.022,
                "level": "DIAMOND",
                "value": 15165.0,
                "achievedTime": 1761351539269,
            }
        )
        untouched = ChallengeProgress.from_api_response(
            {"challengeId": 303204, "percentile": 1.0, "level": "NONE", "value": 1.0}
        )

        assert placed.achieved_time == datetime.fromtimestamp(1737630019432 / 1000, tz=UTC)
        assert placed.position == 73196
        assert placed.players_in_level == 109586

        assert progressed.achieved_time == datetime.fromtimestamp(1761351539269 / 1000, tz=UTC)
        assert progressed.position == 0
        assert progressed.players_in_level == 0

        assert untouched.achieved_time is None
        assert untouched.level == "NONE"

    def test_progress_stripped_row_defaults(self) -> None:
        progress = ChallengeProgress.from_api_response({"challengeId": 1})

        assert progress == ChallengeProgress(
            challenge_id=1,
            percentile=0.0,
            level="NONE",
            value=0.0,
            achieved_time=None,
            players_in_level=0,
            position=0,
        )

    def test_challenge_points_reads_the_wire_percentile_key(self) -> None:
        """The wire spells it 'percentile' (measured 2026-11-21).

        The reference DTO table's 'precentile' is a documentation typo, so
        that spelling is not read.
        """
        points = ChallengePoints.from_api_response(
            {"level": "DIAMOND", "current": 15165, "max": 29680, "percentile": 0.022}
        )

        assert points.percentile == 0.022
        assert points == ChallengePoints(level="DIAMOND", current=15165, max=29680, percentile=0.022)

    def test_player_data_stripped_parses_empty(self) -> None:
        data = PlayerChallengeData.from_api_response({})

        assert data == PlayerChallengeData(challenges=(), preferences=None, total_points=None, category_points={})

    def test_player_data_null_containers_parse_empty(self) -> None:
        data = PlayerChallengeData.from_api_response(
            {"challenges": None, "categoryPoints": None, "preferences": None, "totalPoints": None}
        )

        assert data.challenges == ()
        assert data.category_points == {}

    def test_leaderboard_entry_defaults(self) -> None:
        entry = ChallengeLeaderboardEntry.from_api_response({"puuid": "p1"})

        assert entry == ChallengeLeaderboardEntry(puuid="p1", value=0.0, position=0)

    def test_level_enum_covers_the_reference_legal_set(self) -> None:
        """All thirteen values the reference op block lists for Level."""
        assert len(ChallengeLevel) == 13
        assert ChallengeLevel("HIGHEST_NOT_LEADERBOARD_ONLY") is ChallengeLevel.HIGHEST_NOT_LEADERBOARD_ONLY
        assert ChallengeLevel.NONE.value == "NONE"


class TestPlayerChallengeSeam:
    """Player.get_challenge_data rides the conftest player-data catch-all."""

    async def test_seam_lazy_caches_and_refresh_clears(self, client: NexarClient) -> None:
        player = await client.get_player(game_name="bexli", tag_line="bex")

        data = await player.get_challenge_data()
        assert isinstance(data, PlayerChallengeData)
        assert len(data.challenges) == 3
        assert data.challenges[0].challenge_id == 302101

        # Lazy: the same object comes back, not a refetch.
        assert await player.get_challenge_data() is data

        player.refresh_cache()
        refetched = await player.get_challenge_data()
        assert refetched == data
        assert refetched is not data


class TestLiveChallengesCanary:
    """Live canary: all six ops plus the limit param, one region, one account lookup."""

    @pytest.mark.slow
    async def test_live_challenge_roundtrip(self, real_client: "NexarClient") -> None:
        player = await real_client.get_player(game_name="bexli", tag_line="bex")

        configs = await real_client.get_all_challenge_configs()
        assert configs, "the challenge catalog is non-empty"
        states = {config.state for config in configs}
        assert states <= {"DISABLED", "HIDDEN", "ENABLED", "ARCHIVED"}
        assert any(config.leaderboard for config in configs), "some challenges have leaderboards"

        single = await real_client.get_challenge_config(0)
        by_id = {config.id: config for config in configs}
        assert single.id == 0
        # The by-id call is a second, later snapshot of a moving catalog, so
        # agreement stops at stable structure: identity, state, and the set of
        # threshold levels. Full threshold-value equality is drift-exposed —
        # the one uncaptured canary failure in the 2026-11-21 live suite run
        # can only have come from the two cross-snapshot comparisons below,
        # and the two clean reruns cleared every within-snapshot assertion.
        assert single.state == by_id[0].state
        assert single.thresholds.keys() == by_id[0].thresholds.keys()
        # The one timed catalog entry (measured 2026-11-21): the launch-window
        # challenge the catalog still serves with an endTimestamp.
        assert by_id[600012].end_timestamp is not None

        all_percentiles = await real_client.get_all_challenge_percentiles()
        assert all_percentiles, "percentile maps are non-empty"
        assert all(isinstance(value, float) for m in all_percentiles.values() for value in m.values())

        one_percentiles = await real_client.get_challenge_percentiles(0)
        assert "NONE" in one_percentiles, "the no-progress share is a key (measured 2026-11-21)"
        assert all(0.0 <= value <= 1.0 for value in one_percentiles.values())

        board = await real_client.get_challenge_leaderboard(0, ChallengeLevel.MASTER)
        assert board, "the CRYSTAL MASTER board is non-empty (138 rows at recording)"
        positions = [entry.position for entry in board]
        assert positions == sorted(positions), "entries arrive sorted by position (measured)"
        assert all(position >= 1 for position in positions)
        # Same drift class as the threshold check above: the board is its own
        # snapshot, so only the top of the ladder is compared against the
        # entry bar — every row below the bar is a recalibration heartbeat
        # away from a false red.
        master_threshold = single.thresholds.get("MASTER", 0.0)
        assert max(entry.value for entry in board) >= master_threshold, (
            "the top of the MASTER board sits at or above the MASTER threshold"
        )

        limited = await real_client.get_challenge_leaderboard(0, ChallengeLevel.MASTER, limit=3)
        assert len(limited) <= 3, "the limit param truncates (measured)"

        data = await player.get_challenge_data()
        assert data.challenges, "the player has progressed challenges"
        assert data.total_points is not None
        assert data.category_points, "category point blocks are present"
        assert all(0.0 <= row.percentile <= 1.0 for row in data.challenges)
        for row in data.challenges:
            if row.achieved_time is not None:
                assert row.achieved_time.tzinfo is not None

        # The seam is lazy on the live path too: no refetch behind this call.
        assert await player.get_challenge_data() is data

        stats = real_client.get_api_call_stats()
        assert stats.retries == 0, "the canary ran clean — no 429s"
        assert stats.fresh_calls == 8, (
            "budget: account + six ops + the limit variant, every op fresh under NO_CACHE_CONFIG"
        )
