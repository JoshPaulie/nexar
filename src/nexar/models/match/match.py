"""Match-related models."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .participant import Participant
    from .participant_list import ParticipantList
    from .team import Team

from nexar.enums import MapId, PlatformId, Queue

# Team ID constants
BLUE_TEAM_ID: int = 100
RED_TEAM_ID: int = 200


@dataclass(frozen=True)
class MatchMetadata:
    """Represents match metadata."""

    data_version: str
    """API data version for this match."""

    match_id: str
    """Unique identifier for the match."""

    participants: list[str]
    """List of participant PUUIDs in the match."""

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
    game_creation: datetime
    """Timestamp for when the game is created on the game server (i.e., the loading screen)."""

    game_duration: int
    """Game length in milliseconds (pre-11.20) or seconds (post-11.20)."""

    game_id: int
    """Unique game identifier."""

    game_mode: str
    """Game mode (e.g., CLASSIC, ARAM, etc.)."""

    game_start_timestamp: datetime
    """When the match started on the game server."""

    game_type: str
    """Game type (e.g., MATCHED_GAME, CUSTOM_GAME, etc.)."""

    game_version: str
    """Game version - first two parts determine the patch."""

    map_id: MapId
    """Map identifier (e.g., 11 for Summoner's Rift)."""

    platform_id: PlatformId
    """Platform where the match was played."""

    queue_id: Queue
    """Queue identifier."""

    participants: "ParticipantList"
    """List of all participants in the match."""

    teams: list["Team"]
    """List of team data (usually 2 teams)."""

    # Optional fields
    game_end_timestamp: datetime | None = None
    """When the match ended on the game server, if available."""

    game_name: str | None = None
    """
    Meta tag used by Riot.

    Example: teambuilder-match-5318386826
    """

    tournament_code: str | None = None
    """Tournament code used to generate the match, if applicable."""

    end_of_game_result: str | None = None
    """Indicates if game ended in termination or other special condition."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "MatchInfo":
        """Create MatchInfo from API response."""
        from .participant import Participant
        from .participant_list import ParticipantList
        from .team import Team

        return cls(
            game_creation=datetime.fromtimestamp(data["gameCreation"] / 1000, tz=UTC),
            game_duration=data["gameDuration"],
            game_id=data["gameId"],
            game_mode=data["gameMode"],
            game_start_timestamp=datetime.fromtimestamp(
                data["gameStartTimestamp"] / 1000,
                tz=UTC,
            ),
            game_type=data["gameType"],
            game_version=data["gameVersion"],
            map_id=MapId(data["mapId"]),
            platform_id=PlatformId(data["platformId"]),
            queue_id=Queue(data["queueId"]),
            participants=ParticipantList(
                Participant.from_api_response(participant) for participant in data["participants"]
            ),
            teams=[Team.from_api_response(team) for team in data["teams"]],
            game_end_timestamp=datetime.fromtimestamp(data["gameEndTimestamp"] / 1000, tz=UTC)
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
    """Match metadata including match ID and participant list."""

    info: MatchInfo
    """Detailed match information including participants and teams."""

    @property
    def participants(self) -> "ParticipantList":
        """Get all participants in the match."""
        return self.info.participants

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
