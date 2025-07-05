"""Tests for match models."""

from datetime import datetime

import pytest

from nexar.enums import MapId, MatchParticipantPosition, PlatformId, QueueId
from nexar.models import (
    Ban,
    Challenges,
    Match,
    MatchInfo,
    MatchMetadata,
    Objective,
    Objectives,
    Participant,
    Team,
    TeamInfo,
    TeamsInfo,
)


def create_test_participant(**overrides) -> Participant:
    """Create a participant with all required fields for testing."""
    defaults = {
        # Core participant data
        "puuid": "test_player",
        "_summoner_name": "TestPlayer",
        "riot_id_game_name": "TestPlayer",
        "riot_id_tagline": "TST",
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

    @pytest.mark.skip(
        reason="Requires specific match ID - implement when match history endpoint is added",
    )
    def test_match_from_api_response(self):
        """Test Match creation from real API response."""
        # TODO: Implement when we add match history endpoints to get real match IDs

    def test_ban_creation(self):
        """Test Ban model can be created directly."""
        ban = Ban(champion_id=238, pick_turn=1)

        assert ban.champion_id == 238
        assert ban.pick_turn == 1

    def test_objective_creation(self):
        """Test Objective model can be created directly."""
        objective = Objective(first=True, kills=1)

        assert objective.first is True
        assert objective.kills == 1

    def test_challenges_creation(self):
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

    def test_objectives_creation(self):
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

    def test_match_teams_property(self):
        """Test Match.teams property returns TeamsInfo with blue and red teams."""
        # Create test participants
        blue_participant = create_test_participant(
            puuid="blue_player",
            riot_id_game_name="BluePlayer",
            riot_id_tagline="BLU",
            champion_id=1,
            champion_name="Annie",
            team_id=100,  # Blue team
            participant_id=1,
            total_damage_dealt_to_champions=20000,
            total_damage_taken=15000,
            win=True,
        )

        red_participant = create_test_participant(
            puuid="red_player",
            riot_id_game_name="RedPlayer",
            riot_id_tagline="RED",
            champion_id=2,
            champion_name="Olaf",
            team_id=200,  # Red team
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

        blue_team = Team(
            team_id=100,
            win=True,
            bans=[],
            objectives=Objectives(
                baron=Objective(first=True, kills=1),
                champion=Objective(first=True, kills=20),
                dragon=Objective(first=True, kills=3),
                horde=Objective(first=False, kills=0),
                inhibitor=Objective(first=True, kills=2),
                rift_herald=Objective(first=True, kills=1),
                tower=Objective(first=True, kills=8),
            ),
        )

        red_team = Team(
            team_id=200,
            win=False,
            bans=[],
            objectives=Objectives(
                baron=Objective(first=False, kills=0),
                champion=Objective(first=False, kills=15),
                dragon=Objective(first=False, kills=1),
                horde=Objective(first=False, kills=0),
                inhibitor=Objective(first=False, kills=1),
                rift_herald=Objective(first=False, kills=0),
                tower=Objective(first=False, kills=3),
            ),
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
            queue_id=QueueId.RANKED_SOLO_5x5,
            participants=[blue_participant, red_participant],
            teams=[blue_team, red_team],
        )

        match_metadata = MatchMetadata(
            data_version="2",
            match_id="NA1_1234567890",
            participants=["blue_player", "red_player"],
        )

        match = Match(metadata=match_metadata, info=match_info)

        # Test teams property
        teams = match.teams
        assert isinstance(teams, TeamsInfo)
        assert isinstance(teams.blue, TeamInfo)
        assert isinstance(teams.red, TeamInfo)

        # Test blue team
        assert teams.blue.team_id == 100
        assert teams.blue.win is True
        assert len(teams.blue.participants) == 1
        assert teams.blue.participants[0].riot_id_game_name == "BluePlayer"

        # Test red team
        assert teams.red.team_id == 200
        assert teams.red.win is False
        assert len(teams.red.participants) == 1
        assert teams.red.participants[0].riot_id_game_name == "RedPlayer"

    def test_team_info_aggregated_stats(self):
        """Test TeamInfo aggregated statistics properties."""
        participants = [
            create_test_participant(
                puuid="player1",
                riot_id_game_name="Player1",
                riot_id_tagline="P1",
                champion_id=1,
                champion_name="Annie",
                team_id=100,
                participant_id=1,
                kills=5,
                deaths=2,
                assists=10,
                champion_level=18,
                gold_earned=15000,
                gold_spent=14000,
                total_damage_dealt_to_champions=20000,
                total_damage_taken=15000,
                vision_score=30,
                individual_position=MatchParticipantPosition.MIDDLE,
                team_position=MatchParticipantPosition.MIDDLE,
                lane="MIDDLE",
                role="SOLO",
                win=True,
            ),
            create_test_participant(
                puuid="player2",
                riot_id_game_name="Player2",
                riot_id_tagline="P2",
                champion_id=2,
                champion_name="Olaf",
                team_id=100,
                participant_id=2,
                kills=3,
                deaths=1,
                assists=8,
                champion_level=16,
                gold_earned=12000,
                gold_spent=11000,
                total_damage_dealt_to_champions=18000,
                total_damage_taken=12000,
                vision_score=25,
                individual_position=MatchParticipantPosition.JUNGLE,
                team_position=MatchParticipantPosition.JUNGLE,
                lane="JUNGLE",
                role="NONE",
                win=True,
            ),
        ]

        team_info = TeamInfo(
            team_id=100,
            win=True,
            bans=[],
            objectives=Objectives(
                baron=Objective(first=True, kills=1),
                champion=Objective(first=True, kills=20),
                dragon=Objective(first=True, kills=3),
                horde=Objective(first=False, kills=0),
                inhibitor=Objective(first=True, kills=2),
                rift_herald=Objective(first=True, kills=1),
                tower=Objective(first=True, kills=8),
            ),
            participants=participants,
        )

        # Test aggregated stats
        assert team_info.total_damage == 38000  # 20000 + 18000
        assert team_info.total_damage_taken == 27000  # 15000 + 12000
        assert team_info.total_gold_earned == 27000  # 15000 + 12000
        assert team_info.total_kills == 8  # 5 + 3
        assert team_info.total_deaths == 3  # 2 + 1
        assert team_info.total_assists == 18  # 10 + 8
        assert team_info.total_vision_score == 55  # 30 + 25

    def test_match_iteration(self):
        """Test that Match is iterable over participants."""
        blue_participant = create_test_participant(
            puuid="blue_player",
            riot_id_game_name="BluePlayer",
            riot_id_tagline="BLU",
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
            riot_id_game_name="RedPlayer",
            riot_id_tagline="RED",
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
            queue_id=QueueId.RANKED_SOLO_5x5,
            participants=[blue_participant, red_participant],
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
            participant_names.append(participant.riot_id_game_name)

        assert participant_names == ["BluePlayer", "RedPlayer"]

    def test_teams_info_iteration(self):
        """Test that TeamsInfo is iterable over teams."""
        blue_team = TeamInfo(
            team_id=100,
            win=True,
            bans=[],
            objectives=Objectives(
                baron=Objective(first=True, kills=1),
                champion=Objective(first=True, kills=20),
                dragon=Objective(first=True, kills=3),
                horde=Objective(first=False, kills=0),
                inhibitor=Objective(first=True, kills=2),
                rift_herald=Objective(first=True, kills=1),
                tower=Objective(first=True, kills=8),
            ),
            participants=[],
        )

        red_team = TeamInfo(
            team_id=200,
            win=False,
            bans=[],
            objectives=Objectives(
                baron=Objective(first=False, kills=0),
                champion=Objective(first=False, kills=15),
                dragon=Objective(first=False, kills=1),
                horde=Objective(first=False, kills=0),
                inhibitor=Objective(first=False, kills=1),
                rift_herald=Objective(first=False, kills=0),
                tower=Objective(first=False, kills=3),
            ),
            participants=[],
        )

        teams_info = TeamsInfo(blue=blue_team, red=red_team)

        # Test iteration
        team_ids = []
        for team in teams_info:
            team_ids.append(team.team_id)

        assert team_ids == [100, 200]
