"""League and ranking-related models."""

import logging
from dataclasses import dataclass
from typing import Any

from nexar.enums import Queue, RankDivision, RankTier

logger = logging.getLogger("nexar")


# Map string queue types from the API to Queue enums; unknown strings degrade
# to Queue.UNKNOWN rather than conflating new ranked queues with CUSTOM games.
_QUEUE_TYPE_MAP = {
    "RANKED_SOLO_5x5": Queue.RANKED_SOLO_5x5,
    "RANKED_FLEX_SR": Queue.RANKED_FLEX_SR,
}


def _queue_from_string(queue_str: str) -> Queue:
    """Map an API queue string to a Queue enum, degrading unknown strings to UNKNOWN."""
    if queue_str not in _QUEUE_TYPE_MAP:
        # A new queue string from Riot is expected forward drift, not an anomaly.
        logger.debug("Unknown queue type '%s' in league payload. Defaulting to UNKNOWN.", queue_str)
        return Queue.UNKNOWN
    return _QUEUE_TYPE_MAP[queue_str]


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
    """Unique identifier for the league. Empty when Riot omits it (the by-puuid
    entries endpoint no longer returns it)."""

    puuid: str
    """Player's universally unique identifier."""

    queue_type: Queue
    """Type of ranked queue."""

    queue_type_raw: str
    """Original queue type string from the API (e.g. 'RANKED_SOLO_5x5').

    Useful for forward compatibility when Riot adds new queue types.
    """

    tier: RankTier
    """Current tier (IRON, BRONZE, ..., CHALLENGER)."""

    division: RankDivision
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
        """Win rate as a ratio (0.0 to 1.0). Returns 0.0 if no games played."""
        if self.total_games == 0:
            return 0.0
        return self.wins / self.total_games

    @property
    def rank_tuple(self) -> tuple[int, int]:
        """Returns (tier_index, league_points) for easy sorting by rank.

        ``RankDivision.EMPTY`` is a sentinel for apex/decayed entries that carry no
        division: it is excluded from the division scale so existing scores keep their
        historic numbering. Master+ entries are scored as if they sat above division I
        (they have no divisions), and an EMPTY division in a non-apex tier is scored as
        the lowest division rather than raising.
        """
        all_tiers = list(RankTier)
        divisions = [division for division in RankDivision if division is not RankDivision.EMPTY]
        tier_index = all_tiers.index(self.tier)

        # For Master+ tiers, rank is always Division.I
        if self.tier in {RankTier.MASTER, RankTier.GRANDMASTER, RankTier.CHALLENGER}:
            # Master+ tiers do not have divisions, so assign a division_score higher than any division
            division_score = len(divisions)  # This will be 4, higher than 0-3 for divisions
        elif self.division is RankDivision.EMPTY:
            # No division to place: treat as the bottom of the tier
            division_score = 0
        else:
            # Reverse the division index: I=0, II=1, III=2, IV=3 (I is highest)
            division_score = len(divisions) - 1 - divisions.index(self.division)

        # Combine tier and division into a single rank value, then add LP
        tier_division_score = tier_index * (len(divisions) + 1) + division_score
        return (tier_division_score, self.league_points)

    def is_higher_rank_than(self, other: "LeagueEntry") -> bool:
        """Compare if this entry has a higher rank than another."""
        return self.rank_tuple > other.rank_tuple

    def __lt__(self, other: object) -> bool:
        """Compare rank for sorting purposes."""
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_tuple < other.rank_tuple

    def __le__(self, other: object) -> bool:
        """Compare rank for sorting purposes."""
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_tuple <= other.rank_tuple

    def __gt__(self, other: object) -> bool:
        """Compare rank for sorting purposes."""
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_tuple > other.rank_tuple

    def __ge__(self, other: object) -> bool:
        """Compare rank for sorting purposes."""
        if not isinstance(other, LeagueEntry):
            return NotImplemented
        return self.rank_tuple >= other.rank_tuple

    def __str__(self) -> str:
        """Compact rank display, e.g. ``Gold IV 27LP``.

        Apex and decayed entries carry :attr:`RankDivision.EMPTY` and print
        without a division: ``Master 512LP``. An unranked queue never
        reaches this method at all: the by-puuid wire sends entries only
        for queues the player is ranked in (there is no UNRANKED tier), so
        an unranked player has no entry for the queue,
        :meth:`Player.get_solo_rank` returns None, and the caller prints
        its own unranked label.
        """
        if self.division is RankDivision.EMPTY:
            return f"{self.tier} {self.league_points}LP"
        return f"{self.tier} {self.division} {self.league_points}LP"

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LeagueEntry":
        """Create LeagueEntry from API response."""
        queue_type_str = data["queueType"]
        queue_type = _queue_from_string(queue_type_str)

        # Riot omits empty values: apex/decayed entries have no rank, and 0 LP/wins/losses
        # are absent rather than zero.
        rank_str = data.get("rank") or ""
        try:
            division = RankDivision(rank_str)
        except ValueError:
            logger.warning("Unknown division '%s' in league entry. Defaulting to EMPTY.", rank_str)
            division = RankDivision.EMPTY

        return cls(
            league_id=data.get("leagueId") or "",
            puuid=data["puuid"],
            queue_type=queue_type,
            queue_type_raw=queue_type_str,
            tier=RankTier(data["tier"]),
            division=division,
            league_points=data.get("leaguePoints", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            hot_streak=data.get("hotStreak", False),
            veteran=data.get("veteran", False),
            fresh_blood=data.get("freshBlood", False),
            inactive=data.get("inactive", False),
            mini_series=MiniSeries.from_api_response(data["miniSeries"]) if data.get("miniSeries") else None,
        )


@dataclass(frozen=True)
class LeagueItem:
    """A single player's standing inside an apex league (challenger/grandmaster/master).

    The live apex payloads are puuid-era shaped: entries carry ``puuid`` and no
    ``summonerId``/``summonerName`` (measured 2026-11-21). Unlike
    :class:`LeagueEntry` there is no ``queueType`` — the queue lives on the
    container :class:`LeagueList`.
    """

    puuid: str
    """Player's universally unique identifier."""

    division: RankDivision
    """Division placeholder the wire still sends on apex entries ('I'). EMPTY when omitted."""

    league_points: int
    """Current LP (League Points) in the ladder."""

    wins: int
    """Total number of wins in the current season for this queue."""

    losses: int
    """Total number of losses in the current season for this queue."""

    hot_streak: bool
    """Whether the player is currently on a winning streak."""

    veteran: bool
    """Whether the player is a veteran (has played 100+ games in the tier)."""

    fresh_blood: bool
    """Whether the player is newly promoted into the tier."""

    inactive: bool
    """Whether the player has been inactive and is subject to decay."""

    mini_series: MiniSeries | None = None
    """Promotion series data if currently in promos, None otherwise (apex entries
    are never in promos on the live wire; the field exists because Riot's DTO
    declares it)."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LeagueItem":
        """Create LeagueItem from an apex-league entries element.

        Riot omits empty values, so everything except ``puuid`` parses with defaults.
        """
        rank_str = data.get("rank") or ""
        try:
            division = RankDivision(rank_str)
        except ValueError:
            logger.warning("Unknown division '%s' in apex league item. Defaulting to EMPTY.", rank_str)
            division = RankDivision.EMPTY

        return cls(
            puuid=data["puuid"],
            division=division,
            league_points=data.get("leaguePoints", 0),
            wins=data.get("wins", 0),
            losses=data.get("losses", 0),
            hot_streak=data.get("hotStreak", False),
            veteran=data.get("veteran", False),
            fresh_blood=data.get("freshBlood", False),
            inactive=data.get("inactive", False),
            mini_series=MiniSeries.from_api_response(data["miniSeries"]) if data.get("miniSeries") else None,
        )


@dataclass(frozen=True)
class LeagueList:
    """An apex league (challenger, grandmaster or master) for one ranked queue.

    Riot wraps the apex ladders in this small container; the ladder itself is
    not paginated — every entry arrives in one response, pre-sorted by league
    points. The live payload carries no ``leagueId`` and no ``name`` (both
    measured absent on every apex queue, 2026-11-21), so both parse as empty
    strings rather than raising.
    """

    league_id: str
    """Unique identifier for the league. Empty on the live surface."""

    tier: RankTier
    """The apex tier this league covers (CHALLENGER, GRANDMASTER or MASTER)."""

    name: str
    """League display name. Empty when Riot omits it (the live payload does)."""

    queue: Queue
    """Type of ranked queue the ladder covers."""

    queue_raw: str
    """Original queue string from the API (e.g. 'RANKED_SOLO_5x5').

    Useful for forward compatibility when Riot adds new queue types.
    """

    entries: tuple[LeagueItem, ...]
    """The full ladder, highest league points first (Riot pre-sorts it)."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LeagueList":
        """Create LeagueList from a league-list API response.

        ``tier`` is a direct identity read — an unknown tier string raises
        (deliberate, pinned by a test) rather than degrading the way an unknown
        queue string does.
        """
        queue_str = data.get("queue") or ""
        return cls(
            league_id=data.get("leagueId") or "",
            tier=RankTier(data["tier"]),
            name=data.get("name") or "",
            queue=_queue_from_string(queue_str),
            queue_raw=queue_str,
            entries=tuple(LeagueItem.from_api_response(entry) for entry in (data.get("entries") or ())),
        )
