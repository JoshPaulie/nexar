"""Tests for champion-mastery client methods and models."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region
from nexar.exceptions import NotFoundError
from nexar.models.champion_mastery import ChampionMastery, NextSeasonMilestone, RewardConfig
from tests.helpers import champion_mastery_payload, register_exact_url

if TYPE_CHECKING:
    from aioresponses import aioresponses

BASE_URL = "https://na1.api.riotgames.com/lol/champion-mastery/v4"


@pytest_asyncio.fixture
async def fresh_client() -> AsyncGenerator[NexarClient]:
    """Client with no conftest catch-alls, so exact-URL registrations are the only matches."""
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
    yield client
    await client.close()


def expected_mastery() -> ChampionMastery:
    """The ChampionMastery the recorded-shape payload must parse to, field for field."""
    return ChampionMastery(
        puuid="0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA",
        champion_id=7,
        champion_level=7,
        champion_points=127530,
        champion_points_since_last_level=2690,
        champion_points_until_next_level=1470,
        chest_granted=True,
        tokens_earned=0,
        last_play_time=datetime(2024, 12, 25, 7, 40, tzinfo=UTC),
        mark_required_for_next_level=2,
        champion_season_milestone=8,
        milestone_grades=("S", "S-"),
        next_season_milestone=NextSeasonMilestone(
            require_grade_counts={"S-": 1, "S": 2},
            reward_marks=2,
            bonus=False,
            reward_config=RewardConfig(reward_value="MASTERY_CHEST", reward_type="CHEST", maximum_reward=1),
        ),
    )


class TestChampionMasteryClient:
    """Client methods against exact-URL registrations (parameter pinning)."""

    async def test_get_champion_masteries_returns_parsed_list(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            f"{BASE_URL}/champion-masteries/by-puuid/test-puuid",
            [champion_mastery_payload()],
        )

        masteries = await fresh_client.get_champion_masteries("test-puuid")

        assert masteries == [expected_mastery()]

    async def test_get_champion_mastery_by_champion(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            f"{BASE_URL}/champion-masteries/by-puuid/test-puuid/by-champion/7",
            champion_mastery_payload(),
        )

        mastery = await fresh_client.get_champion_mastery("test-puuid", 7)

        assert mastery == expected_mastery()

    async def test_get_champion_mastery_unknown_champion_raises_not_found(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """A champion the player has never played maps to Riot's 404 → NotFoundError."""
        register_exact_url(
            mock_aioresponse,
            f"{BASE_URL}/champion-masteries/by-puuid/test-puuid/by-champion/999",
            {"status": {"message": "No champion data found"}},
            status=404,
        )

        with pytest.raises(NotFoundError):
            await fresh_client.get_champion_mastery("test-puuid", 999)

    async def test_get_top_champion_masteries(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            f"{BASE_URL}/champion-masteries/by-puuid/test-puuid/top",
            [champion_mastery_payload()],
        )

        top = await fresh_client.get_top_champion_masteries("test-puuid")

        assert top == [expected_mastery()]

    async def test_get_top_champion_masteries_with_count(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """The exact-URL pin: a provided count lands in the query string."""
        register_exact_url(
            mock_aioresponse,
            f"{BASE_URL}/champion-masteries/by-puuid/test-puuid/top?count=5",
            [champion_mastery_payload()],
        )

        top = await fresh_client.get_top_champion_masteries("test-puuid", count=5)

        assert top == [expected_mastery()]

    async def test_get_top_champion_masteries_count_must_be_positive(self, fresh_client: NexarClient) -> None:
        with pytest.raises(ValueError, match="count must be positive"):
            await fresh_client.get_top_champion_masteries("test-puuid", count=0)

    async def test_get_champion_mastery_score_returns_int(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/scores/by-puuid/test-puuid", 157331)

        score = await fresh_client.get_champion_mastery_score("test-puuid")

        assert score == 157331


class TestChampionMasteryModels:
    """ChampionMastery parsing, including Riot's omission of empty values."""

    def test_full_payload_parses_every_field(self) -> None:
        assert ChampionMastery.from_api_response(champion_mastery_payload()) == expected_mastery()

    def test_minimal_payload_defaults_omitted_values(self) -> None:
        """Riot omits empty values: a bare entry parses with defaults, not KeyErrors."""
        mastery = ChampionMastery.from_api_response(
            {
                "puuid": "test-puuid",
                "championId": 19,
                "championLevel": 2,
                "championPoints": 3400,
            },
        )

        assert mastery.champion_id == 19
        assert mastery.champion_points_since_last_level == 0
        assert mastery.champion_points_until_next_level == 0
        assert mastery.chest_granted is False
        assert mastery.tokens_earned == 0
        assert mastery.last_play_time == datetime(1970, 1, 1, tzinfo=UTC)
        assert mastery.mark_required_for_next_level == 0
        assert mastery.champion_season_milestone == 0
        assert mastery.milestone_grades == ()
        assert mastery.next_season_milestone is None

    def test_tokens_and_grades_parse_when_present(self) -> None:
        mastery = ChampionMastery.from_api_response(
            champion_mastery_payload(tokensEarned=3, milestoneGrades=["S", "S", "S-"]),
        )

        assert mastery.tokens_earned == 3
        assert mastery.milestone_grades == ("S", "S", "S-")

    def test_next_season_milestone_without_reward_config(self) -> None:
        payload = champion_mastery_payload()
        payload["nextSeasonMilestone"].pop("rewardConfig")

        mastery = ChampionMastery.from_api_response(payload)

        assert mastery.next_season_milestone is not None
        assert mastery.next_season_milestone.reward_config is None


class TestPlayerChampionMasteries:
    """Player.get_champion_masteries lazily fetches and caches (conftest catch-alls)."""

    async def test_player_get_champion_masteries(self, client: "NexarClient") -> None:
        player = await client.get_player(game_name="bexli", tag_line="bex")

        masteries = await player.get_champion_masteries()

        assert masteries[0].champion_id == 106
        assert masteries[0].chest_granted is True
        # Second call is served from the Player cache, not a second fetch.
        assert await player.get_champion_masteries() is masteries

    async def test_player_get_champion_masteries_omitted_defaults(self, client: "NexarClient") -> None:
        """The second conftest fixture entry carries only identity+points (omission shape)."""
        player = await client.get_player(game_name="bexli", tag_line="bex")

        masteries = await player.get_champion_masteries()

        assert masteries[1].champion_id == 22
        assert masteries[1].chest_granted is False
        assert masteries[1].milestone_grades == ()
        assert masteries[1].next_season_milestone is None

    async def test_refresh_cache_clears_masteries(self, client: "NexarClient") -> None:
        player = await client.get_player(game_name="bexli", tag_line="bex")
        masteries = await player.get_champion_masteries()

        player.refresh_cache()

        # Refetched from the (repeat=True) catch-all: equal content, new object.
        assert await player.get_champion_masteries() == masteries
        assert await player.get_champion_masteries() is not masteries


class TestChampionMasteryLive:
    """Live canaries (real Riot API calls; skipped keyless)."""

    @pytest.mark.slow
    async def test_live_champion_mastery_roundtrip(self, real_client: "NexarClient") -> None:
        """Live canary: all four mastery ops return coherent data for a real player."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")

        masteries = await player.get_champion_masteries()
        assert masteries, "account has champion masteries"
        points = [mastery.champion_points for mastery in masteries]
        assert points == sorted(points, reverse=True)

        top = await real_client.get_top_champion_masteries(player.puuid)
        assert top, "account has top masteries"
        assert top[0].champion_id == masteries[0].champion_id

        top_two = await real_client.get_top_champion_masteries(player.puuid, count=2)
        assert len(top_two) <= 2

        single = await real_client.get_champion_mastery(player.puuid, masteries[0].champion_id)
        assert single.champion_id == masteries[0].champion_id
        assert single.champion_points == masteries[0].champion_points

        score = await real_client.get_champion_mastery_score(player.puuid)
        assert isinstance(score, int)
        assert score > 0
