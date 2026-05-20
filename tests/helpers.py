"""Shared test helpers for Nexar test suite."""

from datetime import datetime
from typing import Any

from nexar.enums import MapId, MatchParticipantPosition, PlatformId, Queue
from nexar.models.match.challenges import Challenges, Missions
from nexar.models.match.match import Match, MatchInfo, MatchMetadata
from nexar.models.match.participant import Participant
from nexar.models.match.participant_list import ParticipantList
from nexar.models.match.perks import Perks, PerkStats
from nexar.rate_limiter import PERSONAL_LIMITS, RateLimiter, RateLimitRecord


class MockRateLimiter:
    """Wraps RateLimiter to expose internal state for testing."""

    def __init__(
        self,
        app_limits: tuple[tuple[int, int], ...] = PERSONAL_LIMITS,
        safety_margin: float = 0.01,
    ) -> None:
        self._inner = RateLimiter(app_limits, safety_margin)

    @property
    def limits(self) -> dict[str, dict[str, RateLimitRecord]]:
        return self._inner._limits

    async def acquire(self, region: str, method: str) -> None:
        await self._inner.acquire(region, method)

    async def update_from_headers(self, headers: dict[str, str], region: str, method: str) -> None:
        await self._inner.update_from_headers(headers, region, method)

    def detect_rate_limit_type(self, headers: dict[str, str]) -> tuple[str, bool]:
        return self._inner._detect_rate_limit_type(headers)


def create_test_participant(**overrides: object) -> Participant:
    """Create a participant with all required fields for testing."""
    defaults: dict[str, Any] = {
        "puuid": "test_player",
        "_summoner_name": "TestPlayer",
        "game_name": "TestPlayer",
        "tagline": "TST",
        "champion_id": 1,
        "champion_name": "Annie",
        "team_id": 100,
        "participant_id": 1,
        "kills": 5,
        "deaths": 2,
        "assists": 10,
        "champion_level": 18,
        "gold_earned": 15000,
        "gold_spent": 14000,
        "vision_score": 30,
        "win": True,
        "item_0": 1001,
        "item_1": 1001,
        "item_2": 1001,
        "item_3": 1001,
        "item_4": 1001,
        "item_5": 1001,
        "item_6": 3340,
        "individual_position": MatchParticipantPosition.MIDDLE,
        "team_position": MatchParticipantPosition.MIDDLE,
        "lane": "MIDDLE",
        "role": "SOLO",
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
        "neutral_minions_killed": 120,
        "total_ally_jungle_minions_killed": 15,
        "total_enemy_jungle_minions_killed": 10,
        "total_minions_killed": 180,
        "total_heal": 3000,
        "total_heals_on_teammates": 1500,
        "total_units_healed": 8,
        "longest_time_spent_living": 1200,
        "time_ccing_others": 45,
        "time_played": 1800,
        "total_time_cc_dealt": 15,
        "total_time_spent_dead": 60,
        "detector_wards_placed": 2,
        "sight_wards_bought_in_game": 0,
        "vision_wards_bought_in_game": 3,
        "wards_killed": 8,
        "wards_placed": 15,
        "spell_1_casts": 25,
        "spell_2_casts": 18,
        "spell_3_casts": 12,
        "spell_4_casts": 8,
        "summoner_1_casts": 2,
        "summoner_1_id": 4,
        "summoner_2_casts": 1,
        "summoner_2_id": 7,
        "inhibitor_takedowns": 1,
        "inhibitors_lost": 0,
        "nexus_takedowns": 1,
        "nexus_lost": 0,
        "turret_takedowns": 3,
        "turrets_lost": 2,
        "objectives_stolen": 0,
        "objectives_stolen_assists": 1,
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
        "perks": Perks(stat_perks=PerkStats(defense=0, flex=0, offense=0), styles=[]),
        "challenges": Challenges(),
        "missions": Missions(),
        "game_name": "TestPlayer",
        "tagline": "TST",
    }
    defaults.update(overrides)
    return Participant(**defaults)


def create_test_match(
    match_id: str,
    puuid: str = "test_player",
    *,
    game_id: int = 12345,
    game_duration: int = 1800,
    participant: Participant | None = None,
) -> Match:
    p = participant or create_test_participant(puuid=puuid)
    info = MatchInfo(
        game_creation=datetime.fromtimestamp(1234567890),
        game_duration=game_duration,
        game_id=game_id,
        game_mode="CLASSIC",
        game_start_timestamp=datetime.fromtimestamp(1234567890),
        game_type="MATCHED_GAME",
        game_version="14.1.1",
        map_id=MapId.SUMMONERS_RIFT,
        platform_id=PlatformId.NA1,
        queue_id=Queue.RANKED_SOLO_5x5,
        participants=ParticipantList([p]),
        teams=[],
    )
    metadata = MatchMetadata(
        data_version="2",
        match_id=match_id,
        participants=[p.puuid],
    )
    return Match(metadata=metadata, info=info)
