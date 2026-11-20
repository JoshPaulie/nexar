"""Tests for utility functions."""

import pytest
from pytest_mock import MockerFixture

from nexar import RiotAccount
from nexar.enums import Queue, RankDivision, RankTier
from nexar.models.league import LeagueEntry
from nexar.models.match.participant import Participant
from nexar.models.match.participant_list import ParticipantList
from nexar.models.player import Player
from nexar.utils import sort_players_by_rank, team_total_percentage
from tests.helpers import create_test_participant


def _solo_entry(puuid: str, tier: RankTier, division: RankDivision, league_points: int) -> LeagueEntry:
    return LeagueEntry(
        league_id=f"test-league-{puuid}",
        puuid=puuid,
        queue_type=Queue.RANKED_SOLO_5x5,
        queue_type_raw="RANKED_SOLO_5x5",
        tier=tier,
        division=division,
        league_points=league_points,
        wins=50,
        losses=50,
        hot_streak=False,
        veteran=False,
        fresh_blood=False,
        inactive=False,
    )


class TestSortPlayersByRank:
    """Test the sort_players_by_rank utility function."""

    @pytest.fixture
    def mock_players(self, mocker: MockerFixture) -> list[Player]:
        """Four players: Diamond I, Gold II, unranked, Silver III — all unranked in flex."""

        def make_player(name: str, *, solo_rank: LeagueEntry | None) -> Player:
            player = Player(
                client=mocker.Mock(),
                game_name=name,
                tag_line=f"tag-{name}",
                riot_account=RiotAccount(puuid=f"puuid-{name}", game_name=name, tag_line=f"tag-{name}"),
            )
            player.get_solo_rank = mocker.AsyncMock(return_value=solo_rank)
            player.get_flex_rank = mocker.AsyncMock(return_value=None)
            return player

        return [
            make_player("player1", solo_rank=_solo_entry("puuid-player1", RankTier.GOLD, RankDivision.TWO, 50)),
            make_player("player2", solo_rank=_solo_entry("puuid-player2", RankTier.DIAMOND, RankDivision.ONE, 75)),
            make_player("player3", solo_rank=None),
            make_player("player4", solo_rank=_solo_entry("puuid-player4", RankTier.SILVER, RankDivision.THREE, 25)),
        ]

    @pytest.mark.parametrize(
        ("descending", "expected_names"),
        [
            (True, ["player2", "player1", "player4", "player3"]),
            (False, ["player4", "player1", "player2", "player3"]),
        ],
        ids=["descending", "ascending"],
    )
    async def test_sort_players_by_rank(
        self,
        mock_players: list[Player],
        *,
        descending: bool,
        expected_names: list[str],
    ) -> None:
        """Ranked players order by rank in the requested direction; unranked go last."""
        sorted_players = await sort_players_by_rank(mock_players, descending=descending)

        assert [p.game_name for p in sorted_players] == expected_names

    async def test_sort_players_by_flex_rank(
        self,
        mock_players: list[Player],
        mocker: MockerFixture,
    ) -> None:
        """Sorting by flex keeps the one flex-ranked player first and preserves input order after."""
        flex_rank = LeagueEntry(
            league_id="test-league-flex",
            puuid="puuid-player1",
            queue_type=Queue.RANKED_FLEX_SR,
            queue_type_raw="RANKED_FLEX_SR",
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

        sorted_players = await sort_players_by_rank(mock_players, ranked_queue_type=Queue.RANKED_FLEX_SR)

        assert [p.game_name for p in sorted_players] == ["player1", "player2", "player3", "player4"]

    async def test_sort_players_invalid_queue_type(self, mock_players: list[Player]) -> None:
        """Test that invalid queue type raises ValueError naming the ranked_queue_type parameter."""
        with pytest.raises(ValueError, match="Invalid ranked_queue_type"):
            await sort_players_by_rank(mock_players, ranked_queue_type=Queue.QUICKPLAY)

    async def test_sort_players_empty_list(self) -> None:
        """Test sorting an empty list of players."""
        sorted_players = await sort_players_by_rank([])
        assert sorted_players == []

    async def test_sort_players_all_unranked_preserves_order(self, mocker: MockerFixture) -> None:
        """All-unranked players keep their input order exactly."""
        players = [
            Player(
                client=mocker.Mock(),
                game_name=f"player{i}",
                tag_line=f"tag{i}",
                riot_account=RiotAccount(puuid=f"puuid{i}", game_name=f"player{i}", tag_line=f"tag{i}"),
            )
            for i in range(3)
        ]
        for player in players:
            player.get_solo_rank = mocker.AsyncMock(return_value=None)
            player.get_flex_rank = mocker.AsyncMock(return_value=None)

        sorted_players = await sort_players_by_rank(players)

        assert [p.game_name for p in sorted_players] == ["player0", "player1", "player2"]


class TestTeamTotalPercentage:
    @pytest.mark.parametrize(
        ("damage_by_puuid", "target_puuid", "expected"),
        [
            ({"p1": 20000, "p2": 15000}, "p1", 57.142857142857146),
            ({"p1": 0, "p2": 0}, "p1", 0.0),
            ({"p1": 1000, "p2": 2000, "p3": 5000}, "p1", 33.333333333333336),
            ({"p1": 500}, "p1", 100.0),
        ],
        ids=["basic-percentage", "zero-total-returns-zero", "only-team-members-count", "single-player"],
    )
    def test_team_total_percentage(
        self,
        damage_by_puuid: dict[str, int],
        target_puuid: str,
        expected: float,
    ) -> None:
        """The share of the target's stat within their own team, regardless of other teams."""
        participants = ParticipantList(
            [
                create_test_participant(
                    puuid=puuid,
                    team_id=200 if puuid == "p3" else 100,
                    total_damage_dealt_to_champions=damage,
                )
                for puuid, damage in damage_by_puuid.items()
            ],
        )
        target = next(p for p in participants if p.puuid == target_puuid)

        def stat_selector(participant: Participant) -> int:
            return participant.total_damage_dealt_to_champions

        result = team_total_percentage(participants, target, stat_selector)

        assert result == pytest.approx(expected)
