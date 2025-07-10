"""League and ranking-related models."""

from dataclasses import dataclass
from typing import Any

from nexar.enums import QueueId, RankDivision, RankTier


@dataclass(frozen=True)
class MiniSeries:
    """Represents mini series progress, colloquially known as 'promos'."""

    losses: int
    """Number of losses in promo."""

    progress: str
    """
    String showing the current progress where 'W' represents a win, 'L' represents a loss,
    and 'N' represents a game not yet played.
    """

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

    queue_type: QueueId
    """Type of ranked queue."""

    tier: RankTier
    """Current tier (IRON, BRONZE, ..., CHALLENGER)."""

    rank: RankDivision
    """Current rank (IV, III, etc) within the tier (not applicable for Master+)."""

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

    @property
    def rank_value(self) -> int:
        """A unique integer representing the combined tier and rank for comparison purposes."""
        tier_order = list(RankTier)
        rank_order = list(RankDivision)
        tier_index = tier_order.index(self.tier)
        # For Master+ tiers, rank is always Division.I
        if self.tier in {RankTier.MASTER, RankTier.GRANDMASTER, RankTier.CHALLENGER}:
            rank_index = 0
        else:
            # Reverse the division index: I=0, II=1, III=2, IV=3 (I is highest)
            rank_index = len(rank_order) - 1 - rank_order.index(self.rank)
        return tier_index * len(rank_order) + rank_index

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_value < other.rank_value

    def __le__(self, other: object) -> bool:
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_value <= other.rank_value

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_value > other.rank_value

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_value >= other.rank_value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_value == other.rank_value

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_value != other.rank_value

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LeagueEntry":
        """Create LeagueEntry from API response."""
        # Map string queue types from API to QueueId enums
        queue_type_mapping = {
            "RANKED_SOLO_5x5": QueueId.RANKED_SOLO_5x5,
            "RANKED_FLEX_SR": QueueId.RANKED_FLEX_SR,
        }

        queue_type_str = data["queueType"]
        if queue_type_str not in queue_type_mapping:
            msg = f"Unknown queue type: {queue_type_str}"
            raise ValueError(msg)

        return cls(
            league_id=data["leagueId"],
            puuid=data["puuid"],
            queue_type=queue_type_mapping[queue_type_str],
            tier=RankTier(data["tier"]),
            rank=RankDivision(data["rank"]),
            league_points=data["leaguePoints"],
            wins=data["wins"],
            losses=data["losses"],
            hot_streak=data["hotStreak"],
            veteran=data["veteran"],
            fresh_blood=data["freshBlood"],
            inactive=data["inactive"],
            mini_series=MiniSeries.from_api_response(data["miniSeries"]) if data.get("miniSeries") else None,
        )
