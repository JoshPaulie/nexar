"""Tests for match models."""

from datetime import datetime
from typing import TYPE_CHECKING, Any

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

if TYPE_CHECKING:
    from nexar.client import NexarClient


def create_test_participant(**overrides: Any) -> Participant:
    """Create a participant with all required fields for testing."""
    defaults: dict[str, Any] = {
        # Core participant data
        "puuid": "test_player",
        "_summoner_name": "TestPlayer",
        "game_name": "TestPlayer",
        "tagline": "TST",
        "champion_id": 1,
        "champion_name": "Annie",
        "team_id": 100,
        "participant_id": 1,
        # Basic stats
        "kills": 5,
        "deaths": 2,
        "assists": 10,
        "champion_level": 18,
        "gold_earned": 15000,
        "gold_spent": 14000,
        "vision_score": 30,
        "win": True,
        # Items
        "item_0": 1001,
        "item_1": 1001,
        "item_2": 1001,
        "item_3": 1001,
        "item_4": 1001,
        "item_5": 1001,
        "item_6": 3340,
        # Position and role
        "individual_position": MatchParticipantPosition.MIDDLE,
        "team_position": MatchParticipantPosition.MIDDLE,
        "lane": "MIDDLE",
        "role": "SOLO",
        # Ping stats
        "all_in_pings": 0,
        "assist_me_pings": 0,
        "command_pings": 1,
        "enemy_missing_pings": 2,
        "enemy_vision_pings": 0,
        "get_back_pings": 0,
        "hold_pings": 0,
        "need_vision_pings": 1,
        "on_my_way_pings": 3,
        "push_pings": 0,
        "vision_cleared_pings": 0,
        # Kill stats
        "baron_kills": 0,
        "double_kills": 1,
        "dragon_kills": 0,
        "inhibitor_kills": 0,
        "killing_sprees": 2,
        "largest_killing_spree": 3,
        "largest_multi_kill": 2,
        "nexus_kills": 0,
        "penta_kills": 0,
        "quadra_kills": 0,
        "triple_kills": 0,
        "turret_kills": 1,
        "unreal_kills": 0,
        # Damage stats
        "damage_dealt_to_buildings": 5000,
        "damage_dealt_to_objectives": 3000,
        "damage_dealt_to_turrets": 4000,
        "damage_self_mitigated": 8000,
        "largest_critical_strike": 1500,
        "magic_damage_dealt": 25000,
        "magic_damage_dealt_to_champions": 20000,
        "magic_damage_taken": 12000,
        "physical_damage_dealt": 8000,
        "physical_damage_dealt_to_champions": 5000,
        "physical_damage_taken": 8000,
        "total_damage_dealt": 35000,
        "total_damage_dealt_to_champions": 25000,
        "total_damage_shielded_on_teammates": 2000,
        "total_damage_taken": 22000,
        "true_damage_dealt": 2000,
        "true_damage_dealt_to_champions": 1000,
        "true_damage_taken": 2000,
        # Minion and jungle stats
        "neutral_minions_killed": 120,
        "total_ally_jungle_minions_killed": 15,
        "total_enemy_jungle_minions_killed": 10,
        "total_minions_killed": 180,
        # Healing and support stats
        "total_heal": 3000,
        "total_heals_on_teammates": 1500,
        "total_units_healed": 8,
        # Time stats
        "longest_time_spent_living": 1200,
        "time_ccing_others": 45,
        "time_played": 1800,
        "total_time_cc_dealt": 15,
        "total_time_spent_dead": 60,
        # Ward and vision stats
        "detector_wards_placed": 2,
        "sight_wards_bought_in_game": 0,
        "vision_wards_bought_in_game": 3,
        "wards_killed": 8,
        "wards_placed": 15,
        # Spell casts
        "spell_1_casts": 25,
        "spell_2_casts": 18,
        "spell_3_casts": 12,
        "spell_4_casts": 8,
        "summoner_1_casts": 2,
        "summoner_1_id": 4,
        "summoner_2_casts": 1,
        "summoner_2_id": 7,
        # Structure stats
        "inhibitor_takedowns": 1,
        "inhibitors_lost": 0,
        "nexus_takedowns": 1,
        "nexus_lost": 0,
        "turret_takedowns": 3,
        "turrets_lost": 2,
        # Objectives
        "objectives_stolen": 0,
        "objectives_stolen_assists": 1,
        # Game state
        "bounty_level": 0,
        "champ_experience": 18500,
        "champion_transform": 0,
        "consumables_purchased": 12,
        "eligible_for_progression": True,
        "first_blood_assist": False,
        "first_blood_kill": False,
        "first_tower_assist": True,
        "first_tower_kill": False,
        "game_ended_in_early_surrender": False,
        "game_ended_in_surrender": False,
        "items_purchased": 18,
        "placement": 0,
        "profile_icon": 1,
        "summoner_id": "test_summoner_id",
        "summoner_level": 150,
        "team_early_surrendered": False,
    }

    # Apply any overrides
    defaults.update(overrides)
    return Participant(**defaults)


class TestMatchModels:
    """Test match-related models."""

    async def test_match_from_api_response(self, real_client: "NexarClient") -> None:
        """Test Match creation from real API response."""
        player = await real_client.get_player("bexli", "bex")
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

        # Test iteration
        participant_names = []
        for participant in match:
            participant_names.append(participant.game_name)

        assert participant_names == ["BluePlayer", "RedPlayer"]
