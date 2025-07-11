"""Tests for ParticipantList functionality."""

import pytest

from nexar.enums import MatchParticipantPosition
from nexar.models.match.participant import Participant
from nexar.models.match.participant_list import ParticipantList


class TestParticipantList:
    """Test ParticipantList filtering and utility methods."""

    @pytest.fixture
    def sample_participants(self) -> list[Participant]:
        """Create sample participants for testing."""
        # Note: Using minimal required fields for testing
        return [
            Participant(
                puuid="player1",
                _summoner_name="Player1",
                champion_id=1,
                champion_name="Annie",
                team_id=100,
                participant_id=1,
                kills=5,
                deaths=2,
                assists=8,
                champion_level=18,
                gold_earned=12000,
                gold_spent=11000,
                vision_score=15,
                win=True,
                item_0=0,
                item_1=0,
                item_2=0,
                item_3=0,
                item_4=0,
                item_5=0,
                item_6=0,
                individual_position=MatchParticipantPosition.MIDDLE,
                team_position=MatchParticipantPosition.MIDDLE,
                lane="MIDDLE",
                role="SOLO",
                all_in_pings=0,
                assist_me_pings=0,
                command_pings=0,
                enemy_missing_pings=0,
                enemy_vision_pings=0,
                get_back_pings=0,
                hold_pings=0,
                need_vision_pings=0,
                on_my_way_pings=0,
                push_pings=0,
                vision_cleared_pings=0,
                baron_kills=0,
                double_kills=1,
                dragon_kills=0,
                inhibitor_kills=0,
                killing_sprees=1,
                largest_killing_spree=3,
                largest_multi_kill=2,
                nexus_kills=0,
                penta_kills=0,
                quadra_kills=0,
                triple_kills=0,
                turret_kills=1,
                unreal_kills=0,
                damage_dealt_to_buildings=1000,
                damage_dealt_to_objectives=500,
                damage_dealt_to_turrets=800,
                damage_self_mitigated=5000,
                largest_critical_strike=1200,
                magic_damage_dealt=8000,
                magic_damage_dealt_to_champions=6000,
                magic_damage_taken=4000,
                physical_damage_dealt=12000,
                physical_damage_dealt_to_champions=9000,
                physical_damage_taken=8000,
                total_damage_dealt=20000,
                total_damage_dealt_to_champions=15000,
                total_damage_shielded_on_teammates=1000,
                total_damage_taken=12000,
                true_damage_dealt=500,
                true_damage_dealt_to_champions=0,
                true_damage_taken=200,
                neutral_minions_killed=50,
                total_ally_jungle_minions_killed=5,
                total_enemy_jungle_minions_killed=10,
                total_minions_killed=150,
                total_heal=3000,
                total_heals_on_teammates=1500,
                total_units_healed=8,
                longest_time_spent_living=300,
                time_ccing_others=25,
                time_played=1800,
                total_time_cc_dealt=30,
                total_time_spent_dead=45,
                detector_wards_placed=2,
                sight_wards_bought_in_game=0,
                vision_wards_bought_in_game=5,
                wards_killed=8,
                wards_placed=15,
                spell_1_casts=45,
                spell_2_casts=30,
                spell_3_casts=25,
                spell_4_casts=8,
                summoner_1_casts=3,
                summoner_1_id=4,
                summoner_2_casts=2,
                summoner_2_id=7,
                inhibitor_takedowns=1,
                inhibitors_lost=0,
                nexus_takedowns=1,
                nexus_lost=0,
                turret_takedowns=3,
                turrets_lost=1,
                objectives_stolen=0,
                objectives_stolen_assists=0,
                champ_experience=18000,
                champion_transform=0,
                consumables_purchased=15,
                eligible_for_progression=True,
                first_blood_assist=False,
                first_blood_kill=False,
                first_tower_assist=False,
                first_tower_kill=False,
                game_ended_in_early_surrender=False,
                game_ended_in_surrender=False,
                items_purchased=8,
                placement=1,
                profile_icon=1234,
                summoner_id="summoner1",
                summoner_level=150,
                team_early_surrendered=False,
                game_name="Player1",
                tagline="NA1",
            ),
            Participant(
                puuid="player2",
                _summoner_name="Player2",
                champion_id=2,
                champion_name="Olaf",
                team_id=100,
                participant_id=2,
                kills=8,
                deaths=3,
                assists=4,
                champion_level=17,
                gold_earned=13000,
                gold_spent=12500,
                vision_score=8,
                win=True,
                item_0=0,
                item_1=0,
                item_2=0,
                item_3=0,
                item_4=0,
                item_5=0,
                item_6=0,
                individual_position=MatchParticipantPosition.JUNGLE,
                team_position=MatchParticipantPosition.JUNGLE,
                lane="JUNGLE",
                role="NONE",
                all_in_pings=0,
                assist_me_pings=0,
                command_pings=0,
                enemy_missing_pings=0,
                enemy_vision_pings=0,
                get_back_pings=0,
                hold_pings=0,
                need_vision_pings=0,
                on_my_way_pings=0,
                push_pings=0,
                vision_cleared_pings=0,
                baron_kills=1,
                double_kills=2,
                dragon_kills=2,
                inhibitor_kills=0,
                killing_sprees=2,
                largest_killing_spree=5,
                largest_multi_kill=2,
                nexus_kills=0,
                penta_kills=0,
                quadra_kills=0,
                triple_kills=0,
                turret_kills=2,
                unreal_kills=0,
                damage_dealt_to_buildings=2000,
                damage_dealt_to_objectives=3000,
                damage_dealt_to_turrets=1200,
                damage_self_mitigated=6000,
                largest_critical_strike=1500,
                magic_damage_dealt=5000,
                magic_damage_dealt_to_champions=4000,
                magic_damage_taken=3500,
                physical_damage_dealt=15000,
                physical_damage_dealt_to_champions=14000,
                physical_damage_taken=9000,
                total_damage_dealt=20000,
                total_damage_dealt_to_champions=18000,
                total_damage_shielded_on_teammates=500,
                total_damage_taken=12500,
                true_damage_dealt=800,
                true_damage_dealt_to_champions=100,
                true_damage_taken=300,
                neutral_minions_killed=80,
                total_ally_jungle_minions_killed=10,
                total_enemy_jungle_minions_killed=15,
                total_minions_killed=120,
                total_heal=2500,
                total_heals_on_teammates=1000,
                total_units_healed=5,
                longest_time_spent_living=450,
                time_ccing_others=35,
                time_played=1800,
                total_time_cc_dealt=40,
                total_time_spent_dead=30,
                detector_wards_placed=3,
                sight_wards_bought_in_game=0,
                vision_wards_bought_in_game=7,
                wards_killed=12,
                wards_placed=18,
                spell_1_casts=50,
                spell_2_casts=35,
                spell_3_casts=30,
                spell_4_casts=10,
                summoner_1_casts=4,
                summoner_1_id=11,
                summoner_2_casts=3,
                summoner_2_id=4,
                inhibitor_takedowns=0,
                inhibitors_lost=0,
                nexus_takedowns=1,
                nexus_lost=0,
                turret_takedowns=4,
                turrets_lost=1,
                objectives_stolen=1,
                objectives_stolen_assists=1,
                champ_experience=17500,
                champion_transform=0,
                consumables_purchased=18,
                eligible_for_progression=True,
                first_blood_assist=False,
                first_blood_kill=True,
                first_tower_assist=False,
                first_tower_kill=False,
                game_ended_in_early_surrender=False,
                game_ended_in_surrender=False,
                items_purchased=10,
                placement=2,
                profile_icon=2345,
                summoner_id="summoner2",
                summoner_level=145,
                team_early_surrendered=False,
                game_name="Player2",
                tagline="NA1",
            ),
            Participant(
                puuid="player3",
                _summoner_name="Player3",
                champion_id=3,
                champion_name="Jinx",
                team_id=200,
                participant_id=6,
                kills=12,
                deaths=4,
                assists=6,
                champion_level=18,
                gold_earned=15000,
                gold_spent=14500,
                vision_score=12,
                win=False,
                item_0=0,
                item_1=0,
                item_2=0,
                item_3=0,
                item_4=0,
                item_5=0,
                item_6=0,
                individual_position=MatchParticipantPosition.BOTTOM,
                team_position=MatchParticipantPosition.BOTTOM,
                lane="BOTTOM",
                role="DUO_CARRY",
                all_in_pings=0,
                assist_me_pings=0,
                command_pings=0,
                enemy_missing_pings=0,
                enemy_vision_pings=0,
                get_back_pings=0,
                hold_pings=0,
                need_vision_pings=0,
                on_my_way_pings=0,
                push_pings=0,
                vision_cleared_pings=0,
                baron_kills=0,
                double_kills=3,
                dragon_kills=0,
                inhibitor_kills=1,
                killing_sprees=3,
                largest_killing_spree=8,
                largest_multi_kill=3,
                nexus_kills=0,
                penta_kills=0,
                quadra_kills=0,
                triple_kills=1,
                turret_kills=3,
                unreal_kills=0,
                damage_dealt_to_buildings=4000,
                damage_dealt_to_objectives=1500,
                damage_dealt_to_turrets=2500,
                damage_self_mitigated=7000,
                largest_critical_strike=2000,
                magic_damage_dealt=3000,
                magic_damage_dealt_to_champions=2000,
                magic_damage_taken=5000,
                physical_damage_dealt=22000,
                physical_damage_dealt_to_champions=23000,
                physical_damage_taken=10000,
                total_damage_dealt=25000,
                total_damage_dealt_to_champions=25000,
                total_damage_shielded_on_teammates=200,
                total_damage_taken=15000,
                true_damage_dealt=100,
                true_damage_dealt_to_champions=0,
                true_damage_taken=100,
                neutral_minions_killed=20,
                total_ally_jungle_minions_killed=2,
                total_enemy_jungle_minions_killed=5,
                total_minions_killed=200,
                total_heal=2000,
                total_heals_on_teammates=500,
                total_units_healed=3,
                longest_time_spent_living=500,
                time_ccing_others=15,
                time_played=1800,
                total_time_cc_dealt=20,
                total_time_spent_dead=60,
                detector_wards_placed=1,
                sight_wards_bought_in_game=0,
                vision_wards_bought_in_game=3,
                wards_killed=5,
                wards_placed=10,
                spell_1_casts=60,
                spell_2_casts=40,
                spell_3_casts=35,
                spell_4_casts=12,
                summoner_1_casts=2,
                summoner_1_id=7,
                summoner_2_casts=4,
                summoner_2_id=4,
                inhibitor_takedowns=2,
                inhibitors_lost=1,
                nexus_takedowns=0,
                nexus_lost=1,
                turret_takedowns=5,
                turrets_lost=3,
                objectives_stolen=0,
                objectives_stolen_assists=1,
                champ_experience=18000,
                champion_transform=0,
                consumables_purchased=20,
                eligible_for_progression=True,
                first_blood_assist=True,
                first_blood_kill=False,
                first_tower_assist=True,
                first_tower_kill=False,
                game_ended_in_early_surrender=False,
                game_ended_in_surrender=False,
                items_purchased=12,
                placement=6,
                profile_icon=3456,
                summoner_id="summoner3",
                summoner_level=140,
                team_early_surrendered=False,
                game_name="Player3",
                tagline="NA1",
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
        """Test filtering by team."""
        blue_team = participant_list.by_team(100)
        assert len(blue_team) == 2
        assert all(p.team_id == 100 for p in blue_team)

        red_team = participant_list.by_team(200)
        assert len(red_team) == 1
        assert red_team[0].team_id == 200

    def test_blue_red_team_shortcuts(self, participant_list: ParticipantList) -> None:
        """Test blue and red team shortcut methods."""
        blue_team = participant_list.blue_team()
        assert len(blue_team) == 2
        assert all(p.team_id == 100 for p in blue_team)

        red_team = participant_list.red_team()
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
        """Test getting highest KDA participants."""
        top_kda = participant_list.highest_kda(count=2)
        assert len(top_kda) == 2
        # Annie should have the highest KDA: (5+8)/2 = 6.5
        # Jinx has KDA: (12+6)/4 = 4.5
        assert top_kda[0].champion_name == "Annie"

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
