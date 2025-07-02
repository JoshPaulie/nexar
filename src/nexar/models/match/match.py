"""Match-related models."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .participant import Participant
    from .team import Team, TeamsInfo


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
    participants: list["Participant"]  # List of participants
    teams: list["Team"]  # List of teams

    # Optional fields
    game_end_timestamp: datetime | None = None  # When match ends on the game server
    game_name: str | None = None
    tournament_code: str | None = None  # Tournament code used to generate the match
    end_of_game_result: str | None = None  # Indicates if game ended in termination

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "MatchInfo":
        """Create MatchInfo from API response."""
        from .participant import Participant
        from .team import Team

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
class Match:
    """Represents a complete match."""

    metadata: MatchMetadata
    info: MatchInfo

    @property
    def participants(self) -> list["Participant"]:
        """Get all participants in the match."""
        return self.info.participants

    @property
    def teams(self) -> "TeamsInfo":
        """Get enhanced team information with participants grouped by side."""
        from .team import TeamInfo, TeamsInfo

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

    def __iter__(self) -> Iterator["Participant"]:
        """Allow iteration over participants."""
        return iter(self.participants)

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Match":
        """Create Match from API response."""
        return cls(
            metadata=MatchMetadata.from_api_response(data["metadata"]),
            info=MatchInfo.from_api_response(data["info"]),
        )
