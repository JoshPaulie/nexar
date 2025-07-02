"""Domain models for Riot API responses."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class RiotAccount:
    """Represents a Riot account."""

    puuid: str
    game_name: str
    tag_line: str

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "RiotAccount":
        """Create RiotAccount from API response."""
        return cls(
            puuid=data["puuid"], game_name=data["gameName"], tag_line=data["tagLine"]
        )


@dataclass(frozen=True)
class Summoner:
    """Represents a League of Legends summoner."""

    id: str
    puuid: str
    profile_icon_id: int
    revision_date: datetime  # Last modification date of summoner
    summoner_level: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Summoner":
        """Create Summoner from API response."""
        return cls(
            id=data["id"],
            puuid=data["puuid"],
            profile_icon_id=data["profileIconId"],
            revision_date=datetime.fromtimestamp(data["revisionDate"] / 1000),
            summoner_level=data["summonerLevel"],
        )


@dataclass(frozen=True)
class PerkStyleSelection:
    """Represents a perk style selection."""

    perk: int
    var1: int
    var2: int
    var3: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "PerkStyleSelection":
        """Create PerkStyleSelection from API response."""
        return cls(
            perk=data["perk"],
            var1=data["var1"],
            var2=data["var2"],
            var3=data["var3"],
        )


@dataclass(frozen=True)
class PerkStyle:
    """Represents a perk style."""

    description: str
    selections: list["PerkStyleSelection"]
    style: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "PerkStyle":
        """Create PerkStyle from API response."""
        return cls(
            description=data["description"],
            selections=[
                PerkStyleSelection.from_api_response(selection)
                for selection in data["selections"]
            ],
            style=data["style"],
        )


@dataclass(frozen=True)
class PerkStats:
    """Represents perk stats."""

    defense: int
    flex: int
    offense: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "PerkStats":
        """Create PerkStats from API response."""
        return cls(
            defense=data["defense"],
            flex=data["flex"],
            offense=data["offense"],
        )


@dataclass(frozen=True)
class Perks:
    """Represents participant perks."""

    stat_perks: PerkStats
    styles: list[PerkStyle]

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Perks":
        """Create Perks from API response."""
        return cls(
            stat_perks=PerkStats.from_api_response(data["statPerks"]),
            styles=[PerkStyle.from_api_response(style) for style in data["styles"]],
        )


@dataclass(frozen=True)
class Challenges:
    """Represents participant challenges."""

    # Core challenge stats
    kda: float | None = None
    kill_participation: float | None = None
    damage_per_minute: float | None = None
    gold_per_minute: float | None = None
    vision_score_per_minute: float | None = None

    # Additional challenge fields can be added as needed
    # Using flexible approach since challenges have many optional fields

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Challenges":
        """Create Challenges from API response."""
        return cls(
            kda=data.get("kda"),
            kill_participation=data.get("killParticipation"),
            damage_per_minute=data.get("damagePerMinute"),
            gold_per_minute=data.get("goldPerMinute"),
            vision_score_per_minute=data.get("visionScorePerMinute"),
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


@dataclass(frozen=True)
class Participant:
    """Represents a match participant."""

    # Core participant data
    puuid: str
    summoner_name: str
    champion_id: int
    champion_name: str
    team_id: int
    participant_id: int

    # Basic stats
    kills: int
    deaths: int
    assists: int
    champion_level: int
    gold_earned: int
    gold_spent: int
    vision_score: int
    win: bool

    # Items
    item_0: int
    item_1: int
    item_2: int
    item_3: int
    item_4: int
    item_5: int
    item_6: int

    # Position and role
    individual_position: str
    team_position: str
    lane: str
    role: str

    # Ping stats
    all_in_pings: int
    assist_me_pings: int
    command_pings: int
    enemy_missing_pings: int
    enemy_vision_pings: int
    get_back_pings: int
    hold_pings: int
    need_vision_pings: int
    on_my_way_pings: int
    push_pings: int
    vision_cleared_pings: int

    # Kill stats
    baron_kills: int
    double_kills: int
    dragon_kills: int
    inhibitor_kills: int
    killing_sprees: int
    largest_killing_spree: int
    largest_multi_kill: int
    nexus_kills: int
    penta_kills: int
    quadra_kills: int
    triple_kills: int
    turret_kills: int
    unreal_kills: int

    # Damage stats
    damage_dealt_to_buildings: int
    damage_dealt_to_objectives: int
    damage_dealt_to_turrets: int
    damage_self_mitigated: int
    largest_critical_strike: int
    magic_damage_dealt: int
    magic_damage_dealt_to_champions: int
    magic_damage_taken: int
    physical_damage_dealt: int
    physical_damage_dealt_to_champions: int
    physical_damage_taken: int
    total_damage_dealt: int
    total_damage_dealt_to_champions: int
    total_damage_shielded_on_teammates: int
    total_damage_taken: int
    true_damage_dealt: int
    true_damage_dealt_to_champions: int
    true_damage_taken: int

    # Minion and jungle stats
    neutral_minions_killed: int
    total_ally_jungle_minions_killed: int
    total_enemy_jungle_minions_killed: int
    total_minions_killed: int

    # Healing and support stats
    total_heal: int
    total_heals_on_teammates: int
    total_units_healed: int

    # Time stats
    longest_time_spent_living: int
    time_ccing_others: int
    time_played: int
    total_time_cc_dealt: int
    total_time_spent_dead: int

    # Ward and vision stats
    detector_wards_placed: int
    sight_wards_bought_in_game: int
    vision_wards_bought_in_game: int
    wards_killed: int
    wards_placed: int

    # Spell casts
    spell_1_casts: int
    spell_2_casts: int
    spell_3_casts: int
    spell_4_casts: int
    summoner_1_casts: int
    summoner_1_id: int
    summoner_2_casts: int
    summoner_2_id: int

    # Structure stats
    inhibitor_takedowns: int
    inhibitors_lost: int
    nexus_takedowns: int
    nexus_lost: int
    turret_takedowns: int
    turrets_lost: int

    # Objectives
    objectives_stolen: int
    objectives_stolen_assists: int

    # Game state
    bounty_level: int
    champ_experience: int
    champion_transform: int
    consumables_purchased: int
    eligible_for_progression: bool
    first_blood_assist: bool
    first_blood_kill: bool
    first_tower_assist: bool
    first_tower_kill: bool
    game_ended_in_early_surrender: bool
    game_ended_in_surrender: bool
    items_purchased: int
    placement: int
    profile_icon: int
    summoner_id: str
    summoner_level: int
    team_early_surrendered: bool

    # Riot ID
    riot_id_game_name: str | None = None
    riot_id_tagline: str | None = None

    # Player scores (from missions)
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

    # Player augments (for specific game modes)
    player_augment_1: int | None = None
    player_augment_2: int | None = None
    player_augment_3: int | None = None
    player_augment_4: int | None = None
    player_subteam_id: int | None = None
    subteam_placement: int | None = None

    # Complex nested objects
    perks: Perks | None = None
    challenges: Challenges | None = None
    missions: Missions | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Participant":
        """Create Participant from API response."""
        return cls(
            # Core participant data
            puuid=data["puuid"],
            summoner_name=data["summonerName"],
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
            individual_position=data["individualPosition"],
            team_position=data["teamPosition"],
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
            bounty_level=data["bountyLevel"],
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


@dataclass(frozen=True)
class Ban:
    """Represents a champion ban."""

    champion_id: int
    pick_turn: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Ban":
        """Create Ban from API response."""
        return cls(
            champion_id=data["championId"],
            pick_turn=data["pickTurn"],
        )


@dataclass(frozen=True)
class Objective:
    """Represents an objective (baron, dragon, etc.)."""

    first: bool
    kills: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Objective":
        """Create Objective from API response."""
        return cls(
            first=data["first"],
            kills=data["kills"],
        )


@dataclass(frozen=True)
class Objectives:
    """Represents team objectives."""

    baron: Objective
    champion: Objective
    dragon: Objective
    horde: Objective
    inhibitor: Objective
    rift_herald: Objective
    tower: Objective

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Objectives":
        """Create Objectives from API response."""
        return cls(
            baron=Objective.from_api_response(data["baron"]),
            champion=Objective.from_api_response(data["champion"]),
            dragon=Objective.from_api_response(data["dragon"]),
            horde=Objective.from_api_response(data["horde"]),
            inhibitor=Objective.from_api_response(data["inhibitor"]),
            rift_herald=Objective.from_api_response(data["riftHerald"]),
            tower=Objective.from_api_response(data["tower"]),
        )


@dataclass(frozen=True)
class Team:
    """Represents a team in a match."""

    team_id: int
    win: bool
    bans: list[Ban]
    objectives: Objectives

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Team":
        """Create Team from API response."""
        return cls(
            team_id=data["teamId"],
            win=data["win"],
            bans=[Ban.from_api_response(ban) for ban in data["bans"]],
            objectives=Objectives.from_api_response(data["objectives"]),
        )


@dataclass(frozen=True)
class MatchInfo:
    """Represents match info."""

    # Core match data
    game_creation: datetime  # When the game is created on the game server
    game_duration: int  # Game length (milliseconds pre-11.20, seconds post-11.20)
    game_id: int
    game_mode: str
    game_start_timestamp: datetime  # When match starts on the game server
    game_type: str
    game_version: str  # First two parts determine the patch
    map_id: int
    platform_id: str  # Platform where the match was played
    queue_id: int
    participants: list[Participant]  # List of participants
    teams: list[Team]  # List of teams

    # Optional fields
    game_end_timestamp: datetime | None = None  # When match ends on the game server
    game_name: str | None = None
    tournament_code: str | None = None  # Tournament code used to generate the match
    end_of_game_result: str | None = None  # Indicates if game ended in termination

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "MatchInfo":
        """Create MatchInfo from API response."""
        return cls(
            game_creation=datetime.fromtimestamp(data["gameCreation"] / 1000),
            game_duration=data["gameDuration"],
            game_id=data["gameId"],
            game_mode=data["gameMode"],
            game_start_timestamp=datetime.fromtimestamp(
                data["gameStartTimestamp"] / 1000
            ),
            game_type=data["gameType"],
            game_version=data["gameVersion"],
            map_id=data["mapId"],
            platform_id=data["platformId"],
            queue_id=data["queueId"],
            participants=[
                Participant.from_api_response(participant)
                for participant in data["participants"]
            ],
            teams=[Team.from_api_response(team) for team in data["teams"]],
            game_end_timestamp=datetime.fromtimestamp(data["gameEndTimestamp"] / 1000)
            if data.get("gameEndTimestamp")
            else None,
            game_name=data.get("gameName"),
            tournament_code=data.get("tournamentCode"),
            end_of_game_result=data.get("endOfGameResult"),
        )


@dataclass(frozen=True)
class TeamInfo:
    """Enhanced team information with participants and aggregated stats."""

    team_id: int
    win: bool
    bans: list[Ban]
    objectives: Objectives
    participants: list[Participant]

    @property
    def total_damage(self) -> int:
        """Total damage dealt to champions by all team members."""
        return sum(p.total_damage_dealt_to_champions for p in self.participants)

    @property
    def total_damage_taken(self) -> int:
        """Total damage taken by all team members."""
        return sum(p.total_damage_taken for p in self.participants)

    @property
    def total_gold_earned(self) -> int:
        """Total gold earned by all team members."""
        return sum(p.gold_earned for p in self.participants)

    @property
    def total_kills(self) -> int:
        """Total kills by all team members."""
        return sum(p.kills for p in self.participants)

    @property
    def total_deaths(self) -> int:
        """Total deaths by all team members."""
        return sum(p.deaths for p in self.participants)

    @property
    def total_assists(self) -> int:
        """Total assists by all team members."""
        return sum(p.assists for p in self.participants)

    @property
    def total_vision_score(self) -> int:
        """Total vision score by all team members."""
        return sum(p.vision_score for p in self.participants)


@dataclass(frozen=True)
class TeamsInfo:
    """Container for blue and red team information."""

    blue: TeamInfo
    red: TeamInfo

    def __iter__(self) -> Iterator[TeamInfo]:
        """Allow iteration over teams."""
        yield self.blue
        yield self.red


@dataclass(frozen=True)
class MatchMetadata:
    """Represents match metadata."""

    data_version: str
    match_id: str
    participants: list[str]  # List of PUUIDs

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "MatchMetadata":
        """Create MatchMetadata from API response."""
        return cls(
            data_version=data["dataVersion"],
            match_id=data["matchId"],
            participants=data["participants"],
        )


@dataclass(frozen=True)
class Match:
    """Represents a complete match."""

    metadata: MatchMetadata
    info: MatchInfo

    @property
    def participants(self) -> list[Participant]:
        """Get all participants in the match."""
        return self.info.participants

    @property
    def teams(self) -> TeamsInfo:
        """Get enhanced team information with participants grouped by side."""
        # Separate participants by team ID (100 = blue, 200 = red)
        blue_participants = [p for p in self.participants if p.team_id == 100]
        red_participants = [p for p in self.participants if p.team_id == 200]

        # Find the corresponding team data
        blue_team_data = next(t for t in self.info.teams if t.team_id == 100)
        red_team_data = next(t for t in self.info.teams if t.team_id == 200)

        blue_team = TeamInfo(
            team_id=blue_team_data.team_id,
            win=blue_team_data.win,
            bans=blue_team_data.bans,
            objectives=blue_team_data.objectives,
            participants=blue_participants,
        )

        red_team = TeamInfo(
            team_id=red_team_data.team_id,
            win=red_team_data.win,
            bans=red_team_data.bans,
            objectives=red_team_data.objectives,
            participants=red_participants,
        )

        return TeamsInfo(blue=blue_team, red=red_team)

    def __iter__(self) -> Iterator[Participant]:
        """Allow iteration over participants."""
        return iter(self.participants)

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Match":
        """Create Match from API response."""
        return cls(
            metadata=MatchMetadata.from_api_response(data["metadata"]),
            info=MatchInfo.from_api_response(data["info"]),
        )
