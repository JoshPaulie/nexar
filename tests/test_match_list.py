"""Tests for the MatchList class."""

import textwrap
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING, Any

import pytest

from nexar.enums import MapId, MatchParticipantPosition, PlatformId, Queue
from nexar.models.match.challenges import Challenges
from nexar.models.match.match import Match, MatchInfo, MatchMetadata
from nexar.models.match.participant import Participant
from nexar.models.match.participant_list import ParticipantList
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

    def test_filter(self) -> None:
        m1 = create_test_match("NA1_1", puuid="p1", game_id=1, game_duration=1000)
        m2 = create_test_match("NA1_2", puuid="p1", game_id=2, game_duration=2000)
        m3 = create_test_match("NA1_3", puuid="p1", game_id=3, game_duration=3000)
        ml = MatchList([m1, m2, m3], "p1")

        filtered = ml.filter(lambda m: m.info.game_duration > 1500)
        assert len(filtered) == 2
        assert filtered.puuid == "p1"
        assert isinstance(filtered, MatchList)

    def test_filter_empty_result(self) -> None:
        m1 = create_test_match("NA1_1", puuid="p1", game_id=1)
        ml = MatchList([m1], "p1")
        filtered = ml.filter(lambda m: m.info.game_duration > 9999)
        assert len(filtered) == 0
        assert isinstance(filtered, MatchList)

    def test_sort_by_ascending(self) -> None:
        m1 = create_test_match("NA1_1", puuid="p1", game_id=1, game_duration=3000)
        m2 = create_test_match("NA1_2", puuid="p1", game_id=2, game_duration=1000)
        m3 = create_test_match("NA1_3", puuid="p1", game_id=3, game_duration=2000)
        ml = MatchList([m1, m2, m3], "p1")

        sorted_ml = ml.sort_by(lambda m: m.info.game_duration)
        assert [m.info.game_duration for m in sorted_ml] == [1000, 2000, 3000]
        assert sorted_ml.puuid == "p1"

    def test_sort_by_descending(self) -> None:
        m1 = create_test_match("NA1_1", puuid="p1", game_id=1, game_duration=1000)
        m2 = create_test_match("NA1_2", puuid="p1", game_id=2, game_duration=3000)
        ml = MatchList([m1, m2], "p1")

        sorted_ml = ml.sort_by(lambda m: m.info.game_duration, reverse=True)
        assert [m.info.game_duration for m in sorted_ml] == [3000, 1000]

    def test_getitem_int(self) -> None:
        m1 = create_test_match("NA1_1", puuid="p1", game_id=1)
        m2 = create_test_match("NA1_2", puuid="p1", game_id=2)
        ml = MatchList([m1, m2], "p1")

        assert ml[0].metadata.match_id == "NA1_1"
        assert ml[1].metadata.match_id == "NA1_2"

    def test_getitem_slice(self) -> None:
        m1 = create_test_match("NA1_1", puuid="p1", game_id=1)
        m2 = create_test_match("NA1_2", puuid="p1", game_id=2)
        m3 = create_test_match("NA1_3", puuid="p1", game_id=3)
        ml = MatchList([m1, m2, m3], "p1")

        sliced = ml[1:3]
        assert isinstance(sliced, MatchList)
        assert len(sliced) == 2
        assert sliced.puuid == "p1"
        assert sliced[0].metadata.match_id == "NA1_2"
        assert sliced[1].metadata.match_id == "NA1_3"

    def test_getitem_slice_full(self) -> None:
        m1 = create_test_match("NA1_1", puuid="p1", game_id=1)
        ml = MatchList([m1], "p1")
        sliced = ml[:]
        assert isinstance(sliced, MatchList)
        assert len(sliced) == 1

    def test_getitem_negative_index(self) -> None:
        m1 = create_test_match("NA1_1", puuid="p1", game_id=1)
        m2 = create_test_match("NA1_2", puuid="p1", game_id=2)
        ml = MatchList([m1, m2], "p1")
        assert ml[-1].metadata.match_id == "NA1_2"


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


class TestPerformanceStatsZeroDeaths:
    """Zero-death match lists must average as a perfect KDA, not 0.0."""

    def test_performance_stats_zero_deaths_is_perfect_kda(self) -> None:
        """A match list with zero total deaths averages kills+assists, mirroring Participant.kda."""
        participant = create_test_participant(puuid="p1", kills=5, deaths=0, assists=10)
        matches = MatchList([create_test_match("NA1_1", puuid="p1", participant=participant)], "p1")

        stats = matches.get_performance_stats()

        assert stats.avg_kda == 15.0
