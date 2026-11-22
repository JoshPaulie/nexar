"""Tests for high-level Player functionality."""

import copy
import logging
import re
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any

import pytest
import pytest_asyncio

from nexar import (
    BatchError,
    ChampionStats,
    MatchParticipantPosition,
    MatchType,
    NexarClient,
    NotFoundError,
    PerformanceStats,
    Player,
    Queue,
    Region,
    RiotAccount,
)
from nexar.cache import NO_CACHE_CONFIG
from nexar.models.match_list import MatchList

if TYPE_CHECKING:
    import pytest_mock
    from aioresponses import aioresponses

PUUID = "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA"

_IDS_URL = re.compile(r"https://americas\.api\.riotgames\.com/lol/match/v5/matches/by-puuid/test-puuid/ids.*")
_MATCH_URL = "https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}"


def _register_match(
    mock: "aioresponses",
    mock_responses: dict[str, Any],
    match_id: str,
    *,
    win: bool,
    champion_id: int = 69,
    champion_name: str = "Cassiopeia",
) -> None:
    """Register one match payload whose first participant is the batch player."""
    payload = copy.deepcopy(mock_responses["match"])
    payload["metadata"]["matchId"] = match_id
    target = payload["info"]["participants"][0]
    target["puuid"] = "test-puuid"
    target["win"] = win
    target["championId"] = champion_id
    target["championName"] = champion_name
    mock.get(_MATCH_URL.format(match_id=match_id), payload=payload, repeat=True)


class TestPlayer:
    """Test the Player class against the recorded payloads."""

    async def test_get_player_delegates_to_player_create(
        self,
        client: "NexarClient",
        mocker: "pytest_mock.MockerFixture",
    ) -> None:
        """client.get_player is a thin delegate: it resolves the region and forwards to Player.create."""
        sentinel = Player(
            client=client,
            game_name="bexli",
            tag_line="bex",
            riot_account=RiotAccount(puuid="test-puuid", game_name="bexli", tag_line="bex"),
            region=Region.EUW1,
        )
        create = mocker.patch.object(Player, "create", return_value=sentinel)

        result = await client.get_player(game_name="bexli", tag_line="bex", region=Region.EUW1)

        assert result is sentinel
        create.assert_awaited_once_with(
            client=client,
            game_name="bexli",
            tag_line="bex",
            puuid=None,
            riot_id=None,
            region=Region.EUW1,
        )

    async def test_player_puuid_cross_checks_riot_account(self, client: "NexarClient") -> None:
        """player.puuid is exactly the riot account's puuid, and the summoner fetch agrees."""
        player = await client.get_player(game_name="bexli", tag_line="bex")

        assert player.puuid == player.riot_account.puuid == PUUID

        summoner = await player.get_summoner()
        assert player.puuid == summoner.puuid

    async def test_get_summoner_memoizes(self, client: "NexarClient") -> None:
        """The summoner is fetched once and memoized on the Player."""
        player = await client.get_player(game_name="bexli", tag_line="bex")

        first = await player.get_summoner()
        second = await player.get_summoner()

        assert first is second

    async def test_refresh_cache_forces_wire_refetch(
        self,
        client: "NexarClient",
        mock_aioresponse: "aioresponses",
    ) -> None:
        """After refresh_cache a second get_summoner must hit the wire again."""
        player = await client.get_player(game_name="bexli", tag_line="bex")

        def summoner_wire_hits() -> int:
            return sum(
                len(calls)
                for (method, url), calls in (mock_aioresponse.requests or {}).items()
                if method == "GET" and "summoners/by-puuid" in str(url)
            )

        await player.get_summoner()
        assert summoner_wire_hits() == 1
        await player.get_summoner()
        assert summoner_wire_hits() == 1  # memoized: no second wire hit

        player.refresh_cache()
        await player.get_summoner()
        assert summoner_wire_hits() == 2  # forced refetch

    async def test_player_string_representations(self, client: "NexarClient") -> None:
        """Test string representations of Player."""
        player = await client.get_player(game_name="bexli", tag_line="bex")

        assert str(player) == "bexli#bex"

        repr_repr = repr(player)
        assert "Player" in repr_repr
        assert "bexli" in repr_repr
        assert "bex" in repr_repr

    async def test_player_regions_customization(self, client: "NexarClient") -> None:
        """Test Player with custom regions."""
        player = await Player.create(
            client=client,
            game_name="bexli",
            tag_line="bex",
            region=Region.EUW1,
        )

        assert player.region == Region.EUW1

    async def test_player_with_regions_fallback_to_defaults(
        self,
        client: "NexarClient",
    ) -> None:
        """Test Player falls back to client defaults when no regions specified."""
        player = await Player.create(
            client=client,
            game_name="bexli",
            tag_line="bex",
        )

        assert player.region is None

    async def test_get_last_match_returns_most_recent_fixture_match(self, client: "NexarClient") -> None:
        """get_last_match fetches the first id of the most-recent-first id list."""
        player = await client.get_player(game_name="bexli", tag_line="bex")

        match = await player.get_last_match()

        assert match is not None
        assert match.metadata.match_id == "NA1_5320484860"

    async def test_get_solo_rank_value_matches_fixture_entry(self, client: "NexarClient") -> None:
        """The recorded SILVER IV 54 LP entry parses to its exact sort tuple."""
        player = await client.get_player(game_name="bexli", tag_line="bex")

        assert await player.get_solo_rank_value() == (10, 54)

    async def test_get_solo_rank_value_unranked_is_none(
        self,
        client: "NexarClient",
        mocker: "pytest_mock.MockerFixture",
    ) -> None:
        """No solo-queue entry propagates None instead of raising."""
        player = await client.get_player(game_name="bexli", tag_line="bex")
        mocker.patch.object(player, "get_solo_rank", return_value=None)

        assert await player.get_solo_rank_value() is None

    # --- get_player / Player.create overload tests ---

    async def test_get_player_by_puuid(self, client: "NexarClient") -> None:
        """Test get_player with puuid keyword argument."""
        player = await client.get_player(puuid=PUUID)

        assert player.puuid == player.riot_account.puuid == PUUID

    async def test_get_player_by_riot_id(self, client: "NexarClient") -> None:
        """Test get_player with riot_id keyword argument."""
        player = await client.get_player(riot_id="bexli#bex")

        assert player.game_name == "bexli"
        assert player.tag_line == "bex"
        assert player.puuid is not None

    @pytest.mark.parametrize(
        ("entry", "kwargs", "expected_region"),
        [
            ("get_player", {"puuid": PUUID}, Region.NA1),
            ("get_player", {"puuid": PUUID, "region": Region.EUW1}, Region.EUW1),
            ("create", {"puuid": PUUID}, None),
            ("create", {"riot_id": "bexli#bex"}, None),
        ],
        ids=["get-player-puuid", "get-player-puuid-region", "create-puuid", "create-riot-id"],
    )
    async def test_player_entry_points_resolve_the_same_identity(
        self,
        client: "NexarClient",
        entry: str,
        kwargs: dict[str, Any],
        expected_region: Region | None,
    ) -> None:
        """Both entry points resolve the recorded account; get_player fills in the region."""
        if entry == "get_player":
            player = await client.get_player(**kwargs)
        else:
            player = await Player.create(client=client, **kwargs)

        assert player.game_name == "bexli"
        assert player.tag_line == "bex"
        assert player.puuid == PUUID
        assert player.region == expected_region

    async def test_get_player_no_args_raises(self, client: "NexarClient") -> None:
        """Test that get_player with no identification raises ValueError."""
        with pytest.raises(ValueError, match="Either game_name \\+ tag_line, puuid, or riot_id"):
            await client.get_player()

    async def test_get_player_ambiguous_args_raises(self, client: "NexarClient") -> None:
        """game_name without tag_line is not a valid identification and raises."""
        with pytest.raises(ValueError, match="Either game_name \\+ tag_line, puuid, or riot_id"):
            await client.get_player(game_name="bexli")

    @pytest.mark.parametrize("bad_riot_id", ["no_hash", "#onlytag", "onlyname#"])
    async def test_get_player_by_riot_id_invalid_format(
        self,
        client: "NexarClient",
        bad_riot_id: str,
    ) -> None:
        """Test that get_player with invalid riot_id format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid Riot ID format"):
            await client.get_player(riot_id=bad_riot_id)

    async def test_get_riot_account_by_puuid(self, client: "NexarClient") -> None:
        """Test client.get_riot_account_by_puuid method directly."""
        account_by_name = await client.get_riot_account("bexli", "bex")
        puuid = account_by_name.puuid

        account_by_puuid = await client.get_riot_account_by_puuid(puuid)

        assert account_by_puuid.puuid == puuid
        assert account_by_puuid.game_name == "bexli"
        assert account_by_puuid.tag_line == "bex"

    # --- live canaries (real Riot API calls; skipped keyless) ---

    @pytest.mark.slow
    @pytest.mark.parametrize(
        "filters",
        [
            {"count": 5},
            {"count": 10, "queue": Queue.RANKED_SOLO_5x5},
            {"count": 5, "match_type": MatchType.RANKED},
        ],
        ids=["basic", "queue-filter", "match-type-filter"],
    )
    async def test_player_get_recent_matches(self, real_client: "NexarClient", filters: dict[str, Any]) -> None:
        """Live canary: each filtered get_matches path returns a bounded MatchList."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")

        matches = await player.get_matches(**filters)

        assert isinstance(matches, MatchList)
        assert len(matches) <= filters["count"]

    @pytest.mark.slow
    async def test_player_get_champion_stats(self, real_client: "NexarClient") -> None:
        """Live canary: champion stats keep their internal invariants."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")

        matches = await player.get_matches(count=10)
        stats = matches.get_champion_stats()
        assert isinstance(stats, list)

        for stat in stats:
            assert isinstance(stat, ChampionStats)
            assert stat.champion_id > 0
            assert stat.games_played > 0
            assert stat.wins + stat.losses == stat.games_played
            assert 0 <= stat.win_rate <= 1

    @pytest.mark.slow
    async def test_player_get_most_played_champions(self, real_client: "NexarClient") -> None:
        """Live canary: get_most_played_champions returns up to top_n stats, games-played descending."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")

        top = await player.get_most_played_champions(top_n=3)

        assert isinstance(top, list)
        assert len(top) <= 3
        assert all(isinstance(stat, ChampionStats) for stat in top)
        games = [stat.games_played for stat in top]
        assert games == sorted(games, reverse=True)

    @pytest.mark.slow
    async def test_player_get_performance_summary(self, real_client: "NexarClient") -> None:
        """Live canary: performance summary keeps its invariants."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")

        matches = await player.get_matches(count=10)
        summary = matches.get_performance_stats()
        assert isinstance(summary, PerformanceStats)

        assert isinstance(summary.total_games, int)
        assert isinstance(summary.wins, int)
        assert isinstance(summary.losses, int)
        assert isinstance(summary.win_rate, float)
        assert isinstance(summary.avg_kills, float)
        assert isinstance(summary.avg_deaths, float)
        assert isinstance(summary.avg_assists, float)
        assert isinstance(summary.avg_kda, float)

        assert 0 <= summary.win_rate <= 1
        assert summary.wins + summary.losses == summary.total_games

    @pytest.mark.slow
    async def test_player_get_recent_performance_by_role(self, real_client: "NexarClient") -> None:
        """Live canary: role buckets carry the documented keys."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")

        role_performance = await player.get_recent_performance_by_role(count=10)
        assert isinstance(role_performance, dict)

        for stats in role_performance.values():
            assert "games" in stats
            assert "wins" in stats
            assert "win_rate" in stats


class TestMostPlayedChampionsMocked:
    """get_most_played_champions ordering and truncation, pinned offline (P6: it had zero coverage)."""

    async def test_orders_by_games_played_and_truncates(
        self,
        batch_player: Player,
        mock_aioresponse: "aioresponses",
        mock_responses: dict[str, Any],
    ) -> None:
        mock_aioresponse.get(_IDS_URL, payload=["NA1_1", "NA1_2", "NA1_3"], repeat=True)
        _register_match(mock_aioresponse, mock_responses, "NA1_1", win=True, champion_id=69, champion_name="Cassiopeia")
        _register_match(
            mock_aioresponse,
            mock_responses,
            "NA1_2",
            win=False,
            champion_id=69,
            champion_name="Cassiopeia",
        )
        _register_match(mock_aioresponse, mock_responses, "NA1_3", win=True, champion_id=22, champion_name="Ashe")

        top_one = await batch_player.get_most_played_champions(top_n=1)

        assert [stat.champion_name for stat in top_one] == ["Cassiopeia"]
        assert top_one[0].games_played == 2
        assert top_one[0].wins == 1
        assert top_one[0].losses == 1

        top_all = await batch_player.get_most_played_champions(top_n=5)

        assert [(stat.champion_name, stat.games_played) for stat in top_all] == [
            ("Cassiopeia", 2),
            ("Ashe", 1),
        ]


class TestIsOnWinStreak:
    """is_on_win_streak pinned offline (P5: it had zero mocked coverage)."""

    @pytest.mark.parametrize(
        ("win_flags", "expected"),
        [
            ([True, True, False], True),
            ([True, False], False),
        ],
        ids=["two-wins-then-loss", "one-win-then-loss"],
    )
    async def test_streak_reads_player_wins_from_most_recent_match(
        self,
        batch_player: Player,
        mock_aioresponse: "aioresponses",
        mock_responses: dict[str, Any],
        *,
        win_flags: list[bool],
        expected: bool,
    ) -> None:
        match_ids = [f"NA1_{index}" for index in range(len(win_flags))]
        mock_aioresponse.get(_IDS_URL, payload=match_ids, repeat=True)
        for match_id, win in zip(match_ids, win_flags, strict=True):
            _register_match(mock_aioresponse, mock_responses, match_id, win=win)

        assert await batch_player.is_on_win_streak(min_games=2) is expected


@pytest_asyncio.fixture
async def batch_player() -> AsyncGenerator[Player]:
    """Player bound to an isolated client, ready for inline match mocks."""
    client = NexarClient(
        riot_api_key="test-api-key",
        default_region=Region.NA1,
        cache_config=NO_CACHE_CONFIG,
    )
    yield Player(
        client=client,
        game_name="bexli",
        tag_line="bex",
        riot_account=RiotAccount(puuid="test-puuid", game_name="bexli", tag_line="bex"),
        region=Region.NA1,
    )
    await client.close()


class TestGetMatchesBatchErrorHandling:
    """get_matches must keep successful matches when one match id fails."""

    async def test_one_missing_match_raises_batch_error_keeping_successes(
        self,
        batch_player: Player,
        mock_aioresponse: "aioresponses",
        mock_responses: dict[str, Any],
    ) -> None:
        """A single 404 must not discard the matches that did load."""
        mock_aioresponse.get(
            re.compile(r"https://americas\.api\.riotgames\.com/lol/match/v5/matches/by-puuid/test-puuid/ids.*"),
            payload=["NA1_1", "NA1_2", "NA1_3"],
        )
        mock_aioresponse.get(
            "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_2",
            status=404,
            payload={"status": {"message": "Not Found", "status_code": 404}},
        )
        for match_id in ("NA1_1", "NA1_3"):
            payload = copy.deepcopy(mock_responses["match"])
            payload["metadata"]["matchId"] = match_id
            mock_aioresponse.get(
                f"https://americas.api.riotgames.com/lol/match/v5/matches/{match_id}",
                payload=payload,
            )

        with pytest.raises(BatchError) as exc_info:
            await batch_player.get_matches(count=3)

        batch_error = exc_info.value
        assert [label for label, _ in batch_error.errors] == ["NA1_2"]
        assert isinstance(batch_error.errors[0][1], NotFoundError)
        assert sorted(match.metadata.match_id for match in batch_error.successful_results) == ["NA1_1", "NA1_3"]

    async def test_allow_partial_returns_loaded_matches_and_names_the_skip(
        self,
        batch_player: Player,
        mock_aioresponse: "aioresponses",
        mock_responses: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """allow_partial swaps the raise for the matches that loaded plus a warning."""
        mock_aioresponse.get(_IDS_URL, payload=["NA1_1", "NA1_2", "NA1_3"])
        mock_aioresponse.get(
            "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_2",
            status=404,
            payload={"status": {"message": "Not Found", "status_code": 404}},
        )
        for match_id in ("NA1_1", "NA1_3"):
            payload = copy.deepcopy(mock_responses["match"])
            payload["metadata"]["matchId"] = match_id
            mock_aioresponse.get(_MATCH_URL.format(match_id=match_id), payload=payload)

        with caplog.at_level(logging.WARNING, logger="nexar"):
            matches = await batch_player.get_matches(count=3, allow_partial=True)

        assert sorted(match.metadata.match_id for match in matches) == ["NA1_1", "NA1_3"]
        assert "NA1_2" in caplog.text

    async def test_allow_partial_still_raises_when_every_id_fails(
        self,
        batch_player: Player,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """There is no partial result when nothing loaded, so the call still fails."""
        mock_aioresponse.get(_IDS_URL, payload=["NA1_404"])
        mock_aioresponse.get(
            "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_404",
            status=404,
            payload={"status": {"message": "Not Found", "status_code": 404}},
        )

        with pytest.raises(BatchError) as exc_info:
            await batch_player.get_matches(count=1, allow_partial=True)

        assert [label for label, _ in exc_info.value.errors] == ["NA1_404"]
        assert exc_info.value.successful_results == []

    async def test_all_matches_missing_raises_batch_error_with_no_successes(
        self,
        batch_player: Player,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """When every id fails the BatchError carries no successes."""
        mock_aioresponse.get(
            re.compile(r"https://americas\.api\.riotgames\.com/lol/match/v5/matches/by-puuid/test-puuid/ids.*"),
            payload=["NA1_404"],
        )
        mock_aioresponse.get(
            "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_404",
            status=404,
            payload={"status": {"message": "Not Found", "status_code": 404}},
        )

        with pytest.raises(BatchError) as exc_info:
            await batch_player.get_matches(count=1)

        assert [label for label, _ in exc_info.value.errors] == ["NA1_404"]
        assert exc_info.value.successful_results == []


class TestRoleFallback:
    """Unresolved positions must fall back to UNKNOWN, never an empty key."""

    async def test_empty_team_position_maps_to_unknown_role(
        self,
        batch_player: Player,
        mock_aioresponse: "aioresponses",
        mock_responses: dict[str, Any],
    ) -> None:
        """A participant with EMPTY team_position reports under UNKNOWN."""
        payload = copy.deepcopy(mock_responses["match"])
        payload["info"]["participants"][0]["puuid"] = "test-puuid"
        payload["info"]["participants"][0]["teamPosition"] = MatchParticipantPosition.EMPTY.value

        mock_aioresponse.get(
            re.compile(r"https://americas\.api\.riotgames\.com/lol/match/v5/matches/by-puuid/test-puuid/ids.*"),
            payload=["NA1_1"],
        )
        mock_aioresponse.get(
            "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_1",
            payload=payload,
        )

        role_performance = await batch_player.get_recent_performance_by_role(count=1)

        assert list(role_performance) == ["UNKNOWN"]
        assert role_performance["UNKNOWN"]["games"] == 1


class TestRolePerformanceKda:
    """Zero-death role records must average as a perfect KDA, not 0.0."""

    async def test_zero_deaths_role_records_are_perfect_kda(
        self,
        batch_player: Player,
        mock_aioresponse: "aioresponses",
        mock_responses: dict[str, Any],
    ) -> None:
        """Every role bucket with zero deaths averages kills+assists, mirroring Participant.kda."""
        payload = copy.deepcopy(mock_responses["match"])
        target = payload["info"]["participants"][0]
        target["puuid"] = "test-puuid"
        target["deaths"] = 0

        mock_aioresponse.get(
            re.compile(r"https://americas\.api\.riotgames\.com/lol/match/v5/matches/by-puuid/test-puuid/ids.*"),
            payload=["NA1_1"],
        )
        mock_aioresponse.get(
            "https://americas.api.riotgames.com/lol/match/v5/matches/NA1_1",
            payload=payload,
        )

        role_stats = await batch_player.get_recent_performance_by_role(count=1)

        assert role_stats
        for stats in role_stats.values():
            assert stats["avg_kda"] == stats["kills"] + stats["assists"]
