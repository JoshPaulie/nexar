"""Tests for utility functions."""

from typing import Any

import pytest
from pytest_mock import MockerFixture

from nexar.enums import Queue, RankDivision, RankTier
from nexar.models.league import LeagueEntry
from nexar.models.player import Player
from nexar.utils import sort_players_by_rank


class TestSortPlayersByRank:
    """Test the sort_players_by_rank utility function."""

    @pytest.fixture
    def mock_players(self, mocker: MockerFixture) -> list[Player]:
        """Create mock players with different ranks."""
        # Mock the client
        mock_client = mocker.Mock()

        # Create mock players
        players = []

        # Player 1: Gold II (mid-tier)
        player1 = Player(
            client=mock_client,
            game_name="player1",
            tag_line="tag1",
            riot_account=mocker.Mock(puuid="puuid1"),
        )
        gold_rank = LeagueEntry(
            league_id="test-league-1",
            puuid="puuid1",
            queue_type=Queue.RANKED_SOLO_5x5,
            tier=RankTier.GOLD,
            division=RankDivision.TWO,
            league_points=50,
            wins=60,
            losses=40,
            hot_streak=False,
            veteran=False,
            fresh_blood=False,
            inactive=False,
        )
        mocker.patch.object(player1, "get_solo_rank", return_value=gold_rank)
        mocker.patch.object(player1, "get_flex_rank", return_value=None)
        players.append(player1)

        # Player 2: Diamond I (highest)
        player2 = Player(
            client=mock_client,
            game_name="player2",
            tag_line="tag2",
            riot_account=mocker.Mock(puuid="puuid2"),
        )
        diamond_rank = LeagueEntry(
            league_id="test-league-2",
            puuid="puuid2",
            queue_type=Queue.RANKED_SOLO_5x5,
            tier=RankTier.DIAMOND,
            division=RankDivision.ONE,
            league_points=75,
            wins=100,
            losses=80,
            hot_streak=True,
            veteran=True,
            fresh_blood=False,
            inactive=False,
        )
        player2.get_solo_rank = mocker.AsyncMock(return_value=diamond_rank)
        player2.get_flex_rank = mocker.AsyncMock(return_value=None)
        players.append(player2)

        # Player 3: Unranked
        player3 = Player(
            client=mock_client,
            game_name="player3",
            tag_line="tag3",
            riot_account=mocker.Mock(puuid="puuid3"),
        )
        player3.get_solo_rank = mocker.AsyncMock(return_value=None)
        player3.get_flex_rank = mocker.AsyncMock(return_value=None)
        players.append(player3)

        # Player 4: Silver III (lowest ranked)
        player4 = Player(
            client=mock_client,
            game_name="player4",
            tag_line="tag4",
            riot_account=mocker.Mock(puuid="puuid4"),
        )
        silver_rank = LeagueEntry(
            league_id="test-league-4",
            puuid="puuid4",
            queue_type=Queue.RANKED_SOLO_5x5,
            tier=RankTier.SILVER,
            division=RankDivision.THREE,
            league_points=25,
            wins=30,
            losses=35,
            hot_streak=False,
            veteran=False,
            fresh_blood=True,
            inactive=False,
        )
        player4.get_solo_rank = mocker.AsyncMock(return_value=silver_rank)
        player4.get_flex_rank = mocker.AsyncMock(return_value=None)
        players.append(player4)

        return players

    async def test_sort_players_by_rank_descending(self, mock_players: list[Player]) -> None:
        """Test sorting players by rank in descending order (highest first)."""
        sorted_players = await sort_players_by_rank(mock_players, descending=True)

        # Order should be: Diamond I, Gold II, Silver III, Unranked
        assert sorted_players[0].game_name == "player2"  # Diamond I
        assert sorted_players[1].game_name == "player1"  # Gold II
        assert sorted_players[2].game_name == "player4"  # Silver III
        assert sorted_players[3].game_name == "player3"  # Unranked

    async def test_sort_players_by_rank_ascending(self, mock_players: list[Player]) -> None:
        """Test sorting players by rank in ascending order (lowest first)."""
        sorted_players = await sort_players_by_rank(mock_players, descending=False)

        # Order should be: Silver III, Gold II, Diamond I, Unranked
        assert sorted_players[0].game_name == "player4"  # Silver III
        assert sorted_players[1].game_name == "player1"  # Gold II
        assert sorted_players[2].game_name == "player2"  # Diamond I
        assert sorted_players[3].game_name == "player3"  # Unranked

    async def test_sort_players_by_flex_rank(self, mock_players: list[Player], mocker: MockerFixture) -> None:
        """Test sorting players by flex queue rank."""
        # Give one player a flex rank
        flex_rank = LeagueEntry(
            league_id="test-league-flex",
            puuid="puuid1",
            queue_type=Queue.RANKED_FLEX_SR,
            tier=RankTier.PLATINUM,
            division=RankDivision.FOUR,
            league_points=88,
            wins=25,
            losses=15,
            hot_streak=False,
            veteran=False,
            fresh_blood=False,
            inactive=False,
        )
        mock_players[0].get_flex_rank = mocker.AsyncMock(return_value=flex_rank)

        sorted_players = await sort_players_by_rank(
            mock_players,
            ranked_queue_type=Queue.RANKED_FLEX_SR,
        )

        # Only one player has flex rank, so they should be first
        assert sorted_players[0].game_name == "player1"  # Has flex rank
        # Other players should follow (order doesn't matter much since they're all unranked in flex)

    async def test_sort_players_invalid_queue_type(self, mock_players: list[Player]) -> None:
        """Test that invalid queue type raises ValueError."""
        with pytest.raises(ValueError, match="Invalid queue_type"):
            await sort_players_by_rank(mock_players, ranked_queue_type=Queue.QUICKPLAY)

    async def test_sort_players_empty_list(self) -> None:
        """Test sorting an empty list of players."""
        sorted_players = await sort_players_by_rank([])
        assert sorted_players == []

    async def test_sort_players_all_unranked(self, mocker: MockerFixture) -> None:
        """Test sorting players who are all unranked."""
        mock_client: Any = mocker.Mock()

        players = []
        for i in range(3):
            player = Player(
                client=mock_client,
                game_name=f"player{i}",
                tag_line=f"tag{i}",
                riot_account=mocker.Mock(puuid=f"puuid{i}"),
            )
            player.get_solo_rank = mocker.AsyncMock(return_value=None)
            player.get_flex_rank = mocker.AsyncMock(return_value=None)
            players.append(player)

        sorted_players = await sort_players_by_rank(players)

        # All players are unranked, so order should be preserved
        assert len(sorted_players) == 3
        assert all(p in players for p in sorted_players)
