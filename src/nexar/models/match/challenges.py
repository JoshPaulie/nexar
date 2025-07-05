"""Challenge and mission-related models."""

from dataclasses import dataclass
from typing import Any


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

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Challenges":
        """Create Challenges from API response."""
        return cls(
            kda=data.get("kda"),
            kill_participation=data.get("killParticipation"),
            damage_per_minute=data.get("damagePerMinute"),
            gold_per_minute=data.get("goldPerMinute"),
            vision_score_per_minute=data.get("visionScorePerMinute"),
            twelve_assist_streak_count=data.get("12AssistStreakCount"),
            baron_buff_gold_advantage_over_threshold=data.get(
                "baronBuffGoldAdvantageOverThreshold",
            ),
            control_ward_time_coverage_in_river_or_enemy_half=data.get(
                "controlWardTimeCoverageInRiverOrEnemyHalf",
            ),
            earliest_baron=data.get("earliestBaron"),
            earliest_dragon_takedown=data.get("earliestDragonTakedown"),
            earliest_elder_dragon=data.get("earliestElderDragon"),
            early_laning_phase_gold_exp_advantage=data.get(
                "earlyLaningPhaseGoldExpAdvantage",
            ),
            faster_support_quest_completion=data.get("fasterSupportQuestCompletion"),
            fastest_legendary=data.get("fastestLegendary"),
            had_afk_teammate=data.get("hadAfkTeammate"),
            highest_champion_damage=data.get("highestChampionDamage"),
            highest_crowd_control_score=data.get("highestCrowdControlScore"),
            highest_ward_kills=data.get("highestWardKills"),
            jungler_kills_early_jungle=data.get("junglerKillsEarlyJungle"),
            kills_on_laners_early_jungle_as_jungler=data.get(
                "killsOnLanersEarlyJungleAsJungler",
            ),
            laning_phase_gold_exp_advantage=data.get("laningPhaseGoldExpAdvantage"),
            legendary_count=data.get("legendaryCount"),
            max_cs_advantage_on_lane_opponent=data.get("maxCsAdvantageOnLaneOpponent"),
            max_level_lead_lane_opponent=data.get("maxLevelLeadLaneOpponent"),
            most_wards_destroyed_one_sweeper=data.get("mostWardsDestroyedOneSweeper"),
            mythic_item_used=data.get("mythicItemUsed"),
            played_champ_select_position=data.get("playedChampSelectPosition"),
            solo_turrets_lategame=data.get("soloTurretsLategame"),
            takedowns_first_25_minutes=data.get("takedownsFirst25Minutes"),
            teleport_takedowns=data.get("teleportTakedowns"),
            third_inhibitor_destroyed_time=data.get("thirdInhibitorDestroyedTime"),
            three_wards_one_sweeper_count=data.get("threeWardsOneSweeperCount"),
            vision_score_advantage_lane_opponent=data.get(
                "visionScoreAdvantageLaneOpponent",
            ),
            infernal_scale_pickup=data.get("InfernalScalePickup"),
            fist_bump_participation=data.get("fistBumpParticipation"),
            void_monster_kill=data.get("voidMonsterKill"),
            ability_uses=data.get("abilityUses"),
            aces_before_15_minutes=data.get("acesBefore15Minutes"),
            allied_jungle_monster_kills=data.get("alliedJungleMonsterKills"),
            baron_takedowns=data.get("baronTakedowns"),
            blast_cone_opposite_opponent_count=data.get(
                "blastConeOppositeOpponentCount",
            ),
            bounty_gold=data.get("bountyGold"),
            buffs_stolen=data.get("buffsStolen"),
            complete_support_quest_in_time=data.get("completeSupportQuestInTime"),
            control_wards_placed=data.get("controlWardsPlaced"),
            damage_taken_on_team_percentage=data.get("damageTakenOnTeamPercentage"),
            danced_with_rift_herald=data.get("dancedWithRiftHerald"),
            deaths_by_enemy_champs=data.get("deathsByEnemyChamps"),
            dodge_skill_shots_small_window=data.get("dodgeSkillShotsSmallWindow"),
            double_aces=data.get("doubleAces"),
            dragon_takedowns=data.get("dragonTakedowns"),
            legendary_item_used=data.get("legendaryItemUsed"),
            effective_heal_and_shielding=data.get("effectiveHealAndShielding"),
            elder_dragon_kills_with_opposing_soul=data.get(
                "elderDragonKillsWithOpposingSoul",
            ),
            elder_dragon_multikills=data.get("elderDragonMultikills"),
            enemy_champion_immobilizations=data.get("enemyChampionImmobilizations"),
            enemy_jungle_monster_kills=data.get("enemyJungleMonsterKills"),
            epic_monster_kills_near_enemy_jungler=data.get(
                "epicMonsterKillsNearEnemyJungler",
            ),
            epic_monster_kills_within_30_seconds_of_spawn=data.get(
                "epicMonsterKillsWithin30SecondsOfSpawn",
            ),
            epic_monster_steals=data.get("epicMonsterSteals"),
            epic_monster_stolen_without_smite=data.get("epicMonsterStolenWithoutSmite"),
            first_turret_killed=data.get("firstTurretKilled"),
            first_turret_killed_time=data.get("firstTurretKilledTime"),
            flawless_aces=data.get("flawlessAces"),
            full_team_takedown=data.get("fullTeamTakedown"),
            game_length=data.get("gameLength"),
            get_takedowns_in_all_lanes_early_jungle_as_laner=data.get(
                "getTakedownsInAllLanesEarlyJungleAsLaner",
            ),
            had_open_nexus=data.get("hadOpenNexus"),
            immobilize_and_kill_with_ally=data.get("immobilizeAndKillWithAlly"),
            initial_buff_count=data.get("initialBuffCount"),
            initial_crab_count=data.get("initialCrabCount"),
            jungle_cs_before_10_minutes=data.get("jungleCsBefore10Minutes"),
            jungler_takedowns_near_damaged_epic_monster=data.get(
                "junglerTakedownsNearDamagedEpicMonster",
            ),
            kill_after_hidden_with_ally=data.get("killAfterHiddenWithAlly"),
            killed_champ_took_full_team_damage_survived=data.get(
                "killedChampTookFullTeamDamageSurvived",
            ),
            killing_sprees=data.get("killingSprees"),
            kills_near_enemy_turret=data.get("killsNearEnemyTurret"),
            kills_on_other_lanes_early_jungle_as_laner=data.get(
                "killsOnOtherLanesEarlyJungleAsLaner",
            ),
            kills_on_recently_healed_by_aram_pack=data.get(
                "killsOnRecentlyHealedByAramPack",
            ),
            kills_under_own_turret=data.get("killsUnderOwnTurret"),
            kills_with_help_from_epic_monster=data.get("killsWithHelpFromEpicMonster"),
            knock_enemy_into_team_and_kill=data.get("knockEnemyIntoTeamAndKill"),
            k_turrets_destroyed_before_plates_fall=data.get(
                "kTurretsDestroyedBeforePlatesFall",
            ),
            land_skill_shots_early_game=data.get("landSkillShotsEarlyGame"),
            lane_minions_first_10_minutes=data.get("laneMinionsFirst10Minutes"),
            lost_an_inhibitor=data.get("lostAnInhibitor"),
            max_kill_deficit=data.get("maxKillDeficit"),
            mejais_full_stack_in_time=data.get("mejaisFullStackInTime"),
            more_enemy_jungle_than_opponent=data.get("moreEnemyJungleThanOpponent"),
            multi_kill_one_spell=data.get("multiKillOneSpell"),
            multikills=data.get("multikills"),
            multikills_after_aggressive_flash=data.get(
                "multikillsAfterAggressiveFlash",
            ),
            multi_turret_rift_herald_count=data.get("multiTurretRiftHeraldCount"),
            outer_turret_executes_before_10_minutes=data.get(
                "outerTurretExecutesBefore10Minutes",
            ),
            outnumbered_kills=data.get("outnumberedKills"),
            outnumbered_nexus_kill=data.get("outnumberedNexusKill"),
            perfect_dragon_souls_taken=data.get("perfectDragonSoulsTaken"),
            perfect_game=data.get("perfectGame"),
            pick_kill_with_ally=data.get("pickKillWithAlly"),
            poro_explosions=data.get("poroExplosions"),
            quick_cleanse=data.get("quickCleanse"),
            quick_first_turret=data.get("quickFirstTurret"),
            quick_solo_kills=data.get("quickSoloKills"),
            rift_herald_takedowns=data.get("riftHeraldTakedowns"),
            save_ally_from_death=data.get("saveAllyFromDeath"),
            scuttle_crab_kills=data.get("scuttleCrabKills"),
            shortest_time_to_ace_from_first_takedown=data.get(
                "shortestTimeToAceFromFirstTakedown",
            ),
            skillshots_dodged=data.get("skillshotsDodged"),
            skillshots_hit=data.get("skillshotsHit"),
            snowballs_hit=data.get("snowballsHit"),
            solo_baron_kills=data.get("soloBaronKills"),
            swarm_defeat_aatrox=data.get("SWARM_DefeatAatrox"),
            swarm_defeat_briar=data.get("SWARM_DefeatBriar"),
            swarm_defeat_mini_bosses=data.get("SWARM_DefeatMiniBosses"),
            swarm_evolve_weapon=data.get("SWARM_EvolveWeapon"),
            swarm_have_3_passives=data.get("SWARM_Have3Passives"),
            swarm_kill_enemy=data.get("SWARM_KillEnemy"),
            swarm_pickup_gold=data.get("SWARM_PickupGold"),
            swarm_reach_level_50=data.get("SWARM_ReachLevel50"),
            swarm_survive_15_min=data.get("SWARM_Survive15Min"),
            swarm_win_with_5_evolved_weapons=data.get("SWARM_WinWith5EvolvedWeapons"),
            solo_kills=data.get("soloKills"),
            stealth_wards_placed=data.get("stealthWardsPlaced"),
            survived_single_digit_hp_count=data.get("survivedSingleDigitHpCount"),
            survived_three_immobilizes_in_fight=data.get(
                "survivedThreeImmobilizesInFight",
            ),
            takedown_on_first_turret=data.get("takedownOnFirstTurret"),
            takedowns=data.get("takedowns"),
            takedowns_after_gaining_level_advantage=data.get(
                "takedownsAfterGainingLevelAdvantage",
            ),
            takedowns_before_jungle_minion_spawn=data.get(
                "takedownsBeforeJungleMinionSpawn",
            ),
            takedowns_first_x_minutes=data.get("takedownsFirstXMinutes"),
            takedowns_in_alcove=data.get("takedownsInAlcove"),
            takedowns_in_enemy_fountain=data.get("takedownsInEnemyFountain"),
            team_baron_kills=data.get("teamBaronKills"),
            team_damage_percentage=data.get("teamDamagePercentage"),
            team_elder_dragon_kills=data.get("teamElderDragonKills"),
            team_rift_herald_kills=data.get("teamRiftHeraldKills"),
            took_large_damage_survived=data.get("tookLargeDamageSurvived"),
            turret_plates_taken=data.get("turretPlatesTaken"),
            turrets_taken_with_rift_herald=data.get("turretsTakenWithRiftHerald"),
            turret_takedowns=data.get("turretTakedowns"),
            twenty_minions_in_3_seconds_count=data.get("twentyMinionsIn3SecondsCount"),
            two_wards_one_sweeper_count=data.get("twoWardsOneSweeperCount"),
            unseen_recalls=data.get("unseenRecalls"),
            wards_guarded=data.get("wardsGuarded"),
            ward_takedowns=data.get("wardTakedowns"),
            ward_takedowns_before_20m=data.get("wardTakedownsBefore20M"),
        )


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
