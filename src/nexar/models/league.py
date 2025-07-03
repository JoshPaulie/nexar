"""League and ranking-related models."""

from dataclasses import dataclass
from typing import Any

from ..enums import Division, Queue, Tier


@dataclass(frozen=True)
class MiniSeries:
    """Represents mini series progress, colloquially known as 'promos'."""

    losses: int
    """Number of losses in promo."""

    progress: str
    """String showing the current progress where 'W' represents a win, 'L' represents a loss, and 'N' represents a game not yet played."""

    target: int
    """Number of wins required for promotion."""

    wins: int
    """Number of wins in promo."""

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
    """Represents a league entry for a player in a ranked queue."""

    league_id: str
    """Unique identifier for the league."""

    puuid: str
    """Player's universally unique identifier."""

    queue_type: Queue
    """Type of ranked queue."""

    tier: Tier
    """Current tier."""

    rank: Division
    """Current rank within the tier (not applicable for Master+)."""

    league_points: int
    """Current LP (League Points) in the rank."""

    wins: int
    """Total number of wins in the current season for this queue."""

    losses: int
    """Total number of losses in the current season for this queue."""

    hot_streak: bool
    """Whether the player is currently on a winning streak."""

    veteran: bool
    """Whether the player is a veteran (has played 100+ games in current tier)."""

    fresh_blood: bool
    """Whether the player is new to their current tier."""

    inactive: bool
    """Whether the player has been inactive and is subject to decay."""

    mini_series: MiniSeries | None = None
    """Promotion series data if currently in promos, None otherwise."""

    @property
    def total_games(self) -> int:
        """Total number of games played (wins + losses) in the current season for this queue."""
        return self.wins + self.losses

    @property
    def win_rate(self) -> float:
        """Win rate as a percentage (0.0 to 100.0). Returns 0.0 if no games played."""
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100.0

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LeagueEntry":
        """Create LeagueEntry from API response."""
        return cls(
            league_id=data["leagueId"],
            puuid=data["puuid"],
            queue_type=Queue(data["queueType"]),
            tier=Tier(data["tier"]),
            rank=Division(data["rank"]),
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
