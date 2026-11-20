"""Tests for ParticipantList functionality."""

import pytest

from nexar.enums import MatchParticipantPosition
from nexar.models.match.challenges import Challenges
from nexar.models.match.participant import Participant
from nexar.models.match.participant_list import ParticipantList
from tests.helpers import create_test_participant


class TestParticipantList:
    """Test ParticipantList filtering and utility methods."""

    @pytest.fixture
    def sample_participants(self) -> list[Participant]:
        """Three participants: two blue (Annie, Olaf), one red (Jinx)."""

        def positioned(
            puuid: str,
            champion: str,
            team: int,
            pid: int,
            position: MatchParticipantPosition,
            **kwargs: object,
        ) -> Participant:
            lane_role = {
                MatchParticipantPosition.MIDDLE: ("MIDDLE", "SOLO"),
                MatchParticipantPosition.JUNGLE: ("JUNGLE", "NONE"),
                MatchParticipantPosition.BOTTOM: ("BOTTOM", "DUO_CARRY"),
            }[position]
            return create_test_participant(
                puuid=puuid,
                champion_name=champion,
                team_id=team,
                participant_id=pid,
                individual_position=position,
                team_position=position,
                lane=lane_role[0],
                role=lane_role[1],
                **kwargs,
            )

        return [
            positioned(
                "player1",
                "Annie",
                100,
                1,
                MatchParticipantPosition.MIDDLE,
                champion_id=1,
                kills=5,
                deaths=2,
                assists=8,
                win=True,
                total_damage_dealt_to_champions=15000,
                total_damage_taken=12000,
            ),
            positioned(
                "player2",
                "Olaf",
                100,
                2,
                MatchParticipantPosition.JUNGLE,
                champion_id=2,
                kills=8,
                deaths=3,
                assists=4,
                win=True,
                total_damage_dealt_to_champions=18000,
                total_damage_taken=12500,
            ),
            positioned(
                "player3",
                "Jinx",
                200,
                6,
                MatchParticipantPosition.BOTTOM,
                champion_id=3,
                kills=12,
                deaths=4,
                assists=6,
                win=False,
                total_damage_dealt_to_champions=25000,
                total_damage_taken=15000,
            ),
        ]

    @pytest.fixture
    def participant_list(self, sample_participants: list[Participant]) -> ParticipantList:
        """Create a ParticipantList from sample participants."""
        return ParticipantList(sample_participants)

    def test_by_puuid(self, participant_list: ParticipantList) -> None:
        """Test finding participant by PUUID."""
        participant = participant_list.by_puuid("player1")
        assert participant is not None
        assert participant.champion_name == "Annie"

        # Test non-existent PUUID
        assert participant_list.by_puuid("nonexistent") is None

    def test_by_champion(self, participant_list: ParticipantList) -> None:
        """Test filtering by champion name."""
        jinx_players = participant_list.by_champion("Jinx")
        assert len(jinx_players) == 1
        assert jinx_players[0].champion_name == "Jinx"

        # Test case insensitive
        jinx_players = participant_list.by_champion("jinx")
        assert len(jinx_players) == 1

        # Test non-existent champion
        assert len(participant_list.by_champion("Teemo")) == 0

    def test_by_position(self, participant_list: ParticipantList) -> None:
        """Test filtering by position."""
        junglers = participant_list.by_position(MatchParticipantPosition.JUNGLE)
        assert len(junglers) == 1
        assert junglers[0].champion_name == "Olaf"

    def test_by_team(self, participant_list: ParticipantList) -> None:
        """Test filtering by team (the blue_team/red_team shortcuts delegate here)."""
        blue_team = participant_list.by_team(100)
        assert len(blue_team) == 2
        assert all(p.team_id == 100 for p in blue_team)

        red_team = participant_list.by_team(200)
        assert len(red_team) == 1
        assert red_team[0].team_id == 200

    def test_winners_losers(self, participant_list: ParticipantList) -> None:
        """Test filtering by win/loss."""
        winners = participant_list.winners()
        assert len(winners) == 2
        assert all(p.win for p in winners)

        losers = participant_list.losers()
        assert len(losers) == 1
        assert not losers[0].win

    def test_filter_custom_predicate(self, participant_list: ParticipantList) -> None:
        """Test custom filtering with predicate."""
        high_kills = participant_list.filter(lambda p: p.kills > 10)
        assert len(high_kills) == 1
        assert high_kills[0].champion_name == "Jinx"

    def test_sort_by(self, participant_list: ParticipantList) -> None:
        """Test sorting by custom key."""
        sorted_by_kills = participant_list.sort_by(lambda p: p.kills, reverse=True)
        kill_counts = [p.kills for p in sorted_by_kills]
        assert kill_counts == [12, 8, 5]  # Descending order

    def test_highest_kda(self, participant_list: ParticipantList) -> None:
        """highest_kda prefers the challenges.kda key and falls back to the computed ratio."""
        # All three lack challenges.kda, so ranking falls back to (kills+assists)/max(deaths, 1).
        top_kda = participant_list.highest_kda(count=2)
        assert [p.champion_name for p in top_kda] == ["Annie", "Jinx"]  # 6.5 then 4.5 (Olaf 4.0 drops)

        # A present challenges.kda outranks every computed value.
        boosted = create_test_participant(
            puuid="player4",
            champion_name="Ahri",
            team_id=100,
            participant_id=3,
            kills=1,
            deaths=5,
            assists=1,
            win=True,
            challenges=Challenges(kda=99.0),
        )
        ranked = ParticipantList([*participant_list, boosted]).highest_kda(count=1)
        assert ranked[0].champion_name == "Ahri"

    def test_most_kills(self, participant_list: ParticipantList) -> None:
        """Test getting participants with most kills."""
        top_killers = participant_list.most_kills(count=2)
        assert len(top_killers) == 2
        assert top_killers[0].champion_name == "Jinx"  # 12 kills
        assert top_killers[1].champion_name == "Olaf"  # 8 kills

    def test_most_damage(self, participant_list: ParticipantList) -> None:
        """Test getting participants with most damage."""
        top_damage = participant_list.most_damage(count=2)
        assert len(top_damage) == 2
        assert top_damage[0].champion_name == "Jinx"  # 25000 damage
        assert top_damage[1].champion_name == "Olaf"  # 18000 damage

    def test_slicing_returns_participant_list(self, participant_list: ParticipantList) -> None:
        """Test that slicing returns a ParticipantList."""
        sliced = participant_list[:2]
        assert isinstance(sliced, ParticipantList)
        assert len(sliced) == 2

    def test_indexing_returns_participant(self, participant_list: ParticipantList) -> None:
        """Test that indexing returns a Participant."""
        participant = participant_list[0]
        assert isinstance(participant, Participant)
        assert participant.champion_name == "Annie"

    def test_chaining_operations(self, participant_list: ParticipantList) -> None:
        """Test chaining multiple operations."""
        result = participant_list.winners().filter(lambda p: p.kills > 6)
        assert len(result) == 1
        assert result[0].champion_name == "Olaf"

    def test_team_of(self, participant_list: ParticipantList) -> None:
        """Test getting all team members for a given participant PUUID."""
        # Player1 and Player2 are both on team 100
        team = participant_list.team_of("player1")
        assert len(team) == 2
        assert all(p.team_id == 100 for p in team)
        # Player3 is on team 200
        team = participant_list.team_of("player3")
        assert len(team) == 1
        assert team[0].team_id == 200
        # Non-existent PUUID should raise ValueError
        with pytest.raises(ValueError, match="No participant found with PUUID: not_a_real_puuid"):
            participant_list.team_of("not_a_real_puuid")
