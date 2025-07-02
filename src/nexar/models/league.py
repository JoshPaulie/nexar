"""League and ranking-related models."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MiniSeries:
    """Represents mini series progress."""

    losses: int
    progress: str
    target: int
    wins: int

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "MiniSeries":
        """Create MiniSeries from API response."""
        return cls(
            losses=data["losses"],
            progress=data["progress"],
            target=data["target"],
            wins=data["wins"],
        )


@dataclass(frozen=True)
class LeagueEntry:
    """Represents a league entry for a player."""

    league_id: str
    puuid: str
    queue_type: str
    tier: str
    rank: str
    league_points: int
    wins: int
    losses: int
    hot_streak: bool
    veteran: bool
    fresh_blood: bool
    inactive: bool
    mini_series: MiniSeries | None = None

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LeagueEntry":
        """Create LeagueEntry from API response."""
        return cls(
            league_id=data["leagueId"],
            puuid=data["puuid"],
            queue_type=data["queueType"],
            tier=data["tier"],
            rank=data["rank"],
            league_points=data["leaguePoints"],
            wins=data["wins"],
            losses=data["losses"],
            hot_streak=data["hotStreak"],
            veteran=data["veteran"],
            fresh_blood=data["freshBlood"],
            inactive=data["inactive"],
            mini_series=MiniSeries.from_api_response(data["miniSeries"])
            if data.get("miniSeries")
            else None,
        )
