"""Participant-related models."""

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from nexar.enums import MatchParticipantPosition

from .match import BLUE_TEAM_ID

if TYPE_CHECKING:
    from nexar.client import NexarClient
    from nexar.enums import Region
    from nexar.models.player import Player

    from .challenges import Challenges, Missions
    from .perks import Perks


@dataclass(frozen=True)
class Participant:
    """Represents a match participant."""

    # Core participant data
    puuid: str
    """Player's universally unique identifier."""

    _summoner_name: str | None
    """
    Player's summoner name at the time of the match.

    **Deprecated by Riot.** Use `Participant.game_name` instead.

    May be None if Riot omitted the field from the response.
    """

    champion_id: int
    """
    Unique identifier for the champion played.

    Riot docs:
    > Prior to patch 11.4, on Feb 18th, 2021, this field returned invalid championIds.
    We recommend determining the champion based on the championName field for matches played prior
    to patch 11.4.
    """

    champion_name: str
    """
    Name of the champion played.
    """

    @property
    def champion_icon_url(self) -> str:
        """
        Link to champion icon URL via CDragon.

        Useful for Discord embeds or Web UI.
        """
        return (
            f"https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/"
            f"global/default/v1/champion-icons/{self.champion_id}.png"
        )

    team_id: int
    """Team identifier (100 for blue side, 200 for red side)."""

    @property
    def team_color(self) -> str:
        """Team color. Colloquially players use the terms "blue side" or "red side"."""
        return "Blue" if self.team_id == BLUE_TEAM_ID else "Red"

    @property
    @warnings.deprecated("Participant.summoner_name is deprecated. Use Participant.game_name instead.")
    def summoner_name(self) -> str | None:
        """
        Player's summoner name at the time of the match.

        **Deprecated by Riot.** Use `Participant.game_name` instead.

        Returns None if Riot omitted the field from the response.
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

    def kda(self, *, as_str: bool = False) -> float | str:
        """
        KDA ratio or formatted KDA string.

        By default returns the KDA ratio as (kills + assists) / max(1, deaths).
        If as_str=True, returns a formatted string like '5/2/10'.

        This is always available since kills, deaths, and assists are present
        for all game modes. For the challenge-specific KDA, use `Participant.challenges.kda`
        (only available when challenges are included in the API response).
        """
        if as_str:
            return f"{self.kills}/{self.deaths}/{self.assists}"
        return (self.kills + self.assists) / max(self.deaths, 1)

    async def get_player(
        self,
        client: "NexarClient",
        *,
        region: "Region | None" = None,
    ) -> "Player":
        """
        Get a Player object for this participant.

        Uses the participant's PUUID to look up their Riot account and create
        a Player, which provides convenient access to summoner data, league
        entries, match history, and more.

        Args:
            client: The NexarClient instance to use for API calls.
            region: The player's region (defaults to client default).

        Returns:
            A Player instance for this participant.

        """
        from nexar.models.player import Player

        return await Player.create(client=client, puuid=self.puuid, region=region)

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
    """
    (Presumably) Number of unreal kills achieved.

    Possibly for legacy/never released 6v6 gamemodes, but is unused and should be ignored.
    """

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

    @property
    def total_jungle_minions_killed(self) -> int:
        """Alias for neutral_minions_killed."""
        return self.neutral_minions_killed

    total_ally_jungle_minions_killed: int
    """Number of allied jungle minions killed."""

    total_enemy_jungle_minions_killed: int
    """Number of enemy jungle minions killed."""

    total_minions_killed: int
    """
    Total number of minions killed.

    Riot docs:
    > totalMillionsKilled = mMinionsKilled, which is only incremented on kills of kTeamMinion,
    kMeleeLaneMinion, kSuperLaneMinion, kRangedLaneMinion and kSiegeLaneMinion
    """

    @property
    def creep_score(self) -> int:
        """
        Total "Creep score" or CS earned throughout the game.

        Combination of lane minions + jungle minions.
        """
        return self.total_minions_killed + self.neutral_minions_killed

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

    placement: int | None
    """
    Final placement in the match (TFT and other mode-specific queues only).

    None for standard Summoner's Rift games, and when Riot omits the field.
    """

    profile_icon: int
    """Profile icon ID used by the participant."""

    summoner_id: str
    """Summoner ID of the participant."""

    summoner_level: int
    """Summoner level at the time of the match."""

    team_early_surrendered: bool
    """Whether the participant's team early surrendered."""

    # Complex nested objects (optionally included by Riot)
    perks: "Perks | None"
    """Rune and perk information. May be None if not included in the API response."""

    challenges: "Challenges | None"
    """Challenge completion data. May be None if not included in the API response."""

    missions: "Missions | None"
    """Mission completion data. May be None if not included in the API response."""

    # Riot ID
    game_name: str | None = None
    """Riot ID game name, if available."""

    tagline: str | None = None
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

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Participant":
        """Create Participant from API response."""
        from .challenges import Challenges, Missions
        from .perks import Perks

        return cls(
            # Core participant data
            puuid=data["puuid"],
            _summoner_name=data.get("summonerName"),
            champion_id=data["championId"],
            champion_name=data["championName"],
            team_id=data["teamId"],
            participant_id=data["participantId"],
            # Basic stats
            kills=data.get("kills", 0),
            deaths=data.get("deaths", 0),
            assists=data.get("assists", 0),
            champion_level=data.get("champLevel", 0),
            gold_earned=data.get("goldEarned", 0),
            gold_spent=data.get("goldSpent", 0),
            vision_score=data.get("visionScore", 0),
            win=data["win"],
            # Items
            item_0=data.get("item0", 0),
            item_1=data.get("item1", 0),
            item_2=data.get("item2", 0),
            item_3=data.get("item3", 0),
            item_4=data.get("item4", 0),
            item_5=data.get("item5", 0),
            item_6=data.get("item6", 0),
            # Position and role
            individual_position=MatchParticipantPosition(
                data.get("individualPosition", MatchParticipantPosition.INVALID),
            ),
            team_position=MatchParticipantPosition(data.get("teamPosition", MatchParticipantPosition.INVALID)),
            lane=data.get("lane", ""),
            role=data.get("role", ""),
            # Ping stats
            all_in_pings=data.get("allInPings", 0),
            assist_me_pings=data.get("assistMePings", 0),
            command_pings=data.get("commandPings", 0),
            enemy_missing_pings=data.get("enemyMissingPings", 0),
            enemy_vision_pings=data.get("enemyVisionPings", 0),
            get_back_pings=data.get("getBackPings", 0),
            hold_pings=data.get("holdPings", 0),
            need_vision_pings=data.get("needVisionPings", 0),
            on_my_way_pings=data.get("onMyWayPings", 0),
            push_pings=data.get("pushPings", 0),
            vision_cleared_pings=data.get("visionClearedPings", 0),
            # Kill stats
            baron_kills=data.get("baronKills", 0),
            double_kills=data.get("doubleKills", 0),
            dragon_kills=data.get("dragonKills", 0),
            inhibitor_kills=data.get("inhibitorKills", 0),
            killing_sprees=data.get("killingSprees", 0),
            largest_killing_spree=data.get("largestKillingSpree", 0),
            largest_multi_kill=data.get("largestMultiKill", 0),
            nexus_kills=data.get("nexusKills", 0),
            penta_kills=data.get("pentaKills", 0),
            quadra_kills=data.get("quadraKills", 0),
            triple_kills=data.get("tripleKills", 0),
            turret_kills=data.get("turretKills", 0),
            unreal_kills=data.get("unrealKills", 0),
            # Damage stats
            damage_dealt_to_buildings=data.get("damageDealtToBuildings", 0),
            damage_dealt_to_objectives=data.get("damageDealtToObjectives", 0),
            damage_dealt_to_turrets=data.get("damageDealtToTurrets", 0),
            damage_self_mitigated=data.get("damageSelfMitigated", 0),
            largest_critical_strike=data.get("largestCriticalStrike", 0),
            magic_damage_dealt=data.get("magicDamageDealt", 0),
            magic_damage_dealt_to_champions=data.get("magicDamageDealtToChampions", 0),
            magic_damage_taken=data.get("magicDamageTaken", 0),
            physical_damage_dealt=data.get("physicalDamageDealt", 0),
            physical_damage_dealt_to_champions=data.get("physicalDamageDealtToChampions", 0),
            physical_damage_taken=data.get("physicalDamageTaken", 0),
            total_damage_dealt=data.get("totalDamageDealt", 0),
            total_damage_dealt_to_champions=data.get("totalDamageDealtToChampions", 0),
            total_damage_shielded_on_teammates=data.get("totalDamageShieldedOnTeammates", 0),
            total_damage_taken=data.get("totalDamageTaken", 0),
            true_damage_dealt=data.get("trueDamageDealt", 0),
            true_damage_dealt_to_champions=data.get("trueDamageDealtToChampions", 0),
            true_damage_taken=data.get("trueDamageTaken", 0),
            # Minion and jungle stats
            neutral_minions_killed=data.get("neutralMinionsKilled", 0),
            total_ally_jungle_minions_killed=data.get("totalAllyJungleMinionsKilled", 0),
            total_enemy_jungle_minions_killed=data.get("totalEnemyJungleMinionsKilled", 0),
            total_minions_killed=data.get("totalMinionsKilled", 0),
            # Healing and support stats
            total_heal=data.get("totalHeal", 0),
            total_heals_on_teammates=data.get("totalHealsOnTeammates", 0),
            total_units_healed=data.get("totalUnitsHealed", 0),
            # Time stats
            longest_time_spent_living=data.get("longestTimeSpentLiving", 0),
            time_ccing_others=data.get("timeCCingOthers", 0),
            time_played=data.get("timePlayed", 0),
            total_time_cc_dealt=data.get("totalTimeCCDealt", 0),
            total_time_spent_dead=data.get("totalTimeSpentDead", 0),
            # Ward and vision stats
            detector_wards_placed=data.get("detectorWardsPlaced", 0),
            sight_wards_bought_in_game=data.get("sightWardsBoughtInGame", 0),
            vision_wards_bought_in_game=data.get("visionWardsBoughtInGame", 0),
            wards_killed=data.get("wardsKilled", 0),
            wards_placed=data.get("wardsPlaced", 0),
            # Spell casts
            spell_1_casts=data.get("spell1Casts", 0),
            spell_2_casts=data.get("spell2Casts", 0),
            spell_3_casts=data.get("spell3Casts", 0),
            spell_4_casts=data.get("spell4Casts", 0),
            summoner_1_casts=data.get("summoner1Casts", 0),
            summoner_1_id=data.get("summoner1Id", 0),
            summoner_2_casts=data.get("summoner2Casts", 0),
            summoner_2_id=data.get("summoner2Id", 0),
            # Structure stats
            inhibitor_takedowns=data.get("inhibitorTakedowns", 0),
            inhibitors_lost=data.get("inhibitorsLost", 0),
            nexus_takedowns=data.get("nexusTakedowns", 0),
            nexus_lost=data.get("nexusLost", 0),
            turret_takedowns=data.get("turretTakedowns", 0),
            turrets_lost=data.get("turretsLost", 0),
            # Objectives
            objectives_stolen=data.get("objectivesStolen", 0),
            objectives_stolen_assists=data.get("objectivesStolenAssists", 0),
            # Game state
            bounty_level=data.get("bountyLevel"),
            champ_experience=data.get("champExperience", 0),
            champion_transform=data.get("championTransform", 0),
            consumables_purchased=data.get("consumablesPurchased", 0),
            eligible_for_progression=data.get("eligibleForProgression", False),
            first_blood_assist=data.get("firstBloodAssist", False),
            first_blood_kill=data.get("firstBloodKill", False),
            first_tower_assist=data.get("firstTowerAssist", False),
            first_tower_kill=data.get("firstTowerKill", False),
            game_ended_in_early_surrender=data.get("gameEndedInEarlySurrender", False),
            game_ended_in_surrender=data.get("gameEndedInSurrender", False),
            items_purchased=data.get("itemsPurchased", 0),
            placement=data.get("placement"),
            profile_icon=data.get("profileIcon", 0),
            summoner_id=data.get("summonerId", ""),
            summoner_level=data.get("summonerLevel", 0),
            team_early_surrendered=data.get("teamEarlySurrendered", False),
            # Complex nested objects (optionally included by Riot)
            perks=Perks.from_api_response(p_data) if (p_data := data.get("perks")) else None,
            challenges=Challenges.from_api_response(c_data) if (c_data := data.get("challenges")) else None,
            missions=Missions.from_api_response(m_data) if (m_data := data.get("missions")) else None,
            # Riot ID (optional fields)
            game_name=data.get("riotIdGameName"),
            tagline=data.get("riotIdTagline"),
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
        )
