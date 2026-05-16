"""Challenge and mission-related models."""

from dataclasses import dataclass
from typing import Any, ClassVar


@dataclass(frozen=True)
class Challenges:
    """Represents participant challenges."""

    # Core stats
    kda: float | None = None
    """Kill/death/assist ratio"""

    kill_participation: float | None = None
    """Percentage of team kills participated in"""

    damage_per_minute: float | None = None
    """Average damage dealt per minute"""

    gold_per_minute: float | None = None
    """Average gold earned per minute"""

    vision_score_per_minute: float | None = None
    """Vision score normalized per minute"""

    # Extended challenges
    twelve_assist_streak_count: int | None = None
    """Count of 12+ assist streaks"""

    baron_buff_gold_advantage_over_threshold: int | None = None
    """Gold advantage gained from baron buff"""

    control_ward_time_coverage_in_river_or_enemy_half: float | None = None
    """Time coverage of control wards in river or enemy territory"""

    earliest_baron: int | None = None
    """Time of earliest baron takedown"""

    earliest_dragon_takedown: int | None = None
    """Time of earliest dragon takedown"""

    earliest_elder_dragon: int | None = None
    """Time of earliest elder dragon takedown"""

    early_laning_phase_gold_exp_advantage: int | None = None
    """Gold and experience advantage in early laning phase"""

    faster_support_quest_completion: int | None = None
    """Speed of support quest completion"""

    fastest_legendary: int | None = None
    """Time to fastest legendary item"""

    had_afk_teammate: int | None = None
    """Whether player had an AFK teammate"""

    highest_champion_damage: int | None = None
    """Highest champion damage dealt"""

    highest_crowd_control_score: int | None = None
    """Highest crowd control score"""

    highest_ward_kills: int | None = None
    """Highest number of wards destroyed"""

    jungler_kills_early_jungle: int | None = None
    """Jungle kills in early game as jungler"""

    kills_on_laners_early_jungle_as_jungler: int | None = None
    """Kills on enemy laners in early jungle as jungler"""

    laning_phase_gold_exp_advantage: int | None = None
    """Gold and experience advantage during laning phase"""

    legendary_count: int | None = None
    """Number of legendary items"""

    max_cs_advantage_on_lane_opponent: float | None = None
    """Maximum CS advantage over lane opponent"""

    max_level_lead_lane_opponent: int | None = None
    """Maximum level lead over lane opponent"""

    most_wards_destroyed_one_sweeper: int | None = None
    """Most wards destroyed with a single sweeper"""

    mythic_item_used: int | None = None
    """Whether mythic item was used"""

    played_champ_select_position: int | None = None
    """Whether player played their assigned position"""

    solo_turrets_lategame: int | None = None
    """Solo turret kills in late game"""

    takedowns_first_25_minutes: int | None = None
    """Takedowns in first 25 minutes"""

    teleport_takedowns: int | None = None
    """Takedowns assisted by teleport"""

    third_inhibitor_destroyed_time: int | None = None
    """Time when third inhibitor was destroyed"""

    three_wards_one_sweeper_count: int | None = None
    """Count of destroying 3+ wards with one sweeper"""

    vision_score_advantage_lane_opponent: float | None = None
    """Vision score advantage over lane opponent"""

    infernal_scale_pickup: int | None = None
    """Infernal scale pickups"""

    fist_bump_participation: int | None = None
    """Fist bump participation count"""

    void_monster_kill: int | None = None
    """Void monster kills"""

    ability_uses: int | None = None
    """Total ability uses"""

    aces_before_15_minutes: int | None = None
    """Aces achieved before 15 minutes"""

    allied_jungle_monster_kills: float | None = None
    """Allied jungle monster kills"""

    baron_takedowns: int | None = None
    """Baron takedowns"""

    blast_cone_opposite_opponent_count: int | None = None
    """Blast cones used opposite to opponent"""

    bounty_gold: int | None = None
    """Gold earned from bounties"""

    buffs_stolen: int | None = None
    """Enemy buffs stolen"""

    complete_support_quest_in_time: int | None = None
    """Whether support quest was completed in time"""

    control_wards_placed: int | None = None
    """Control wards placed"""

    damage_taken_on_team_percentage: float | None = None
    """Percentage of team damage taken"""

    danced_with_rift_herald: int | None = None
    """Whether player danced with rift herald"""

    deaths_by_enemy_champs: int | None = None
    """Deaths caused by enemy champions"""

    dodge_skill_shots_small_window: int | None = None
    """Skillshots dodged in small time window"""

    double_aces: int | None = None
    """Double aces achieved"""

    dragon_takedowns: int | None = None
    """Dragon takedowns"""

    legendary_item_used: list[int] | None = None
    """List of legendary items used"""

    effective_heal_and_shielding: float | None = None
    """Effective healing and shielding provided"""

    elder_dragon_kills_with_opposing_soul: int | None = None
    """Elder dragon kills when enemy has soul"""

    elder_dragon_multikills: int | None = None
    """Multikills on elder dragon"""

    enemy_champion_immobilizations: int | None = None
    """Enemy champions immobilized"""

    enemy_jungle_monster_kills: float | None = None
    """Enemy jungle monsters killed"""

    epic_monster_kills_near_enemy_jungler: int | None = None
    """Epic monsters killed near enemy jungler"""

    epic_monster_kills_within_30_seconds_of_spawn: int | None = None
    """Epic monsters killed within 30 seconds of spawn"""

    epic_monster_steals: int | None = None
    """Epic monsters stolen"""

    epic_monster_stolen_without_smite: int | None = None
    """Epic monsters stolen without smite"""

    first_turret_killed: int | None = None
    """Whether first turret was killed"""

    first_turret_killed_time: float | None = None
    """Time when first turret was killed"""

    flawless_aces: int | None = None
    """Flawless aces achieved"""

    full_team_takedown: int | None = None
    """Full team takedowns"""

    game_length: float | None = None
    """Total game length"""

    get_takedowns_in_all_lanes_early_jungle_as_laner: int | None = None
    """Takedowns in all lanes during early jungle as laner"""

    had_open_nexus: int | None = None
    """Whether nexus was open"""

    immobilize_and_kill_with_ally: int | None = None
    """Immobilizations and kills with ally"""

    initial_buff_count: int | None = None
    """Initial jungle buff count"""

    initial_crab_count: int | None = None
    """Initial scuttle crab count"""

    jungle_cs_before_10_minutes: float | None = None
    """Jungle CS before 10 minutes"""

    jungler_takedowns_near_damaged_epic_monster: int | None = None
    """Jungler takedowns near damaged epic monster"""

    kill_after_hidden_with_ally: int | None = None
    """Kills after being hidden with ally"""

    killed_champ_took_full_team_damage_survived: int | None = None
    """Champions killed who took full team damage and survived"""

    killing_sprees: int | None = None
    """Killing sprees achieved"""

    kills_near_enemy_turret: int | None = None
    """Kills near enemy turret"""

    kills_on_other_lanes_early_jungle_as_laner: int | None = None
    """Kills on other lanes during early jungle as laner"""

    kills_on_recently_healed_by_aram_pack: int | None = None
    """Kills on recently healed by ARAM health pack"""

    kills_under_own_turret: int | None = None
    """Kills under own turret"""

    kills_with_help_from_epic_monster: int | None = None
    """Kills with help from epic monster"""

    knock_enemy_into_team_and_kill: int | None = None
    """Enemies knocked into team and killed"""

    k_turrets_destroyed_before_plates_fall: int | None = None
    """Turrets destroyed before plates fall"""

    land_skill_shots_early_game: int | None = None
    """Skillshots landed in early game"""

    lane_minions_first_10_minutes: int | None = None
    """Lane minions killed in first 10 minutes"""

    lost_an_inhibitor: int | None = None
    """Whether an inhibitor was lost"""

    max_kill_deficit: int | None = None
    """Maximum kill deficit"""

    mejais_full_stack_in_time: int | None = None
    """Whether Mejais was fully stacked in time"""

    more_enemy_jungle_than_opponent: float | None = None
    """More enemy jungle monsters than opponent"""

    multi_kill_one_spell: int | None = None
    """Multikills with one spell - spell with same instance ID does final damage to 2+ champions"""

    multikills: int | None = None
    """Total multikills"""

    multikills_after_aggressive_flash: int | None = None
    """Multikills after aggressive flash"""

    multi_turret_rift_herald_count: int | None = None
    """Multiple turrets destroyed with rift herald"""

    outer_turret_executes_before_10_minutes: int | None = None
    """Outer turret executes before 10 minutes"""

    outnumbered_kills: int | None = None
    """Kills while outnumbered"""

    outnumbered_nexus_kill: int | None = None
    """Nexus kills while outnumbered"""

    perfect_dragon_souls_taken: int | None = None
    """Perfect dragon souls taken"""

    perfect_game: int | None = None
    """Whether a perfect game was achieved"""

    pick_kill_with_ally: int | None = None
    """Pick kills with ally"""

    poro_explosions: int | None = None
    """Poro explosions caused"""

    quick_cleanse: int | None = None
    """Quick cleanses used"""

    quick_first_turret: int | None = None
    """Quick first turret takedown"""

    quick_solo_kills: int | None = None
    """Quick solo kills"""

    rift_herald_takedowns: int | None = None
    """Rift herald takedowns"""

    save_ally_from_death: int | None = None
    """Allies saved from death"""

    scuttle_crab_kills: int | None = None
    """Scuttle crab kills"""

    shortest_time_to_ace_from_first_takedown: float | None = None
    """Shortest time to ace from first takedown"""

    skillshots_dodged: int | None = None
    """Skillshots dodged"""

    skillshots_hit: int | None = None
    """Skillshots hit"""

    snowballs_hit: int | None = None
    """Snowballs hit (ARAM)"""

    solo_baron_kills: int | None = None
    """Solo baron kills"""

    swarm_defeat_aatrox: int | None = None
    """SWARM mode: Aatrox defeats"""

    swarm_defeat_briar: int | None = None
    """SWARM mode: Briar defeats"""

    swarm_defeat_mini_bosses: int | None = None
    """SWARM mode: Mini boss defeats"""

    swarm_evolve_weapon: int | None = None
    """SWARM mode: Weapon evolutions"""

    swarm_have_3_passives: int | None = None
    """SWARM mode: Having 3 passives"""

    swarm_kill_enemy: int | None = None
    """SWARM mode: Enemy kills"""

    swarm_pickup_gold: float | None = None
    """SWARM mode: Gold picked up"""

    swarm_reach_level_50: int | None = None
    """SWARM mode: Reaching level 50"""

    swarm_survive_15_min: int | None = None
    """SWARM mode: Surviving 15 minutes"""

    swarm_win_with_5_evolved_weapons: int | None = None
    """SWARM mode: Winning with 5 evolved weapons"""

    solo_kills: int | None = None
    """Solo kills"""

    stealth_wards_placed: int | None = None
    """Stealth wards placed"""

    survived_single_digit_hp_count: int | None = None
    """Times survived with single digit HP"""

    survived_three_immobilizes_in_fight: int | None = None
    """Times survived three immobilizes in a fight"""

    takedown_on_first_turret: int | None = None
    """Takedown on first turret"""

    takedowns: int | None = None
    """Total takedowns"""

    takedowns_after_gaining_level_advantage: int | None = None
    """Takedowns after gaining level advantage"""

    takedowns_before_jungle_minion_spawn: int | None = None
    """Takedowns before jungle minion spawn"""

    takedowns_first_x_minutes: int | None = None
    """Takedowns in first X minutes"""

    takedowns_in_alcove: int | None = None
    """Takedowns in alcove"""

    takedowns_in_enemy_fountain: int | None = None
    """Takedowns in enemy fountain"""

    team_baron_kills: int | None = None
    """Team baron kills"""

    team_damage_percentage: float | None = None
    """Percentage of team damage dealt"""

    team_elder_dragon_kills: int | None = None
    """Team elder dragon kills"""

    team_rift_herald_kills: int | None = None
    """Team rift herald kills"""

    took_large_damage_survived: int | None = None
    """Times took large damage and survived"""

    turret_plates_taken: int | None = None
    """Turret plates taken"""

    turrets_taken_with_rift_herald: int | None = None
    """Turrets taken with rift herald - player who damages tower destroyed within 30s of herald charge"""

    turret_takedowns: int | None = None
    """Turret takedowns"""

    twenty_minions_in_3_seconds_count: int | None = None
    """Count of killing 20+ minions in 3 seconds"""

    two_wards_one_sweeper_count: int | None = None
    """Count of destroying 2+ wards with one sweeper"""

    unseen_recalls: int | None = None
    """Unseen recalls"""

    wards_guarded: int | None = None
    """Wards guarded"""

    ward_takedowns: int | None = None
    """Ward takedowns"""

    ward_takedowns_before_20m: int | None = None
    """Ward takedowns before 20 minutes"""

    _FIELD_MAP: ClassVar[dict[str, str]] = {
        "kda": "kda",
        "killParticipation": "kill_participation",
        "damagePerMinute": "damage_per_minute",
        "goldPerMinute": "gold_per_minute",
        "visionScorePerMinute": "vision_score_per_minute",
        "12AssistStreakCount": "twelve_assist_streak_count",
        "baronBuffGoldAdvantageOverThreshold": "baron_buff_gold_advantage_over_threshold",
        "controlWardTimeCoverageInRiverOrEnemyHalf": "control_ward_time_coverage_in_river_or_enemy_half",
        "earliestBaron": "earliest_baron",
        "earliestDragonTakedown": "earliest_dragon_takedown",
        "earliestElderDragon": "earliest_elder_dragon",
        "earlyLaningPhaseGoldExpAdvantage": "early_laning_phase_gold_exp_advantage",
        "fasterSupportQuestCompletion": "faster_support_quest_completion",
        "fastestLegendary": "fastest_legendary",
        "hadAfkTeammate": "had_afk_teammate",
        "highestChampionDamage": "highest_champion_damage",
        "highestCrowdControlScore": "highest_crowd_control_score",
        "highestWardKills": "highest_ward_kills",
        "junglerKillsEarlyJungle": "jungler_kills_early_jungle",
        "killsOnLanersEarlyJungleAsJungler": "kills_on_laners_early_jungle_as_jungler",
        "laningPhaseGoldExpAdvantage": "laning_phase_gold_exp_advantage",
        "legendaryCount": "legendary_count",
        "maxCsAdvantageOnLaneOpponent": "max_cs_advantage_on_lane_opponent",
        "maxLevelLeadLaneOpponent": "max_level_lead_lane_opponent",
        "mostWardsDestroyedOneSweeper": "most_wards_destroyed_one_sweeper",
        "mythicItemUsed": "mythic_item_used",
        "playedChampSelectPosition": "played_champ_select_position",
        "soloTurretsLategame": "solo_turrets_lategame",
        "takedownsFirst25Minutes": "takedowns_first_25_minutes",
        "teleportTakedowns": "teleport_takedowns",
        "thirdInhibitorDestroyedTime": "third_inhibitor_destroyed_time",
        "threeWardsOneSweeperCount": "three_wards_one_sweeper_count",
        "visionScoreAdvantageLaneOpponent": "vision_score_advantage_lane_opponent",
        "InfernalScalePickup": "infernal_scale_pickup",
        "fistBumpParticipation": "fist_bump_participation",
        "voidMonsterKill": "void_monster_kill",
        "abilityUses": "ability_uses",
        "acesBefore15Minutes": "aces_before_15_minutes",
        "alliedJungleMonsterKills": "allied_jungle_monster_kills",
        "baronTakedowns": "baron_takedowns",
        "blastConeOppositeOpponentCount": "blast_cone_opposite_opponent_count",
        "bountyGold": "bounty_gold",
        "buffsStolen": "buffs_stolen",
        "completeSupportQuestInTime": "complete_support_quest_in_time",
        "controlWardsPlaced": "control_wards_placed",
        "damageTakenOnTeamPercentage": "damage_taken_on_team_percentage",
        "dancedWithRiftHerald": "danced_with_rift_herald",
        "deathsByEnemyChamps": "deaths_by_enemy_champs",
        "dodgeSkillShotsSmallWindow": "dodge_skill_shots_small_window",
        "doubleAces": "double_aces",
        "dragonTakedowns": "dragon_takedowns",
        "legendaryItemUsed": "legendary_item_used",
        "effectiveHealAndShielding": "effective_heal_and_shielding",
        "elderDragonKillsWithOpposingSoul": "elder_dragon_kills_with_opposing_soul",
        "elderDragonMultikills": "elder_dragon_multikills",
        "enemyChampionImmobilizations": "enemy_champion_immobilizations",
        "enemyJungleMonsterKills": "enemy_jungle_monster_kills",
        "epicMonsterKillsNearEnemyJungler": "epic_monster_kills_near_enemy_jungler",
        "epicMonsterKillsWithin30SecondsOfSpawn": "epic_monster_kills_within_30_seconds_of_spawn",
        "epicMonsterSteals": "epic_monster_steals",
        "epicMonsterStolenWithoutSmite": "epic_monster_stolen_without_smite",
        "firstTurretKilled": "first_turret_killed",
        "firstTurretKilledTime": "first_turret_killed_time",
        "flawlessAces": "flawless_aces",
        "fullTeamTakedown": "full_team_takedown",
        "gameLength": "game_length",
        "getTakedownsInAllLanesEarlyJungleAsLaner": "get_takedowns_in_all_lanes_early_jungle_as_laner",
        "hadOpenNexus": "had_open_nexus",
        "immobilizeAndKillWithAlly": "immobilize_and_kill_with_ally",
        "initialBuffCount": "initial_buff_count",
        "initialCrabCount": "initial_crab_count",
        "jungleCsBefore10Minutes": "jungle_cs_before_10_minutes",
        "junglerTakedownsNearDamagedEpicMonster": "jungler_takedowns_near_damaged_epic_monster",
        "killAfterHiddenWithAlly": "kill_after_hidden_with_ally",
        "killedChampTookFullTeamDamageSurvived": "killed_champ_took_full_team_damage_survived",
        "killingSprees": "killing_sprees",
        "killsNearEnemyTurret": "kills_near_enemy_turret",
        "killsOnOtherLanesEarlyJungleAsLaner": "kills_on_other_lanes_early_jungle_as_laner",
        "killsOnRecentlyHealedByAramPack": "kills_on_recently_healed_by_aram_pack",
        "killsUnderOwnTurret": "kills_under_own_turret",
        "killsWithHelpFromEpicMonster": "kills_with_help_from_epic_monster",
        "knockEnemyIntoTeamAndKill": "knock_enemy_into_team_and_kill",
        "kTurretsDestroyedBeforePlatesFall": "k_turrets_destroyed_before_plates_fall",
        "landSkillShotsEarlyGame": "land_skill_shots_early_game",
        "laneMinionsFirst10Minutes": "lane_minions_first_10_minutes",
        "lostAnInhibitor": "lost_an_inhibitor",
        "maxKillDeficit": "max_kill_deficit",
        "mejaisFullStackInTime": "mejais_full_stack_in_time",
        "moreEnemyJungleThanOpponent": "more_enemy_jungle_than_opponent",
        "multiKillOneSpell": "multi_kill_one_spell",
        "multikills": "multikills",
        "multikillsAfterAggressiveFlash": "multikills_after_aggressive_flash",
        "multiTurretRiftHeraldCount": "multi_turret_rift_herald_count",
        "outerTurretExecutesBefore10Minutes": "outer_turret_executes_before_10_minutes",
        "outnumberedKills": "outnumbered_kills",
        "outnumberedNexusKill": "outnumbered_nexus_kill",
        "perfectDragonSoulsTaken": "perfect_dragon_souls_taken",
        "perfectGame": "perfect_game",
        "pickKillWithAlly": "pick_kill_with_ally",
        "poroExplosions": "poro_explosions",
        "quickCleanse": "quick_cleanse",
        "quickFirstTurret": "quick_first_turret",
        "quickSoloKills": "quick_solo_kills",
        "riftHeraldTakedowns": "rift_herald_takedowns",
        "saveAllyFromDeath": "save_ally_from_death",
        "scuttleCrabKills": "scuttle_crab_kills",
        "shortestTimeToAceFromFirstTakedown": "shortest_time_to_ace_from_first_takedown",
        "skillshotsDodged": "skillshots_dodged",
        "skillshotsHit": "skillshots_hit",
        "snowballsHit": "snowballs_hit",
        "soloBaronKills": "solo_baron_kills",
        "SWARM_DefeatAatrox": "swarm_defeat_aatrox",
        "SWARM_DefeatBriar": "swarm_defeat_briar",
        "SWARM_DefeatMiniBosses": "swarm_defeat_mini_bosses",
        "SWARM_EvolveWeapon": "swarm_evolve_weapon",
        "SWARM_Have3Passives": "swarm_have_3_passives",
        "SWARM_KillEnemy": "swarm_kill_enemy",
        "SWARM_PickupGold": "swarm_pickup_gold",
        "SWARM_ReachLevel50": "swarm_reach_level_50",
        "SWARM_Survive15Min": "swarm_survive_15_min",
        "SWARM_WinWith5EvolvedWeapons": "swarm_win_with_5_evolved_weapons",
        "soloKills": "solo_kills",
        "stealthWardsPlaced": "stealth_wards_placed",
        "survivedSingleDigitHpCount": "survived_single_digit_hp_count",
        "survivedThreeImmobilizesInFight": "survived_three_immobilizes_in_fight",
        "takedownOnFirstTurret": "takedown_on_first_turret",
        "takedowns": "takedowns",
        "takedownsAfterGainingLevelAdvantage": "takedowns_after_gaining_level_advantage",
        "takedownsBeforeJungleMinionSpawn": "takedowns_before_jungle_minion_spawn",
        "takedownsFirstXMinutes": "takedowns_first_x_minutes",
        "takedownsInAlcove": "takedowns_in_alcove",
        "takedownsInEnemyFountain": "takedowns_in_enemy_fountain",
        "teamBaronKills": "team_baron_kills",
        "teamDamagePercentage": "team_damage_percentage",
        "teamElderDragonKills": "team_elder_dragon_kills",
        "teamRiftHeraldKills": "team_rift_herald_kills",
        "tookLargeDamageSurvived": "took_large_damage_survived",
        "turretPlatesTaken": "turret_plates_taken",
        "turretsTakenWithRiftHerald": "turrets_taken_with_rift_herald",
        "turretTakedowns": "turret_takedowns",
        "twentyMinionsIn3SecondsCount": "twenty_minions_in_3_seconds_count",
        "twoWardsOneSweeperCount": "two_wards_one_sweeper_count",
        "unseenRecalls": "unseen_recalls",
        "wardsGuarded": "wards_guarded",
        "wardTakedowns": "ward_takedowns",
        "wardTakedownsBefore20M": "ward_takedowns_before_20m",
    }

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Challenges":
        """Create Challenges from API response."""
        kwargs: dict[str, Any] = {py_name: data.get(api_name) for api_name, py_name in cls._FIELD_MAP.items()}
        return cls(**kwargs)


@dataclass(frozen=True)
class Missions:
    """Represents participant missions."""

    player_score_0: int | None = None
    player_score_1: int | None = None
    player_score_2: int | None = None
    player_score_3: int | None = None
    player_score_4: int | None = None
    player_score_5: int | None = None
    player_score_6: int | None = None
    player_score_7: int | None = None
    player_score_8: int | None = None
    player_score_9: int | None = None
    player_score_10: int | None = None
    player_score_11: int | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Missions":
        """Create Missions from API response."""
        return cls(
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
        )
