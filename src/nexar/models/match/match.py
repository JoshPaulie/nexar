"""Match-related models."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from nexar.enums import MapId, PlatformId, Queue

from .participant_list import ParticipantList
from .team import Team

# Patch in which ``gameDuration`` switched from milliseconds to seconds.
GAME_DURATION_SECONDS_SINCE: tuple[int, int] = (11, 20)


def game_duration_in_seconds(game_duration: int, game_version: str) -> int:
    """
    Normalize a raw ``gameDuration`` value to seconds.

    Riot reported match durations in milliseconds up to patch 11.19 and in
    seconds from patch 11.20 onwards. The patch is read from the first two
    ``.``-separated segments of ``gameVersion`` (``11.19.1.1`` -> 11.19) and
    compared numerically, so ``11.9`` correctly sorts before ``11.20``.

    Args:
        game_duration: Raw ``gameDuration`` value from the API response.
        game_version: Raw ``gameVersion`` value (e.g. ``14.23.654.12``).

    Returns:
        The duration in whole seconds. Milliseconds are divided by 1000.

    Notes:
        A ``gameVersion`` that is empty or does not begin with two integer
        segments cannot be dated, so the raw value is returned untouched
        instead of guessing. A payload with no ``gameVersion`` key at all
        still raises ``KeyError`` from ``from_api_response``: the field is
        required, and its absence is not silently defaulted.

    """
    parts = game_version.split(".")
    try:
        patch = (int(parts[0]), int(parts[1]))
    except (IndexError, ValueError):
        return game_duration
    if patch < GAME_DURATION_SECONDS_SINCE:
        return game_duration // 1000
    return game_duration


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
    """Game length in seconds.

    Normalized at parse time: Riot reports milliseconds before patch 11.20 and
    seconds from 11.20 onwards, and both are converted to seconds here (see
    :func:`game_duration_in_seconds`).
    """

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

    participants: ParticipantList
    """List of all participants in the match."""

    teams: list[Team]
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
            game_duration=game_duration_in_seconds(data["gameDuration"], data["gameVersion"]),
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

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Match":
        """Create Match from API response."""
        return cls(
            metadata=MatchMetadata.from_api_response(data["metadata"]),
            info=MatchInfo.from_api_response(data["info"]),
        )
