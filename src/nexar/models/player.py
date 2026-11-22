"""High-level player objects for convenient API access."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from nexar.enums import Queue
from nexar.exceptions import BatchError, gather_partitioned

from .match_list import MatchList
from .stats import RoleStats

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from datetime import datetime

    from nexar.client import NexarClient
    from nexar.enums import MatchType, Region

    from .account import RiotAccount, Summoner
    from .challenge import PlayerChallengeData
    from .champion_mastery import ChampionMastery
    from .league import LeagueEntry
    from .match.match import Match
    from .stats import ChampionStats


def _parse_riot_id(riot_id: str) -> tuple[str, str]:
    """Split ``gameName#tagLine`` into its parts, raising ValueError on malformed input."""
    riot_id = riot_id.strip()
    if "#" not in riot_id:
        msg = f"Invalid Riot ID format: '{riot_id}'. Expected 'gameName#tagLine'"
        raise ValueError(msg)
    game_name, tag_line = riot_id.split("#", 1)
    game_name = game_name.strip()
    tag_line = tag_line.strip()
    if not game_name or not tag_line:
        msg = f"Invalid Riot ID format: '{riot_id}'. Both name and tagline must be non-empty"
        raise ValueError(msg)
    return game_name, tag_line


@dataclass
class Player:
    """
    High-level player object for convenient access to player data.

    This class provides a convenient interface for accessing player data
    across multiple API endpoints. The riot account data is fetched immediately
    during creation, while other data is fetched lazily and cached within the
    object to avoid repeated API calls.
    """

    client: NexarClient
    """The client instance to use for API calls."""

    game_name: str
    """Player's game name (without #)."""

    tag_line: str
    """Player's tag line (without #)."""

    riot_account: RiotAccount
    """The player's Riot account information."""

    region: Region | None = None
    """The player's region (defaults to client default)."""

    # Cached data (set after first fetch, not constructor parameters)
    _summoner: Summoner | None = field(default=None, init=False, repr=False)
    _league_entries: list[LeagueEntry] | None = field(default=None, init=False, repr=False)
    _champion_masteries: list[ChampionMastery] | None = field(default=None, init=False, repr=False)
    _challenge_data: PlayerChallengeData | None = field(default=None, init=False, repr=False)

    @classmethod
    async def create(
        cls,
        client: NexarClient,
        *,
        game_name: str | None = None,
        tag_line: str | None = None,
        puuid: str | None = None,
        riot_id: str | None = None,
        region: Region | None = None,
    ) -> Player:
        """
        Create a Player instance and fetch the riot account data immediately.

        At least one identification pattern must be provided (all keyword-only).
        When several are supplied, the first one wins, in this order:

        1. ``game_name`` + ``tag_line``
        2. ``puuid``
        3. ``riot_id``

        Args:
            client: The client instance to use for API calls.
            game_name: Player's game name (without #). Must be paired with tag_line.
            tag_line: Player's tag line (without #). Must be paired with game_name.
            puuid: Player's PUUID for direct lookup.
            riot_id: Riot ID in "gameName#tagLine" format (e.g. "bexli#bex").
            region: The player's region (defaults to client default).

        Returns:
            Player instance with riot account data pre-fetched.

        Raises:
            ValueError: If no identification is provided.

        """
        if game_name is not None and tag_line is not None:
            riot_account = await client.get_riot_account(
                game_name,
                tag_line,
                region=region,
            )
            return cls(
                client=client,
                game_name=game_name,
                tag_line=tag_line,
                riot_account=riot_account,
                region=region,
            )

        if puuid is not None:
            riot_account = await client.get_riot_account_by_puuid(
                puuid,
                region=region,
            )
            return cls(
                client=client,
                game_name=riot_account.game_name,
                tag_line=riot_account.tag_line,
                riot_account=riot_account,
                region=region,
            )

        if riot_id is not None:
            parsed_name, parsed_tag = _parse_riot_id(riot_id)
            return await cls.create(
                client=client,
                game_name=parsed_name,
                tag_line=parsed_tag,
                region=region,
            )

        msg = "Either game_name + tag_line, puuid, or riot_id must be provided."
        raise ValueError(msg)

    @classmethod
    async def by_riot_id(
        cls,
        client: NexarClient,
        riot_id: str,
        *,
        region: Region | None = None,
    ) -> Player:
        """
        Create a Player instance from a Riot ID in "gameName#tagLine" format.

        Forwards to ``Player.create``, which owns the identification dispatch
        and the riot-id parsing.

        Args:
            client: The client instance to use for API calls
            riot_id: Riot ID in "gameName#tagLine" format (e.g., "bexli#bex")
            region: The player's region (defaults to client default)

        Returns:
            Player instance with riot account data pre-fetched

        Raises:
            ValueError: If riot_id is not in the correct format

        """
        return await cls.create(client=client, riot_id=riot_id, region=region)

    async def get_summoner(self) -> Summoner:
        """
        Get the player's summoner information.

        Returns:
            Summoner with summoner information

        """
        if self._summoner is None:
            self._summoner = await self.client.get_summoner_by_puuid(
                self.riot_account.puuid,
                region=self.region,
            )
        return self._summoner

    async def get_league_entries(self) -> list[LeagueEntry]:
        """
        Get the player's league entries.

        Returns:
            List of league entries for the player

        """
        if self._league_entries is None:
            self._league_entries = await self.client.get_league_entries_by_puuid(
                self.riot_account.puuid,
                region=self.region,
            )
        return self._league_entries

    async def get_champion_masteries(self) -> list[ChampionMastery]:
        """
        Get the player's champion masteries.

        Returns:
            List of ChampionMastery entries, highest mastery points first.

        """
        if self._champion_masteries is None:
            self._champion_masteries = await self.client.get_champion_masteries(
                self.riot_account.puuid,
                region=self.region,
            )
        return self._champion_masteries

    async def get_challenge_data(self) -> PlayerChallengeData:
        """
        Get the player's challenge system data.

        One call covering every challenge the player has progress on, plus
        per-category and total challenge points and the player's challenge
        customization.

        Returns:
            PlayerChallengeData with per-challenge progress and point totals.

        """
        if self._challenge_data is None:
            self._challenge_data = await self.client.get_player_challenge_data(
                self.riot_account.puuid,
                region=self.region,
            )
        return self._challenge_data

    async def get_match_ids(
        self,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: Queue | int | None = None,
        match_type: MatchType | str | None = None,
        start: int = 0,
        count: int = 20,
    ) -> list[str]:
        """
        Get match IDs for the player.

        Args:
            start_time: Epoch timestamp in seconds or datetime for match start filter
            end_time: Epoch timestamp in seconds or datetime for match end filter
            queue: Queue ID filter (int or Queue enum)
            match_type: Match type filter (str or MatchType enum)
            start: Start index (0-based)
            count: Number of match IDs to return (0-100), defaulting to 20.
                One request per call.

        Returns:
            List of match IDs

        """
        return await self.client.get_match_ids_by_puuid(
            self.riot_account.puuid,
            start_time=start_time,
            end_time=end_time,
            queue=queue,
            match_type=match_type,
            start=start,
            count=count,
            region=self.region,
        )

    async def get_matches(
        self,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: Queue | int | None = None,
        match_type: MatchType | str | None = None,
        start: int = 0,
        count: int = 20,
        allow_partial: bool = False,
    ) -> MatchList:
        """
        Get match details for the player.

        Args:
            start_time: Epoch timestamp in seconds or datetime for match start filter
            end_time: Epoch timestamp in seconds or datetime for match end filter
            queue: Queue ID filter (int or Queue enum)
            match_type: Match type filter (str or MatchType enum)
            start: Start index (0-based)
            count: Number of match IDs to return (0-100), defaulting to 20.
                Each pull costs one request for the id list plus one request
                per match, so a fresh default page is 21 requests.
            allow_partial: Return the matches that loaded instead of raising
                BatchError when one id fails; the skipped ids are logged at
                WARNING. Strict by default, so a pull either succeeds whole or
                names every failure. When every id fails, BatchError is raised
                even with allow_partial: there is no partial result to return.

        Returns:
            MatchList of Match objects with detailed match information

        """
        match_ids = await self.get_match_ids(
            start_time=start_time,
            end_time=end_time,
            queue=queue,
            match_type=match_type,
            start=start,
            count=count,
        )

        matches, errors = await gather_partitioned(
            match_ids,
            lambda match_id: self.client.get_match(match_id, region=self.region),
        )

        if errors and (not allow_partial or not matches):
            raise BatchError(errors, successful_results=matches)
        if errors:
            skipped = ", ".join(label for label, _ in errors)
            logger.warning(
                "Skipped %d of %d matches that failed to load: %s",
                len(errors),
                len(match_ids),
                skipped,
            )

        return MatchList(matches, self.riot_account.puuid)

    async def get_last_match(self) -> Match | None:
        """
        Get the player's most recent match.

        Returns:
            Most recent Match object, or None if no matches found

        """
        match_ids = await self.get_match_ids(count=1)
        if not match_ids:
            return None

        return await self.client.get_match(match_ids[0], region=self.region)

    @property
    def puuid(self) -> str:
        """Get the player's PUUID."""
        return self.riot_account.puuid

    async def get_solo_rank(self) -> LeagueEntry | None:
        """
        Get the player's solo queue rank.

        - API queue type: RANKED_SOLO_5x5
        - Map: Summoner's Rift
        - Colloquial name: Solo Queue or Solo/Duo Queue

        Returns:
            LeagueEntry for solo queue, or None if unranked

        """
        league_entries = await self.get_league_entries()
        for entry in league_entries:
            if entry.queue_type == Queue.RANKED_SOLO_5x5:
                return entry
        return None

    async def get_flex_rank(self) -> LeagueEntry | None:
        """
        Get the player's flex queue rank.

        - API queue type: RANKED_FLEX_SR
        - Map: Summoner's Rift
        - Colloquial name: Flex Queue

        Returns:
            LeagueEntry for flex queue, or None if unranked

        """
        league_entries = await self.get_league_entries()
        for entry in league_entries:
            if entry.queue_type == Queue.RANKED_FLEX_SR:
                return entry
        return None

    async def get_solo_rank_value(self) -> tuple[int, int] | None:
        """
        Combined tier/rank value for the player's solo queue rank.

        Returns None if the player is unranked in solo queue.

        Useful for comparing or sorting players by solo queue rank.

        Returns:
            Tuple of (rank_value, league_points), or None if unranked

        """
        rank = await self.get_solo_rank()
        if rank is not None:
            return rank.rank_tuple
        return None

    async def get_most_played_champions(
        self,
        top_n: int = 5,
        count: int = 20,
        queue: Queue | int | None = None,
        match_type: MatchType | str | None = None,
    ) -> list[ChampionStats]:
        """
        Get the player's most played champions from recent match history.

        Counts games played, not champion mastery points;
        ``Player.get_champion_masteries`` is the mastery counterpart.

        Args:
            top_n: Number of champions to return (default 5)
            count: Number of recent matches to analyze (default 20)
            queue: Optional queue type filter
            match_type: Optional match type filter

        Returns:
            List of ChampionStats sorted by games played (descending)

        """
        matches = await self.get_matches(
            queue=queue,
            match_type=match_type,
            count=count,
        )
        # get_champion_stats already sorts by games played (descending).
        return matches.get_champion_stats()[:top_n]

    async def get_recent_performance_by_role(
        self,
        count: int = 50,
        queue: Queue | int | None = None,
    ) -> dict[str, RoleStats]:
        """
        Get performance statistics grouped by role.

        Args:
            count: Number of recent matches to analyze (default 50)
            queue: Optional queue type filter

        Returns:
            A ``RoleStats`` per position played, keyed by role name.

        """
        matches = await self.get_matches(queue=queue, count=count)

        tallies: dict[str, dict[str, int]] = {}

        for participant in matches.each_participant():
            # team_position is never None (EMPTY is the sentinel), so no guard:
            # an empty value falls through to the UNKNOWN bucket.
            role = participant.team_position.value or "UNKNOWN"
            bucket = tallies.setdefault(role, {"games": 0, "wins": 0, "kills": 0, "deaths": 0, "assists": 0})
            bucket["games"] += 1
            if participant.win:
                bucket["wins"] += 1
            bucket["kills"] += participant.kills
            bucket["deaths"] += participant.deaths
            bucket["assists"] += participant.assists

        return {
            role: RoleStats(
                role=role,
                games_played=bucket["games"],
                wins=bucket["wins"],
                total_kills=bucket["kills"],
                total_deaths=bucket["deaths"],
                total_assists=bucket["assists"],
            )
            for role, bucket in tallies.items()
        }

    async def is_on_win_streak(self, min_games: int = 3) -> bool:
        """
        Check if the player is currently on a win streak.

        Args:
            min_games: Minimum number of games to consider a streak (default 3)

        Returns:
            True if the player is on a win streak of at least min_games

        """
        matches = await self.get_matches(count=min_games * 2)  # Get extra to be safe

        wins_in_a_row = 0
        for participant in matches.each_participant():
            if participant.win:
                wins_in_a_row += 1
            else:
                break  # Streak broken

        return wins_in_a_row >= min_games

    def refresh_cache(self) -> None:
        """Clear all cached data to force fresh API calls."""
        self._summoner = None
        self._league_entries = None
        self._champion_masteries = None
        self._challenge_data = None

    def __str__(self) -> str:
        """Return string representation of the player."""
        return f"{self.game_name}#{self.tag_line}"

    def __repr__(self) -> str:
        """Detailed string representation of the player."""
        return f"Player(game_name='{self.game_name}', tag_line='{self.tag_line}')"
