"""Participant-related models."""

import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from nexar.enums import MatchParticipantPosition

from .challenges import Challenges, Missions
from .perks import Perks
from .team import BLUE_TEAM_ID

if TYPE_CHECKING:
    from nexar.client import NexarClient
    from nexar.enums import Region
    from nexar.models.player import Player

# (api_name, python_name, default) for every field Riot may omit from a participant.
# Riot includes only non-empty values, so every stat field carries an explicit
# default here. Identity fields (puuid, championId, championName, teamId,
# participantId, win) stay direct reads in ``from_api_response``, a payload
# missing one of those is not a participant at all.
_DEFAULTED_FIELDS: tuple[tuple[str, str, Any], ...] = (
    # Deprecated name
    ("summonerName", "_summoner_name", None),
    # Basic stats
    ("kills", "kills", 0),
    ("deaths", "deaths", 0),
    ("assists", "assists", 0),
    ("champLevel", "champion_level", 0),
    ("goldEarned", "gold_earned", 0),
    ("goldSpent", "gold_spent", 0),
    ("visionScore", "vision_score", 0),
    # Items
    ("item0", "item_0", 0),
    ("item1", "item_1", 0),
    ("item2", "item_2", 0),
    ("item3", "item_3", 0),
    ("item4", "item_4", 0),
    ("item5", "item_5", 0),
    ("item6", "item_6", 0),
    # Position and role
    ("lane", "lane", ""),
    ("role", "role", ""),
    # Ping stats
    ("allInPings", "all_in_pings", 0),
    ("assistMePings", "assist_me_pings", 0),
    ("commandPings", "command_pings", 0),
    ("enemyMissingPings", "enemy_missing_pings", 0),
    ("enemyVisionPings", "enemy_vision_pings", 0),
    ("getBackPings", "get_back_pings", 0),
    ("holdPings", "hold_pings", 0),
    ("needVisionPings", "need_vision_pings", 0),
    ("onMyWayPings", "on_my_way_pings", 0),
    ("pushPings", "push_pings", 0),
    ("visionClearedPings", "vision_cleared_pings", 0),
    # Kill stats
    ("baronKills", "baron_kills", 0),
    ("doubleKills", "double_kills", 0),
    ("dragonKills", "dragon_kills", 0),
    ("inhibitorKills", "inhibitor_kills", 0),
    ("killingSprees", "killing_sprees", 0),
    ("largestKillingSpree", "largest_killing_spree", 0),
    ("largestMultiKill", "largest_multi_kill", 0),
    ("nexusKills", "nexus_kills", 0),
    ("pentaKills", "penta_kills", 0),
    ("quadraKills", "quadra_kills", 0),
    ("tripleKills", "triple_kills", 0),
    ("turretKills", "turret_kills", 0),
    ("unrealKills", "unreal_kills", 0),
    # Damage stats
    ("damageDealtToBuildings", "damage_dealt_to_buildings", 0),
    ("damageDealtToObjectives", "damage_dealt_to_objectives", 0),
    ("damageDealtToTurrets", "damage_dealt_to_turrets", 0),
    ("damageSelfMitigated", "damage_self_mitigated", 0),
    ("largestCriticalStrike", "largest_critical_strike", 0),
    ("magicDamageDealt", "magic_damage_dealt", 0),
    ("magicDamageDealtToChampions", "magic_damage_dealt_to_champions", 0),
    ("magicDamageTaken", "magic_damage_taken", 0),
    ("physicalDamageDealt", "physical_damage_dealt", 0),
    ("physicalDamageDealtToChampions", "physical_damage_dealt_to_champions", 0),
    ("physicalDamageTaken", "physical_damage_taken", 0),
    ("totalDamageDealt", "total_damage_dealt", 0),
    ("totalDamageDealtToChampions", "total_damage_dealt_to_champions", 0),
    ("totalDamageShieldedOnTeammates", "total_damage_shielded_on_teammates", 0),
    ("totalDamageTaken", "total_damage_taken", 0),
    ("trueDamageDealt", "true_damage_dealt", 0),
    ("trueDamageDealtToChampions", "true_damage_dealt_to_champions", 0),
    ("trueDamageTaken", "true_damage_taken", 0),
    # Minion and jungle stats
    ("neutralMinionsKilled", "neutral_minions_killed", 0),
    ("totalAllyJungleMinionsKilled", "total_ally_jungle_minions_killed", 0),
    ("totalEnemyJungleMinionsKilled", "total_enemy_jungle_minions_killed", 0),
    ("totalMinionsKilled", "total_minions_killed", 0),
    # Healing and support stats
    ("totalHeal", "total_heal", 0),
    ("totalHealsOnTeammates", "total_heals_on_teammates", 0),
    ("totalUnitsHealed", "total_units_healed", 0),
    # Time stats
    ("longestTimeSpentLiving", "longest_time_spent_living", 0),
    ("timeCCingOthers", "time_ccing_others", 0),
    ("timePlayed", "time_played", 0),
    ("totalTimeCCDealt", "total_time_cc_dealt", 0),
    ("totalTimeSpentDead", "total_time_spent_dead", 0),
    # Ward and vision stats
    ("detectorWardsPlaced", "detector_wards_placed", 0),
    ("sightWardsBoughtInGame", "sight_wards_bought_in_game", 0),
    ("visionWardsBoughtInGame", "vision_wards_bought_in_game", 0),
    ("wardsKilled", "wards_killed", 0),
    ("wardsPlaced", "wards_placed", 0),
    # Spell casts
    ("spell1Casts", "spell_1_casts", 0),
    ("spell2Casts", "spell_2_casts", 0),
    ("spell3Casts", "spell_3_casts", 0),
    ("spell4Casts", "spell_4_casts", 0),
    ("summoner1Casts", "summoner_1_casts", 0),
    ("summoner1Id", "summoner_1_id", 0),
    ("summoner2Casts", "summoner_2_casts", 0),
    ("summoner2Id", "summoner_2_id", 0),
    # Structure stats
    ("inhibitorTakedowns", "inhibitor_takedowns", 0),
    ("inhibitorsLost", "inhibitors_lost", 0),
    ("nexusTakedowns", "nexus_takedowns", 0),
    ("nexusLost", "nexus_lost", 0),
    ("turretTakedowns", "turret_takedowns", 0),
    ("turretsLost", "turrets_lost", 0),
    # Objectives
    ("objectivesStolen", "objectives_stolen", 0),
    ("objectivesStolenAssists", "objectives_stolen_assists", 0),
    # Game state
    ("bountyLevel", "bounty_level", None),
    ("champExperience", "champ_experience", 0),
    ("championTransform", "champion_transform", 0),
    ("consumablesPurchased", "consumables_purchased", 0),
    ("eligibleForProgression", "eligible_for_progression", False),
    ("firstBloodAssist", "first_blood_assist", False),
    ("firstBloodKill", "first_blood_kill", False),
    ("firstTowerAssist", "first_tower_assist", False),
    ("firstTowerKill", "first_tower_kill", False),
    ("gameEndedInEarlySurrender", "game_ended_in_early_surrender", False),
    ("gameEndedInSurrender", "game_ended_in_surrender", False),
    ("itemsPurchased", "items_purchased", 0),
    ("placement", "placement", None),
    ("profileIcon", "profile_icon", 0),
    ("summonerId", "summoner_id", ""),
    ("summonerLevel", "summoner_level", 0),
    ("teamEarlySurrendered", "team_early_surrendered", False),
    # Riot ID
    ("riotIdGameName", "game_name", None),
    ("riotIdTagline", "tagline", None),
    # Player scores (top-level copies; the missions block is canonical)
    ("playerScore0", "player_score_0", None),
    ("playerScore1", "player_score_1", None),
    ("playerScore2", "player_score_2", None),
    ("playerScore3", "player_score_3", None),
    ("playerScore4", "player_score_4", None),
    ("playerScore5", "player_score_5", None),
    ("playerScore6", "player_score_6", None),
    ("playerScore7", "player_score_7", None),
    ("playerScore8", "player_score_8", None),
    ("playerScore9", "player_score_9", None),
    ("playerScore10", "player_score_10", None),
    ("playerScore11", "player_score_11", None),
    # Player augments (mode-specific)
    ("playerAugment1", "player_augment_1", None),
    ("playerAugment2", "player_augment_2", None),
    ("playerAugment3", "player_augment_3", None),
    ("playerAugment4", "player_augment_4", None),
    ("playerSubteamId", "player_subteam_id", None),
    ("subteamPlacement", "subteam_placement", None),
)


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
    """This participant's index in the match's participant list (1-10).

    Not a map position, see ``team_position`` for the played role."""

    # Basic stats
    kills: int
    """Number of enemy champions killed."""

    deaths: int
    """Number of times the participant died."""

    assists: int
    """Number of assists on enemy champion kills."""

    def kda(self) -> float:
        """
        KDA ratio as (kills + assists) / max(1, deaths).

        This is always available since kills, deaths, and assists are present
        for all game modes. For the challenge-specific KDA, use `Participant.challenges.kda`
        (only available when challenges are included in the API response).
        """
        return (self.kills + self.assists) / max(self.deaths, 1)

    def kda_string(self) -> str:
        """Formatted KDA string like '5/2/10'."""
        return f"{self.kills}/{self.deaths}/{self.assists}"

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
        # local import: nexar.models.player imports the match modules, so importing
        # Player here at module level would be circular.
        from nexar.models.player import Player

        return await Player.create(client=client, puuid=self.puuid, region=region)

    champion_level: int
    """Final champion level achieved."""

    gold_earned: int
    """Total gold earned during the match.

    Per-minute rate: [`Challenges.gold_per_minute`][nexar.models.match.challenges.Challenges.gold_per_minute],
    when the wire includes the challenges block.
    """

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
    """Total damage dealt to enemy champions (all types combined).

    Per-minute rate: [`Challenges.damage_per_minute`][nexar.models.match.challenges.Challenges.damage_per_minute],
    when the wire includes the challenges block.
    """

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
    """Whether the game ended in an early surrender (before the 15-minute remake window closed)."""

    game_ended_in_surrender: bool
    """Whether the game ended in a surrender."""

    items_purchased: int
    """Total number of items purchased."""

    placement: int | None
    """
    Final placement in the match (TFT and other mode-specific queues only).

    None when Riot omits the field. Standard Summoner's Rift games report a
    placement of 0 (the recorded fixture does) rather than omitting it.
    """

    profile_icon: int
    """Profile icon ID used by the participant."""

    summoner_id: str
    """Summoner ID of the participant. Empty string when Riot omits the field."""

    summoner_level: int
    """Summoner level at the time of the match."""

    team_early_surrendered: bool
    """Whether the participant's team early surrendered."""

    # Complex nested objects (optionally included by Riot)
    perks: Perks | None
    """Rune and perk information. May be None if not included in the API response."""

    challenges: Challenges | None
    """Challenge completion data. May be None if not included in the API response.

    None is the old-match case (pre-2022 payloads omit the block), so guard the
    read. The per-minute rates (gold, damage, vision) live here rather than on
    the participant totals.

    See [Challenges][nexar.models.match.challenges.Challenges] for the full attribute list.
    """

    missions: Missions | None
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
    """Mission score 0, if applicable. The ``missions`` block is canonical (``Missions.player_score_0``)."""

    player_score_1: int | None = None
    """Mission score 1, if applicable. The ``missions`` block is canonical (``Missions.player_score_1``)."""

    player_score_2: int | None = None
    """Mission score 2, if applicable. The ``missions`` block is canonical (``Missions.player_score_2``)."""

    player_score_3: int | None = None
    """Mission score 3, if applicable. The ``missions`` block is canonical (``Missions.player_score_3``)."""

    player_score_4: int | None = None
    """Mission score 4, if applicable. The ``missions`` block is canonical (``Missions.player_score_4``)."""

    player_score_5: int | None = None
    """Mission score 5, if applicable. The ``missions`` block is canonical (``Missions.player_score_5``)."""

    player_score_6: int | None = None
    """Mission score 6, if applicable. The ``missions`` block is canonical (``Missions.player_score_6``)."""

    player_score_7: int | None = None
    """Mission score 7, if applicable. The ``missions`` block is canonical (``Missions.player_score_7``)."""

    player_score_8: int | None = None
    """Mission score 8, if applicable. The ``missions`` block is canonical (``Missions.player_score_8``)."""

    player_score_9: int | None = None
    """Mission score 9, if applicable. The ``missions`` block is canonical (``Missions.player_score_9``)."""

    player_score_10: int | None = None
    """Mission score 10, if applicable. The ``missions`` block is canonical (``Missions.player_score_10``)."""

    player_score_11: int | None = None
    """Mission score 11, if applicable. The ``missions`` block is canonical (``Missions.player_score_11``)."""

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
        # local imports: these siblings import .match, so module-level imports
        # here would be circular.
        from .challenges import Challenges, Missions
        from .perks import Perks

        kwargs: dict[str, Any] = {
            py_name: data.get(api_name, default) for api_name, py_name, default in _DEFAULTED_FIELDS
        }
        return cls(
            # Identity fields are direct reads: always present, and a missing one
            # means the payload is not a participant at all.
            puuid=data["puuid"],
            champion_id=data["championId"],
            champion_name=data["championName"],
            team_id=data["teamId"],
            participant_id=data["participantId"],
            win=data["win"],
            # Position enums degrade to INVALID when Riot omits the field.
            individual_position=MatchParticipantPosition(
                data.get("individualPosition", MatchParticipantPosition.INVALID),
            ),
            team_position=MatchParticipantPosition(data.get("teamPosition", MatchParticipantPosition.INVALID)),
            # Complex nested objects, each optional in the payload.
            perks=Perks.from_api_response(p_data) if (p_data := data.get("perks")) else None,
            challenges=Challenges.from_api_response(c_data) if (c_data := data.get("challenges")) else None,
            missions=Missions.from_api_response(m_data) if (m_data := data.get("missions")) else None,
            **kwargs,
        )
