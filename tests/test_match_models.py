"""Tests for match models."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

import pytest

from nexar.enums import MapId, MatchParticipantPosition, PlatformId, Queue
from nexar.models import (
    Ban,
    Challenges,
    Match,
    MatchInfo,
    MatchMetadata,
    Objective,
    Objectives,
    Participant,
    ParticipantList,
)
from tests.helpers import create_test_participant

if TYPE_CHECKING:
    from nexar.client import NexarClient


class TestMatchModels:
    """Test match-related models."""

    @pytest.mark.slow
    async def test_match_from_api_response(self, real_client: "NexarClient") -> None:
        """Test Match creation from real API response."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")
        matches = await player.get_matches(count=1)

        if matches:
            match = matches[0]
            # Basic validation that the match was created properly
            assert match.metadata is not None
            assert match.info is not None
            assert len(match.info.participants) == 10  # Standard 5v5 match
            assert match.metadata.match_id is not None

    def test_ban_creation(self) -> None:
        """Test Ban model can be created directly."""
        ban = Ban(champion_id=238, pick_turn=1)

        assert ban.champion_id == 238
        assert ban.pick_turn == 1

    def test_objective_creation(self) -> None:
        """Test Objective model can be created directly."""
        objective = Objective(first=True, kills=1)

        assert objective.first is True
        assert objective.kills == 1

    def test_challenges_creation(self) -> None:
        """Test Challenges creation from API response."""
        challenges_data = {
            "kda": 6.5,
            "killParticipation": 0.65,
            "damagePerMinute": 833.33,
            "goldPerMinute": 500.0,
            "visionScorePerMinute": 1.5,
        }

        challenges = Challenges.from_api_response(challenges_data)

        assert challenges.kda == 6.5
        assert challenges.kill_participation == 0.65
        assert challenges.damage_per_minute == 833.33
        assert challenges.gold_per_minute == 500.0
        assert challenges.vision_score_per_minute == 1.5

    def test_objectives_creation(self) -> None:
        """Test Objectives creation from API response."""
        objectives_data = {
            "baron": {"first": True, "kills": 1},
            "champion": {"first": True, "kills": 20},
            "dragon": {"first": True, "kills": 3},
            "horde": {"first": False, "kills": 0},
            "inhibitor": {"first": True, "kills": 2},
            "riftHerald": {"first": True, "kills": 1},
            "tower": {"first": True, "kills": 8},
        }

        objectives = Objectives.from_api_response(objectives_data)

        assert isinstance(objectives, Objectives)
        assert isinstance(objectives.baron, Objective)
        assert isinstance(objectives.dragon, Objective)
        assert isinstance(objectives.tower, Objective)

        # Test baron objective
        assert objectives.baron.first is True
        assert objectives.baron.kills == 1

    def test_match_iteration(self) -> None:
        """Test that Match is iterable over participants."""
        blue_participant = create_test_participant(
            puuid="blue_player",
            game_name="BluePlayer",
            tagline="BLU",
            champion_id=1,
            champion_name="Annie",
            team_id=100,
            participant_id=1,
            total_damage_dealt_to_champions=20000,
            total_damage_taken=15000,
            win=True,
        )

        red_participant = create_test_participant(
            puuid="red_player",
            game_name="RedPlayer",
            tagline="RED",
            champion_id=2,
            champion_name="Olaf",
            team_id=200,
            participant_id=2,
            kills=3,
            deaths=5,
            assists=8,
            champion_level=16,
            gold_earned=12000,
            gold_spent=11000,
            total_damage_dealt_to_champions=18000,
            total_damage_taken=20000,
            vision_score=25,
            individual_position=MatchParticipantPosition.JUNGLE,
            team_position=MatchParticipantPosition.JUNGLE,
            lane="JUNGLE",
            role="NONE",
            win=False,
        )

        match_info = MatchInfo(
            game_creation=datetime.fromtimestamp(1234567890),
            game_duration=1800,
            game_id=12345,
            game_mode="CLASSIC",
            game_start_timestamp=datetime.fromtimestamp(1234567890),
            game_type="MATCHED_GAME",
            game_version="14.1.1",
            map_id=MapId.SUMMONERS_RIFT,
            platform_id=PlatformId.NA1,
            queue_id=Queue.RANKED_SOLO_5x5,
            participants=ParticipantList([blue_participant, red_participant]),
            teams=[],
        )

        match_metadata = MatchMetadata(
            data_version="2",
            match_id="NA1_1234567890",
            participants=["blue_player", "red_player"],
        )

        match = Match(metadata=match_metadata, info=match_info)

        # Test iteration via participants
        participant_names = [participant.game_name for participant in match.participants]

        assert participant_names == ["BluePlayer", "RedPlayer"]

    async def test_get_player_returns_player(self, client: "NexarClient") -> None:
        """Test that Participant.get_player() returns a Player."""
        participant = create_test_participant(puuid="test-puuid-123")

        player = await participant.get_player(client)

        assert player.game_name == "bexli"
        assert player.tag_line == "bex"
        assert player.riot_account is not None

    @pytest.mark.slow
    async def test_get_player_with_real_client(self, real_client: "NexarClient") -> None:
        """Integration test: get_player() returns a real Player."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")
        matches = await player.get_matches(count=1)

        if matches:
            first_match = matches[0]
            # Find the participant matching this player's PUUID
            participant = first_match.participants.by_puuid(player.puuid)
            assert participant is not None

            player_from_participant = await participant.get_player(real_client)

            # Both Players should reference the same Riot account (same PUUID)
            assert player_from_participant.riot_account.puuid == player.riot_account.puuid
            assert player_from_participant.riot_account is not None
