"""Unit tests for TeamInfo and TeamsInfo models."""

from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from nexar.enums import MapId, MatchParticipantPosition, PlatformId, Queue
from nexar.models.match.challenges import Challenges, Missions
from nexar.models.match.participant import Participant
from nexar.models.match.perks import PerkStats, Perks
from nexar.models.match.team import (
    Ban,
    Objective,
    Objectives,
    Team,
    TeamInfo,
    TeamsInfo,
)


def _make_participant(
    puuid: str,
    team_id: int,
    participant_id: int,
    *,
    kills: int = 0,
    deaths: int = 0,
    assists: int = 0,
    total_damage_dealt_to_champions: int = 0,
    total_damage_taken: int = 0,
    gold_earned: int = 0,
    vision_score: int = 0,
    win: bool = True,
    champion_id: int = 1,
    champion_name: str = "Annie",
    game_name: str = "Player",
    tagline: str = "TAG",
) -> Participant:
    return Participant(
        puuid=puuid,
        _summoner_name=game_name,
        champion_id=champion_id,
        champion_name=champion_name,
        team_id=team_id,
        participant_id=participant_id,
        kills=kills,
        deaths=deaths,
        assists=assists,
        champion_level=18,
        gold_earned=gold_earned,
        gold_spent=0,
        vision_score=vision_score,
        win=win,
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
        double_kills=0,
        dragon_kills=0,
        inhibitor_kills=0,
        killing_sprees=0,
        largest_killing_spree=0,
        largest_multi_kill=0,
        nexus_kills=0,
        penta_kills=0,
        quadra_kills=0,
        triple_kills=0,
        turret_kills=0,
        unreal_kills=0,
        damage_dealt_to_buildings=0,
        damage_dealt_to_objectives=0,
        damage_dealt_to_turrets=0,
        damage_self_mitigated=0,
        largest_critical_strike=0,
        magic_damage_dealt=0,
        magic_damage_dealt_to_champions=0,
        magic_damage_taken=0,
        physical_damage_dealt=0,
        physical_damage_dealt_to_champions=0,
        physical_damage_taken=0,
        total_damage_dealt=0,
        total_damage_dealt_to_champions=total_damage_dealt_to_champions,
        total_damage_shielded_on_teammates=0,
        total_damage_taken=total_damage_taken,
        true_damage_dealt=0,
        true_damage_dealt_to_champions=0,
        true_damage_taken=0,
        neutral_minions_killed=0,
        total_ally_jungle_minions_killed=0,
        total_enemy_jungle_minions_killed=0,
        total_minions_killed=0,
        total_heal=0,
        total_heals_on_teammates=0,
        total_units_healed=0,
        longest_time_spent_living=0,
        time_ccing_others=0,
        time_played=0,
        total_time_cc_dealt=0,
        total_time_spent_dead=0,
        detector_wards_placed=0,
        sight_wards_bought_in_game=0,
        vision_wards_bought_in_game=0,
        wards_killed=0,
        wards_placed=0,
        spell_1_casts=0,
        spell_2_casts=0,
        spell_3_casts=0,
        spell_4_casts=0,
        summoner_1_casts=0,
        summoner_1_id=0,
        summoner_2_casts=0,
        summoner_2_id=0,
        inhibitor_takedowns=0,
        inhibitors_lost=0,
        nexus_takedowns=0,
        nexus_lost=0,
        turret_takedowns=0,
        turrets_lost=0,
        objectives_stolen=0,
        objectives_stolen_assists=0,
        bounty_level=0,
        champ_experience=0,
        champion_transform=0,
        consumables_purchased=0,
        eligible_for_progression=False,
        first_blood_assist=False,
        first_blood_kill=False,
        first_tower_assist=False,
        first_tower_kill=False,
        game_ended_in_early_surrender=False,
        game_ended_in_surrender=False,
        items_purchased=0,
        placement=0,
        profile_icon=0,
        summoner_id="",
        summoner_level=0,
        team_early_surrendered=False,
        perks=Perks(stat_perks=PerkStats(defense=0, flex=0, offense=0), styles=[]),
        challenges=Challenges(),
        missions=Missions(),
        game_name=game_name,
        tagline=tagline,
    )


class TestTeamInfo:
    def _make_team_info(self) -> TeamInfo:
        p1 = _make_participant(
            "puuid1", 100, 1,
            kills=5, deaths=2, assists=10,
            total_damage_dealt_to_champions=20000,
            total_damage_taken=15000,
            gold_earned=13000,
            vision_score=30,
        )
        p2 = _make_participant(
            "puuid2", 100, 2,
            kills=3, deaths=1, assists=8,
            total_damage_dealt_to_champions=15000,
            total_damage_taken=12000,
            gold_earned=11000,
            vision_score=25,
        )
        return TeamInfo(
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
            participants=[p1, p2],
        )

    def test_total_damage(self) -> None:
        info = self._make_team_info()
        assert info.total_damage == 35000  # 20000 + 15000

    def test_total_damage_taken(self) -> None:
        info = self._make_team_info()
        assert info.total_damage_taken == 27000  # 15000 + 12000

    def test_total_gold_earned(self) -> None:
        info = self._make_team_info()
        assert info.total_gold_earned == 24000  # 13000 + 11000

    def test_total_kills(self) -> None:
        info = self._make_team_info()
        assert info.total_kills == 8  # 5 + 3

    def test_total_deaths(self) -> None:
        info = self._make_team_info()
        assert info.total_deaths == 3  # 2 + 1

    def test_total_assists(self) -> None:
        info = self._make_team_info()
        assert info.total_assists == 18  # 10 + 8

    def test_total_vision_score(self) -> None:
        info = self._make_team_info()
        assert info.total_vision_score == 55  # 30 + 25

    def test_empty_participants(self) -> None:
        info = TeamInfo(
            team_id=100,
            win=True,
            bans=[],
            objectives=Objectives(
                baron=Objective(first=False, kills=0),
                champion=Objective(first=False, kills=0),
                dragon=Objective(first=False, kills=0),
                horde=Objective(first=False, kills=0),
                inhibitor=Objective(first=False, kills=0),
                rift_herald=Objective(first=False, kills=0),
                tower=Objective(first=False, kills=0),
            ),
            participants=[],
        )
        assert info.total_damage == 0
        assert info.total_kills == 0
        assert info.total_gold_earned == 0

    def test_from_api_response(self) -> None:
        team_data = {
            "teamId": 100,
            "win": True,
            "bans": [],
            "objectives": {
                "baron": {"first": True, "kills": 1},
                "champion": {"first": True, "kills": 10},
                "dragon": {"first": False, "kills": 2},
                "horde": {"first": False, "kills": 0},
                "inhibitor": {"first": True, "kills": 1},
                "riftHerald": {"first": True, "kills": 1},
                "tower": {"first": False, "kills": 5},
            },
        }
        team = Team.from_api_response(team_data)
        assert team.team_id == 100
        assert team.win is True
        assert isinstance(team.bans, list)
        assert isinstance(team.objectives, Objectives)
        assert team.objectives.baron.kills == 1

    def test_ban_from_api_response(self) -> None:
        ban = Ban.from_api_response({"championId": 238, "pickTurn": 1})
        assert ban.champion_id == 238
        assert ban.pick_turn == 1

    def test_objective_from_api_response(self) -> None:
        obj = Objective.from_api_response({"first": True, "kills": 3})
        assert obj.first is True
        assert obj.kills == 3


class TestTeamsInfo:
    def _make_teams_info(self) -> TeamsInfo:
        p1 = _make_participant("puuid1", 100, 1, kills=1, win=True)
        p2 = _make_participant("puuid2", 200, 6, kills=1, win=False)
        return TeamsInfo(
            blue=TeamInfo(
                team_id=100, win=True, bans=[], objectives=Objectives(
                    baron=Objective(first=True, kills=1),
                    champion=Objective(first=True, kills=5),
                    dragon=Objective(first=False, kills=0),
                    horde=Objective(first=False, kills=0),
                    inhibitor=Objective(first=False, kills=0),
                    rift_herald=Objective(first=False, kills=0),
                    tower=Objective(first=False, kills=0),
                ),
                participants=[p1],
            ),
            red=TeamInfo(
                team_id=200, win=False, bans=[], objectives=Objectives(
                    baron=Objective(first=False, kills=0),
                    champion=Objective(first=False, kills=5),
                    dragon=Objective(first=False, kills=0),
                    horde=Objective(first=False, kills=0),
                    inhibitor=Objective(first=False, kills=0),
                    rift_herald=Objective(first=False, kills=0),
                    tower=Objective(first=False, kills=0),
                ),
                participants=[p2],
            ),
        )

    def test_iteration(self) -> None:
        info = self._make_teams_info()
        teams = list(info)
        assert len(teams) == 2
        assert teams[0].team_id == 100
        assert teams[0].win is True
        assert teams[1].team_id == 200
        assert teams[1].win is False

    def test_blue_red_access(self) -> None:
        info = self._make_teams_info()
        assert info.blue.team_id == 100
        assert info.red.team_id == 200

    def test_frozen(self) -> None:
        info = self._make_teams_info()
        with pytest.raises(FrozenInstanceError):
            info.blue = info.red  # type: ignore[misc]
