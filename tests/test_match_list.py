"""Tests for the MatchList class."""

from typing import TYPE_CHECKING

from nexar.models.match_list import MatchList

if TYPE_CHECKING:
    from nexar.client import NexarClient


class TestMatchList:
    """Test the MatchList class."""

    async def test_get_average_stat(self, real_client: "NexarClient") -> None:
        """Test getting the average of a participant stat."""
        player = await real_client.get_player("bexli", "bex")
        matches = await player.get_matches(count=5)

        # Test with a valid stat
        avg_gold_per_min = matches.get_average_stat(
            lambda p: p.challenges.gold_per_minute or 0.0 if p.challenges else 0.0,
        )
        assert isinstance(avg_gold_per_min, float)
        assert avg_gold_per_min > 0

        # Test with another valid stat
        avg_kda = matches.get_average_stat(
            lambda p: p.challenges.kda or 0.0 if p.challenges else 0.0,
        )
        assert isinstance(avg_kda, float)
        assert avg_kda > 0

        # Test with an empty match list
        empty_matches = MatchList([], player.puuid)
        avg_stat_empty = empty_matches.get_average_stat(lambda p: p.kills)
        assert avg_stat_empty == 0.0
