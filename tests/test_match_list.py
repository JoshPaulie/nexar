"""Tests for the MatchList class."""

import textwrap
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

import pytest

from nexar.models.match.challenges import Challenges
from nexar.models.match_list import MatchList
from tests.helpers import create_test_match, create_test_participant

if TYPE_CHECKING:
    from nexar.client import NexarClient


def documented_example(func: Callable[..., Any]) -> str:
    """Extract the runnable statements of a function docstring's ``Example:`` block."""
    lines = (func.__doc__ or "").splitlines()
    for index, line in enumerate(lines):
        if line.strip() == "Example:":
            block = [
                example_line
                for example_line in lines[index + 1 :]
                if example_line.strip() and not example_line.strip().startswith("#")
            ]
            return textwrap.dedent("\n".join(block))
    msg = f"{func.__qualname__} has no Example: block"
    raise AssertionError(msg)


def run_documented_example(func: Callable[..., Any], matches: MatchList) -> dict[str, Any]:
    """Execute a docstring example against ``matches`` and return the variables it binds."""
    namespace: dict[str, Any] = {"matches": matches}
    exec(documented_example(func), namespace)  # noqa: S102 - executing our own docstring
    return {name: value for name, value in namespace.items() if name != "matches" and not name.startswith("__")}


class TestMatchList:
    """Test the MatchList class."""

    @pytest.mark.slow
    async def test_get_average_stat(self, real_client: "NexarClient") -> None:
        """Test getting the average of a participant stat."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")
        matches = await player.get_matches(count=5)

        # Test with a valid stat
        avg_gold_per_min = matches.get_average_stat(
            lambda p: p.challenges.gold_per_minute or 0.0,
        )
        assert isinstance(avg_gold_per_min, float)
        assert avg_gold_per_min > 0

        # Test with another valid stat
        avg_kda = matches.get_average_stat(
            lambda p: p.challenges.kda or 0.0,
        )
        assert isinstance(avg_kda, float)
        assert avg_kda > 0

        # Test with an empty match list
        empty_matches = MatchList([], player.puuid)
        avg_stat_empty = empty_matches.get_average_stat(lambda p: p.kills)
        assert avg_stat_empty == 0.0

    @pytest.mark.parametrize(
        ("durations", "threshold", "expected_ids"),
        [
            ([1000, 2000, 3000], 1500, ["NA1_2", "NA1_3"]),
            ([1000], 9999, []),
        ],
        ids=["two-above-threshold", "none-above-threshold"],
    )
    def test_filter(self, durations: list[int], threshold: int, expected_ids: list[str]) -> None:
        matches = MatchList(
            [
                create_test_match(f"NA1_{index}", puuid="p1", game_id=index, game_duration=duration)
                for index, duration in enumerate(durations, start=1)
            ],
            "p1",
        )

        filtered = matches.filter(lambda m: m.info.game_duration > threshold)

        assert [m.metadata.match_id for m in filtered] == expected_ids
        assert isinstance(filtered, MatchList)
        assert filtered.puuid == "p1"

    @pytest.mark.parametrize(
        ("reverse", "expected"),
        [(False, [1000, 2000, 3000]), (True, [3000, 2000, 1000])],
        ids=["ascending", "descending"],
    )
    def test_sort_by(self, *, reverse: bool, expected: list[int]) -> None:
        matches = MatchList(
            [
                create_test_match("NA1_1", puuid="p1", game_id=1, game_duration=3000),
                create_test_match("NA1_2", puuid="p1", game_id=2, game_duration=1000),
                create_test_match("NA1_3", puuid="p1", game_id=3, game_duration=2000),
            ],
            "p1",
        )

        sorted_ml = matches.sort_by(lambda m: m.info.game_duration, reverse=reverse)

        assert [m.info.game_duration for m in sorted_ml] == expected
        assert sorted_ml.puuid == "p1"

    @pytest.mark.parametrize(
        ("index", "expected_ids"),
        [
            (0, ["NA1_1"]),
            (1, ["NA1_2"]),
            (-1, ["NA1_3"]),
            (slice(1, 3), ["NA1_2", "NA1_3"]),
            (slice(None), ["NA1_1", "NA1_2", "NA1_3"]),
        ],
        ids=["first", "second", "negative", "slice", "full-slice"],
    )
    def test_getitem(self, index: object, expected_ids: list[str]) -> None:
        matches = MatchList(
            [
                create_test_match("NA1_1", puuid="p1", game_id=1),
                create_test_match("NA1_2", puuid="p1", game_id=2),
                create_test_match("NA1_3", puuid="p1", game_id=3),
            ],
            "p1",
        )

        result = matches[index]

        if isinstance(index, slice):
            assert isinstance(result, MatchList)
            assert result.puuid == "p1"
            assert [m.metadata.match_id for m in result] == expected_ids
        else:
            assert [result.metadata.match_id] == expected_ids


class TestGetAverageStatWithoutChallenges:
    """Pre-2022 matches have no ``challenges`` block; the documented usage must survive it."""

    def test_documented_example_runs_when_challenges_is_none(self) -> None:
        """The docstring example must not raise for a match parsed without challenges."""
        participant = create_test_participant(puuid="p1", challenges=None)
        matches = MatchList([create_test_match("NA1_1", puuid="p1", participant=participant)], "p1")

        assert participant.challenges is None
        assert run_documented_example(MatchList.get_average_stat, matches) == {"avg_gold_per_min": 0.0}

    def test_documented_example_averages_available_challenges(self) -> None:
        """Matches with challenges data still contribute to the documented average."""
        without = create_test_participant(puuid="p1", challenges=None)
        with_challenges = create_test_participant(puuid="p1", challenges=Challenges(gold_per_minute=500.0))
        matches = MatchList(
            [
                create_test_match("NA1_1", puuid="p1", game_id=1, participant=without),
                create_test_match("NA1_2", puuid="p1", game_id=2, participant=with_challenges),
            ],
            "p1",
        )

        assert run_documented_example(MatchList.get_average_stat, matches) == {"avg_gold_per_min": pytest.approx(500.0)}

    def test_get_average_stat_skips_matches_without_challenges(self) -> None:
        """The None rewarded by a guarded retriever skips the match instead of counting zero."""
        without = create_test_participant(puuid="p1", challenges=None)
        first = create_test_participant(puuid="p1", challenges=Challenges(gold_per_minute=400.0))
        second = create_test_participant(puuid="p1", challenges=Challenges(gold_per_minute=600.0))
        matches = MatchList(
            [
                create_test_match("NA1_1", puuid="p1", game_id=1, participant=without),
                create_test_match("NA1_2", puuid="p1", game_id=2, participant=first),
                create_test_match("NA1_3", puuid="p1", game_id=3, participant=second),
            ],
            "p1",
        )

        average = matches.get_average_stat(
            lambda p: p.challenges.gold_per_minute if p.challenges is not None else None,
        )

        assert average == pytest.approx(500.0)


class TestPerformanceStats:
    """get_performance_stats aggregates (probe #4: win_rate→1.0 left 12 rows green)."""

    def test_performance_stats_exact_values(self) -> None:
        """The documented aggregates come out exactly for a two-match list."""
        wins = create_test_participant(
            puuid="p1",
            kills=10,
            deaths=4,
            assists=10,
            win=True,
            total_minions_killed=100,
            neutral_minions_killed=20,
        )
        losses = create_test_participant(
            puuid="p1",
            kills=2,
            deaths=6,
            assists=8,
            win=False,
            total_minions_killed=200,
            neutral_minions_killed=40,
        )
        matches = MatchList(
            [
                create_test_match("NA1_1", puuid="p1", game_id=1, participant=wins, game_duration=1800),
                create_test_match("NA1_2", puuid="p1", game_id=2, participant=losses, game_duration=1200),
            ],
            "p1",
        )

        stats = matches.get_performance_stats()

        assert stats.total_games == 2
        assert stats.wins == 1
        assert stats.losses == 1
        assert stats.win_rate == 0.5
        assert stats.avg_kills == 6.0
        assert stats.avg_deaths == 5.0
        assert stats.avg_assists == 9.0
        assert stats.avg_kda == 3.0
        assert stats.avg_cs == 180.0
        assert stats.avg_game_duration_minutes == 25.0

    def test_performance_stats_zero_deaths_is_perfect_kda(self) -> None:
        """A match list with zero total deaths averages kills+assists, mirroring Participant.kda."""
        participant = create_test_participant(puuid="p1", kills=5, deaths=0, assists=10)
        matches = MatchList([create_test_match("NA1_1", puuid="p1", participant=participant)], "p1")

        stats = matches.get_performance_stats()

        assert stats.avg_kda == 15.0
