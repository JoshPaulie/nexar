"""Domain models for Riot API responses."""

from dataclasses import dataclass
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
    revision_date: int
    summoner_level: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Summoner":
        """Create Summoner from API response."""
        return cls(
            id=data["id"],
            puuid=data["puuid"],
            profile_icon_id=data["profileIconId"],
            revision_date=data["revisionDate"],
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

    # Game stats
    kills: int
    deaths: int
    assists: int
    champion_level: int
    gold_earned: int
    gold_spent: int
    total_damage_dealt_to_champions: int
    total_damage_taken: int
    vision_score: int

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

    # Game outcome
    win: bool

    # Complex nested objects
    perks: Perks | None = None
    challenges: Challenges | None = None
    missions: Missions | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Participant":
        """Create Participant from API response."""
        return cls(
            puuid=data["puuid"],
            summoner_name=data["summonerName"],
            champion_id=data["championId"],
            champion_name=data["championName"],
            team_id=data["teamId"],
            participant_id=data["participantId"],
            kills=data["kills"],
            deaths=data["deaths"],
            assists=data["assists"],
            champion_level=data["champLevel"],
            gold_earned=data["goldEarned"],
            gold_spent=data["goldSpent"],
            total_damage_dealt_to_champions=data["totalDamageDealtToChampions"],
            total_damage_taken=data["totalDamageTaken"],
            vision_score=data["visionScore"],
            item_0=data["item0"],
            item_1=data["item1"],
            item_2=data["item2"],
            item_3=data["item3"],
            item_4=data["item4"],
            item_5=data["item5"],
            item_6=data["item6"],
            individual_position=data["individualPosition"],
            team_position=data["teamPosition"],
            lane=data["lane"],
            role=data["role"],
            win=data["win"],
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
    game_creation: int
    game_duration: int
    game_id: int
    game_mode: str
    game_start_timestamp: int
    game_type: str
    game_version: str
    map_id: int
    platform_id: str
    queue_id: int

    # Optional fields
    game_end_timestamp: int | None = None
    game_name: str | None = None
    tournament_code: str | None = None
    end_of_game_result: str | None = None

    # Participants and teams
    participants: list[Participant] = None
    teams: list[Team] = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "MatchInfo":
        """Create MatchInfo from API response."""
        return cls(
            game_creation=data["gameCreation"],
            game_duration=data["gameDuration"],
            game_id=data["gameId"],
            game_mode=data["gameMode"],
            game_start_timestamp=data["gameStartTimestamp"],
            game_type=data["gameType"],
            game_version=data["gameVersion"],
            map_id=data["mapId"],
            platform_id=data["platformId"],
            queue_id=data["queueId"],
            game_end_timestamp=data.get("gameEndTimestamp"),
            game_name=data.get("gameName"),
            tournament_code=data.get("tournamentCode"),
            end_of_game_result=data.get("endOfGameResult"),
            participants=[
                Participant.from_api_response(participant)
                for participant in data["participants"]
            ],
            teams=[Team.from_api_response(team) for team in data["teams"]],
        )


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

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Match":
        """Create Match from API response."""
        return cls(
            metadata=MatchMetadata.from_api_response(data["metadata"]),
            info=MatchInfo.from_api_response(data["info"]),
        )
