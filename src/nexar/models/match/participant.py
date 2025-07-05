"""Participant-related models."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ...enums import MatchParticipantPosition

if TYPE_CHECKING:
    from .challenges import Challenges, Missions
    from .perks import Perks


@dataclass(frozen=True)
class Participant:
    """Represents a match participant."""

    # Core participant data
    puuid: str
    """Player's universally unique identifier."""

    _summoner_name: str
    """
    Player's summoner name at the time of the match.
    
    **Deprecated by Riot.** Use `Participant.riot_id_game_name` instead.
    """

    champion_id: int
    """
    Unique identifier for the champion played.
    
    Riot docs:
    > Prior to patch 11.4, on Feb 18th, 2021, this field returned invalid championIds.
    We recommend determining the champion based on the championName field for matches played prior
    to patch 11.4.

    **Use champion_name instead of deriving champion name from ID**
    """

    champion_name: str
    """
    Name of the champion played.
    
    **Use this over champion_id**
    """

    team_id: int
    """Team identifier (100 for blue side, 200 for red side)."""

    @property
    def team_color(self):
        """Team color. Colloquially players use the terms "blue side" or "red side"."""
        return "Blue" if self.team_id == 100 else "Red"

    @property
    def summoner_name(self) -> str:
        """
        Player's summoner name at the time of the match.

        **Deprecated by Riot.** Use `Participant.riot_id_game_name` instead.
        """
        return self._summoner_name

    participant_id: int
    """Participant's position in the match (1-10)."""

    # Basic stats
    kills: int
    """Number of enemy champions killed."""

    deaths: int
    """Number of times the participant died."""

    assists: int
    """Number of assists on enemy champion kills."""

    def kda(self, *, as_str: bool = False) -> tuple[int, int, int] | str:
        """
        Get kills, deaths, and assists.

        Args:
            as_str: If True, returns formatted string like "5/2/10". If False, returns tuple.
        """
        if as_str:
            return f"{self.kills}/{self.deaths}/{self.assists}"
        return (self.kills, self.deaths, self.assists)

    champion_level: int
    """Final champion level achieved."""

    gold_earned: int
    """Total gold earned during the match."""

    gold_spent: int
    """Total gold spent on items."""

    vision_score: int
    """Vision score based on wards placed, cleared, etc."""

    win: bool
    """Whether the participant's team won the match."""

    # Items
    item_0: int
    """Item in slot 0 (item ID, 0 if empty)."""

    item_1: int
    """Item in slot 1 (item ID, 0 if empty)."""

    item_2: int
    """Item in slot 2 (item ID, 0 if empty)."""

    item_3: int
    """Item in slot 3 (item ID, 0 if empty)."""

    item_4: int
    """Item in slot 4 (item ID, 0 if empty)."""

    item_5: int
    """Item in slot 5 (item ID, 0 if empty)."""

    item_6: int
    """Trinket item (item ID, 0 if empty)."""

    # Position and role
    individual_position: MatchParticipantPosition
    """
    Individual position assignment (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY).

    Riot API docs:
    > The individualPosition is the best guess for which position the player actually played in
    isolation of anything else.
    
    **Generally, you should use the team_position over the this.**
    """

    team_position: MatchParticipantPosition
    """
    Team-based position assignment (TOP, JUNGLE, MIDDLE, BOTTOM, UTILITY).

    Riot API docs:
    > The teamPosition is the best guess for which position the player actually played if we add
    the constraint that each team must have one top player, one jungle, one middle, etc.
    
    **Generally, you should use the this over the individual_position.**
    """

    lane: str
    """Lane assignment during the match."""

    role: str
    """Role assignment during the match."""

    # Ping stats
    all_in_pings: int
    """Number of 'all in' (Yellow crossed swords) pings used."""

    assist_me_pings: int
    """Number of 'assist me' (Green flag) pings used."""

    command_pings: int
    """Number of command (Blue generic (ALT+click)) pings used."""

    enemy_missing_pings: int
    """Number of 'enemy missing' (Yellow questionmark) pings used."""

    enemy_vision_pings: int
    """Number of 'enemy vision' (Red eyeball) pings used."""

    get_back_pings: int
    """Number of 'get back' (Yellow circle with horizontal line) pings used."""

    hold_pings: int
    """Number of 'hold' pings used."""

    need_vision_pings: int
    """Number of 'need vision' (Green ward) pings used."""

    on_my_way_pings: int
    """Number of 'on my way' (Blue arrow pointing at ground) pings used."""

    push_pings: int
    """Number of 'push' (Green minion) pings used."""

    vision_cleared_pings: int
    """Number of 'vision cleared' pings used."""

    # Kill stats
    baron_kills: int
    """Number of Baron kills."""

    double_kills: int
    """Number of double kills achieved."""

    dragon_kills: int
    """Number of Dragon kills."""

    inhibitor_kills: int
    """Number of inhibitor kills."""

    killing_sprees: int
    """Number of killing sprees achieved."""

    largest_killing_spree: int
    """Largest killing spree achieved."""

    largest_multi_kill: int
    """Largest multi-kill achieved."""

    nexus_kills: int
    """Number of Nexus kills."""

    penta_kills: int
    """Number of penta kills achieved."""

    quadra_kills: int
    """Number of quadra kills achieved."""

    triple_kills: int
    """Number of triple kills achieved."""

    turret_kills: int
    """Number of turret kills."""

    unreal_kills: int
    """TODO"""

    # Damage stats
    damage_dealt_to_buildings: int
    """Total damage dealt to buildings."""

    damage_dealt_to_objectives: int
    """Total damage dealt to objectives (Baron, Dragon, etc.)."""

    damage_dealt_to_turrets: int
    """Total damage dealt to turrets."""

    damage_self_mitigated: int
    """Total damage mitigated by shields, resistances, etc."""

    largest_critical_strike: int
    """Largest critical strike damage dealt."""

    magic_damage_dealt: int
    """Total magic damage dealt."""

    magic_damage_dealt_to_champions: int
    """Magic damage dealt to enemy champions."""

    magic_damage_taken: int
    """Total magic damage taken."""

    physical_damage_dealt: int
    """Total physical damage dealt."""

    physical_damage_dealt_to_champions: int
    """Physical damage dealt to enemy champions."""

    physical_damage_taken: int
    """Total physical damage taken."""

    total_damage_dealt: int
    """Total damage dealt (all types combined)."""

    total_damage_dealt_to_champions: int
    """Total damage dealt to enemy champions (all types combined)."""

    total_damage_shielded_on_teammates: int
    """Total damage shielded on teammates."""

    total_damage_taken: int
    """Total damage taken (all types combined)."""

    true_damage_dealt: int
    """Total true damage dealt."""

    true_damage_dealt_to_champions: int
    """True damage dealt to enemy champions."""

    true_damage_taken: int
    """Total true damage taken."""

    # Minion and jungle stats
    neutral_minions_killed: int
    """
    Number of neutral minions (jungle monsters) killed.

    This only includes standard monsters Gromp, Red/Blue Buff, etc.
    Oddly enough, it also includes Ivern's Daisy.
    
    Riot docs:
    > neutralMinionsKilled = mNeutralMinionsKilled, which is incremented on kills of kPet and
    kJungleMonster
    """

    total_ally_jungle_minions_killed: int
    """Number of allied jungle minions killed."""

    total_enemy_jungle_minions_killed: int
    """Number of enemy jungle minions killed."""

    total_minions_killed: int
    """
    Total number of minions killed (colloquially known as "CS" or "creep score").
    
    Riot docs:
    > totalMillionsKilled = mMinionsKilled, which is only incremented on kills of kTeamMinion,
    kMeleeLaneMinion, kSuperLaneMinion, kRangedLaneMinion and kSiegeLaneMinion
    """

    @property
    def creep_score(self):
        """Alias for .total_minions_killed"""
        return self.total_minions_killed

    # Healing and support stats
    total_heal: int
    """
    Total healing done.
    
    Riot docs:
    > Whenever positive health is applied (which translates to all heals in the game but not things
    like regeneration), totalHeal is incremented by the amount of health received. This includes
    healing enemies, jungle monsters, yourself, etc
    """

    total_heals_on_teammates: int
    """
    Total healing done on teammates.
    
    Riot docs:
    > Whenever positive health is applied (which translates to all heals in the game but not things
    like regeneration), totalHealsOnTeammates is incremented by the amount of health received.
    This is post modified, so if you heal someone missing 5 health for 100 you will get +5
    totalHealsOnTeammates
    """

    total_units_healed: int
    """Total number of units healed."""

    # Time stats
    longest_time_spent_living: int
    """Longest time spent alive in seconds."""

    time_ccing_others: int
    """Time spent crowd controlling enemies in seconds."""

    time_played: int
    """Total time played in the match in seconds."""

    total_time_cc_dealt: int
    """Total crowd control time dealt in seconds."""

    total_time_spent_dead: int
    """Total time spent dead in seconds."""

    # Ward and vision stats
    detector_wards_placed: int
    """Number of detector wards (control wards) placed."""

    sight_wards_bought_in_game: int
    """Number of sight wards bought."""

    vision_wards_bought_in_game: int
    """Number of vision wards bought."""

    wards_killed: int
    """Number of enemy wards destroyed."""

    wards_placed: int
    """Total number of wards placed."""

    # Spell casts
    spell_1_casts: int
    """Number of times ability Q was cast."""

    spell_2_casts: int
    """Number of times ability W was cast."""

    spell_3_casts: int
    """Number of times ability E was cast."""

    spell_4_casts: int
    """Number of times ability R (ultimate) was cast."""

    summoner_1_casts: int
    """Number of times first summoner spell was cast."""

    summoner_1_id: int
    """ID of the first summoner spell."""

    summoner_2_casts: int
    """Number of times second summoner spell was cast."""

    summoner_2_id: int
    """ID of the second summoner spell."""

    # Structure stats
    inhibitor_takedowns: int
    """Number of inhibitor takedowns participated in."""

    inhibitors_lost: int
    """Number of allied inhibitors lost."""

    nexus_takedowns: int
    """Number of Nexus takedowns participated in."""

    nexus_lost: int
    """Number of allied Nexus lost."""

    turret_takedowns: int
    """Number of turret takedowns participated in."""

    turrets_lost: int
    """Number of allied turrets lost."""

    # Objectives
    objectives_stolen: int
    """Number of objectives stolen from enemies."""

    objectives_stolen_assists: int
    """Number of assists on stolen objectives."""

    # Game state
    champ_experience: int
    """Total champion experience gained."""

    champion_transform: int
    """
    Kayn transformation and end of game.
    
    - 0 = No transformation
    - 1 = Slayer (Red)
    - 2 = Assassin (Blue)
    
    Riot docs:
    > This field is currently only utilized for Kayn's transformations.
    (Legal values: 0 - None, 1 - Slayer, 2 - Assassin)
    """

    consumables_purchased: int
    """Number of consumable items purchased."""

    eligible_for_progression: bool
    """Whether the participant is eligible for progression."""

    first_blood_assist: bool
    """Whether the participant assisted in first blood."""

    first_blood_kill: bool
    """Whether the participant got first blood."""

    first_tower_assist: bool
    """Whether the participant assisted in first tower kill."""

    first_tower_kill: bool
    """Whether the participant got first tower kill."""

    game_ended_in_early_surrender: bool
    """
    Whether the game ended in an early surrender.
    
    Riot docs:
    > This is an offshoot of the OneStone challenge. The code checks if a spell with the same
    instance ID does the final point of damage to at least 2 Champions. It doesn't matter if
    they're enemies, but you cannot hurt your friends.
    """

    game_ended_in_surrender: bool
    """Whether the game ended in a surrender."""

    items_purchased: int
    """Total number of items purchased."""

    placement: int
    """Final placement in the match."""

    profile_icon: int
    """Profile icon ID used by the participant."""

    summoner_id: str
    """Summoner ID of the participant."""

    summoner_level: int
    """Summoner level at the time of the match."""

    team_early_surrendered: bool
    """Whether the participant's team early surrendered."""

    # Riot ID
    riot_id_game_name: str | None = None
    """Riot ID game name, if available."""

    riot_id_tagline: str | None = None
    """Riot ID tagline, if available."""

    # Game state (optional)
    bounty_level: int | None = None
    """Current bounty level, if applicable."""

    # Player scores (from missions)
    player_score_0: int | None = None
    """Mission score 0, if applicable."""

    player_score_1: int | None = None
    """Mission score 1, if applicable."""

    player_score_2: int | None = None
    """Mission score 2, if applicable."""

    player_score_3: int | None = None
    """Mission score 3, if applicable."""

    player_score_4: int | None = None
    """Mission score 4, if applicable."""

    player_score_5: int | None = None
    """Mission score 5, if applicable."""

    player_score_6: int | None = None
    """Mission score 6, if applicable."""

    player_score_7: int | None = None
    """Mission score 7, if applicable."""

    player_score_8: int | None = None
    """Mission score 8, if applicable."""

    player_score_9: int | None = None
    """Mission score 9, if applicable."""

    player_score_10: int | None = None
    """Mission score 10, if applicable."""

    player_score_11: int | None = None
    """Mission score 11, if applicable."""

    # Player augments (for specific game modes)
    player_augment_1: int | None = None
    """Player augment 1, if applicable (mode-specific)."""

    player_augment_2: int | None = None
    """Player augment 2, if applicable (mode-specific)."""

    player_augment_3: int | None = None
    """Player augment 3, if applicable (mode-specific)."""

    player_augment_4: int | None = None
    """Player augment 4, if applicable (mode-specific)."""

    player_subteam_id: int | None = None
    """Player subteam ID, if applicable (mode-specific)."""

    subteam_placement: int | None = None
    """Subteam placement, if applicable (mode-specific)."""

    # Complex nested objects
    perks: "Perks | None" = None
    """Rune and perk information."""

    challenges: "Challenges | None" = None
    """Challenge completion data."""

    missions: "Missions | None" = None
    """Mission completion data."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Participant":
        """Create Participant from API response."""
        from .challenges import Challenges, Missions
        from .perks import Perks

        return cls(
            # Core participant data
            puuid=data["puuid"],
            _summoner_name=data["summonerName"],
            champion_id=data["championId"],
            champion_name=data["championName"],
            team_id=data["teamId"],
            participant_id=data["participantId"],
            # Basic stats
            kills=data["kills"],
            deaths=data["deaths"],
            assists=data["assists"],
            champion_level=data["champLevel"],
            gold_earned=data["goldEarned"],
            gold_spent=data["goldSpent"],
            vision_score=data["visionScore"],
            win=data["win"],
            # Items
            item_0=data["item0"],
            item_1=data["item1"],
            item_2=data["item2"],
            item_3=data["item3"],
            item_4=data["item4"],
            item_5=data["item5"],
            item_6=data["item6"],
            # Position and role
            individual_position=MatchParticipantPosition(data["individualPosition"]),
            team_position=MatchParticipantPosition(data["teamPosition"]),
            lane=data["lane"],
            role=data["role"],
            # Ping stats
            all_in_pings=data["allInPings"],
            assist_me_pings=data["assistMePings"],
            command_pings=data["commandPings"],
            enemy_missing_pings=data["enemyMissingPings"],
            enemy_vision_pings=data["enemyVisionPings"],
            get_back_pings=data["getBackPings"],
            hold_pings=data["holdPings"],
            need_vision_pings=data["needVisionPings"],
            on_my_way_pings=data["onMyWayPings"],
            push_pings=data["pushPings"],
            vision_cleared_pings=data["visionClearedPings"],
            # Kill stats
            baron_kills=data["baronKills"],
            double_kills=data["doubleKills"],
            dragon_kills=data["dragonKills"],
            inhibitor_kills=data["inhibitorKills"],
            killing_sprees=data["killingSprees"],
            largest_killing_spree=data["largestKillingSpree"],
            largest_multi_kill=data["largestMultiKill"],
            nexus_kills=data["nexusKills"],
            penta_kills=data["pentaKills"],
            quadra_kills=data["quadraKills"],
            triple_kills=data["tripleKills"],
            turret_kills=data["turretKills"],
            unreal_kills=data["unrealKills"],
            # Damage stats
            damage_dealt_to_buildings=data["damageDealtToBuildings"],
            damage_dealt_to_objectives=data["damageDealtToObjectives"],
            damage_dealt_to_turrets=data["damageDealtToTurrets"],
            damage_self_mitigated=data["damageSelfMitigated"],
            largest_critical_strike=data["largestCriticalStrike"],
            magic_damage_dealt=data["magicDamageDealt"],
            magic_damage_dealt_to_champions=data["magicDamageDealtToChampions"],
            magic_damage_taken=data["magicDamageTaken"],
            physical_damage_dealt=data["physicalDamageDealt"],
            physical_damage_dealt_to_champions=data["physicalDamageDealtToChampions"],
            physical_damage_taken=data["physicalDamageTaken"],
            total_damage_dealt=data["totalDamageDealt"],
            total_damage_dealt_to_champions=data["totalDamageDealtToChampions"],
            total_damage_shielded_on_teammates=data["totalDamageShieldedOnTeammates"],
            total_damage_taken=data["totalDamageTaken"],
            true_damage_dealt=data["trueDamageDealt"],
            true_damage_dealt_to_champions=data["trueDamageDealtToChampions"],
            true_damage_taken=data["trueDamageTaken"],
            # Minion and jungle stats
            neutral_minions_killed=data["neutralMinionsKilled"],
            total_ally_jungle_minions_killed=data["totalAllyJungleMinionsKilled"],
            total_enemy_jungle_minions_killed=data["totalEnemyJungleMinionsKilled"],
            total_minions_killed=data["totalMinionsKilled"],
            # Healing and support stats
            total_heal=data["totalHeal"],
            total_heals_on_teammates=data["totalHealsOnTeammates"],
            total_units_healed=data["totalUnitsHealed"],
            # Time stats
            longest_time_spent_living=data["longestTimeSpentLiving"],
            time_ccing_others=data["timeCCingOthers"],
            time_played=data["timePlayed"],
            total_time_cc_dealt=data["totalTimeCCDealt"],
            total_time_spent_dead=data["totalTimeSpentDead"],
            # Ward and vision stats
            detector_wards_placed=data["detectorWardsPlaced"],
            sight_wards_bought_in_game=data["sightWardsBoughtInGame"],
            vision_wards_bought_in_game=data["visionWardsBoughtInGame"],
            wards_killed=data["wardsKilled"],
            wards_placed=data["wardsPlaced"],
            # Spell casts
            spell_1_casts=data["spell1Casts"],
            spell_2_casts=data["spell2Casts"],
            spell_3_casts=data["spell3Casts"],
            spell_4_casts=data["spell4Casts"],
            summoner_1_casts=data["summoner1Casts"],
            summoner_1_id=data["summoner1Id"],
            summoner_2_casts=data["summoner2Casts"],
            summoner_2_id=data["summoner2Id"],
            # Structure stats
            inhibitor_takedowns=data["inhibitorTakedowns"],
            inhibitors_lost=data["inhibitorsLost"],
            nexus_takedowns=data["nexusTakedowns"],
            nexus_lost=data["nexusLost"],
            turret_takedowns=data["turretTakedowns"],
            turrets_lost=data["turretsLost"],
            # Objectives
            objectives_stolen=data["objectivesStolen"],
            objectives_stolen_assists=data["objectivesStolenAssists"],
            # Game state
            bounty_level=data.get("bountyLevel"),
            champ_experience=data["champExperience"],
            champion_transform=data["championTransform"],
            consumables_purchased=data["consumablesPurchased"],
            eligible_for_progression=data["eligibleForProgression"],
            first_blood_assist=data["firstBloodAssist"],
            first_blood_kill=data["firstBloodKill"],
            first_tower_assist=data["firstTowerAssist"],
            first_tower_kill=data["firstTowerKill"],
            game_ended_in_early_surrender=data["gameEndedInEarlySurrender"],
            game_ended_in_surrender=data["gameEndedInSurrender"],
            items_purchased=data["itemsPurchased"],
            placement=data["placement"],
            profile_icon=data["profileIcon"],
            summoner_id=data["summonerId"],
            summoner_level=data["summonerLevel"],
            team_early_surrendered=data["teamEarlySurrendered"],
            # Riot ID (optional fields)
            riot_id_game_name=data.get("riotIdGameName"),
            riot_id_tagline=data.get("riotIdTagline"),
            # Player scores (optional fields from missions)
            player_score_0=data.get("playerScore0"),
            player_score_1=data.get("playerScore1"),
            player_score_2=data.get("playerScore2"),
            player_score_3=data.get("playerScore3"),
            player_score_4=data.get("playerScore4"),
            player_score_5=data.get("playerScore5"),
            player_score_6=data.get("playerScore6"),
            player_score_7=data.get("playerScore7"),
            player_score_8=data.get("playerScore8"),
            player_score_9=data.get("playerScore9"),
            player_score_10=data.get("playerScore10"),
            player_score_11=data.get("playerScore11"),
            # Player augments (optional fields for specific game modes)
            player_augment_1=data.get("playerAugment1"),
            player_augment_2=data.get("playerAugment2"),
            player_augment_3=data.get("playerAugment3"),
            player_augment_4=data.get("playerAugment4"),
            player_subteam_id=data.get("playerSubteamId"),
            subteam_placement=data.get("subteamPlacement"),
            # Complex nested objects
            perks=Perks.from_api_response(data["perks"]) if data.get("perks") else None,
            challenges=Challenges.from_api_response(data["challenges"])
            if data.get("challenges")
            else None,
            missions=Missions.from_api_response(data["missions"])
            if data.get("missions")
            else None,
        )
