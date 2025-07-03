"""League and ranking-related models."""

from typing import Any

from ..enums import Division, Queue, Tier


class MiniSeries:
    """Represents mini series progress, colloquially known as 'promos'."""

    def __init__(self, losses: int, progress: str, target: int, wins: int):
        self._losses = losses
        self._progress = progress
        self._target = target
        self._wins = wins

    @property
    def losses(self) -> int:
        """Number of losses in promo."""
        return self._losses

    @property
    def progress(self) -> str:
        """String showing the current progress where 'W' represents a win, 'L' represents a loss, and 'N' represents a game not yet played."""
        return self._progress

    @property
    def target(self) -> int:
        """Number of wins required for promotion."""
        return self._target

    @property
    def wins(self) -> int:
        """Number of wins in promo."""
        return self._wins

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "MiniSeries":
        """Create MiniSeries from API response."""
        return cls(
            losses=data["losses"],
            progress=data["progress"],
            target=data["target"],
            wins=data["wins"],
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, MiniSeries):
            return NotImplemented
        return (
            self.losses == other.losses
            and self.progress == other.progress
            and self.target == other.target
            and self.wins == other.wins
        )

    def __repr__(self) -> str:
        return f"MiniSeries(losses={self.losses}, progress='{self.progress}', target={self.target}, wins={self.wins})"


class LeagueEntry:
    """Represents a league entry for a player in a ranked queue."""

    def __init__(
        self,
        league_id: str,
        puuid: str,
        queue_type: Queue,
        tier: Tier,
        rank: Division,
        league_points: int,
        wins: int,
        losses: int,
        hot_streak: bool,
        veteran: bool,
        fresh_blood: bool,
        inactive: bool,
        mini_series: MiniSeries | None = None,
    ):
        self._league_id = league_id
        self._puuid = puuid
        self._queue_type = queue_type
        self._tier = tier
        self._rank = rank
        self._league_points = league_points
        self._wins = wins
        self._losses = losses
        self._hot_streak = hot_streak
        self._veteran = veteran
        self._fresh_blood = fresh_blood
        self._inactive = inactive
        self._mini_series = mini_series

    @property
    def league_id(self) -> str:
        """Unique identifier for the league."""
        return self._league_id

    @property
    def puuid(self) -> str:
        """Player's universally unique identifier."""
        return self._puuid

    @property
    def queue_type(self) -> Queue:
        """Type of ranked queue."""
        return self._queue_type

    @property
    def tier(self) -> Tier:
        """Current tier."""
        return self._tier

    @property
    def rank(self) -> Division:
        """Current rank within the tier (not applicable for Master+)."""
        return self._rank

    @property
    def league_points(self) -> int:
        """Current LP (League Points) in the rank."""
        return self._league_points

    @property
    def wins(self) -> int:
        """Total number of wins in the current season for this queue."""
        return self._wins

    @property
    def losses(self) -> int:
        """Total number of losses in the current season for this queue."""
        return self._losses

    @property
    def hot_streak(self) -> bool:
        """Whether the player is currently on a winning streak."""
        return self._hot_streak

    @property
    def veteran(self) -> bool:
        """Whether the player is a veteran (has played 100+ games in current tier)."""
        return self._veteran

    @property
    def fresh_blood(self) -> bool:
        """Whether the player is new to their current tier."""
        return self._fresh_blood

    @property
    def inactive(self) -> bool:
        """Whether the player has been inactive and is subject to decay."""
        return self._inactive

    @property
    def mini_series(self) -> MiniSeries | None:
        """Promotion series data if currently in promos, None otherwise."""
        return self._mini_series

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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return (
            self.league_id == other.league_id
            and self.puuid == other.puuid
            and self.queue_type == other.queue_type
            and self.tier == other.tier
            and self.rank == other.rank
            and self.league_points == other.league_points
            and self.wins == other.wins
            and self.losses == other.losses
            and self.hot_streak == other.hot_streak
            and self.veteran == other.veteran
            and self.fresh_blood == other.fresh_blood
            and self.inactive == other.inactive
            and self.mini_series == other.mini_series
        )

    def __repr__(self) -> str:
        return f"LeagueEntry(league_id='{self.league_id}', puuid='{self.puuid}', queue_type={self.queue_type!r}, tier={self.tier!r}, rank={self.rank!r}, league_points={self.league_points}, wins={self.wins}, losses={self.losses}, hot_streak={self.hot_streak}, veteran={self.veteran}, fresh_blood={self.fresh_blood}, inactive={self.inactive}, mini_series={self.mini_series})"
