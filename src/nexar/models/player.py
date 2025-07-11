"""High-level player objects for convenient API access."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from nexar.enums import QueueId

if TYPE_CHECKING:
    from datetime import datetime

    from nexar.client import NexarClient
    from nexar.enums import MatchType, RegionV4, RegionV5

    from .account import RiotAccount, Summoner
    from .league import LeagueEntry
    from .match.match import Match


@dataclass
class ChampionStats:
    """Statistics for a specific champion."""

    champion_id: int
    champion_name: str
    games_played: int
    wins: int
    losses: int
    total_kills: int
    total_deaths: int
    total_assists: int

    @property
    def win_rate(self) -> float:
        """Win rate as a percentage (0.0 to 100.0)."""
        if self.games_played == 0:
            return 0.0
        return (self.wins / self.games_played) * 100.0

    @property
    def avg_kda(self) -> float:
        """Average KDA ratio."""
        if self.games_played == 0 or self.total_deaths == 0:
            return 0.0
        return (self.total_kills + self.total_assists) / self.total_deaths

    @property
    def avg_kills(self) -> float:
        """Average kills per game."""
        if self.games_played == 0:
            return 0.0
        return self.total_kills / self.games_played

    @property
    def avg_deaths(self) -> float:
        """Average deaths per game."""
        if self.games_played == 0:
            return 0.0
        return self.total_deaths / self.games_played

    @property
    def avg_assists(self) -> float:
        """Average assists per game."""
        if self.games_played == 0:
            return 0.0
        return self.total_assists / self.games_played


@dataclass
class PerformanceStats:
    """Performance statistics for a player over a set of matches."""

    total_games: int
    """Total number of games analyzed."""

    wins: int
    """Number of wins."""

    losses: int
    """Number of losses."""

    win_rate: float
    """Win rate as a percentage (0.0 to 100.0)."""

    avg_kills: float
    """Average kills per game."""

    avg_deaths: float
    """Average deaths per game."""

    avg_assists: float
    """Average assists per game."""

    avg_kda: float
    """Average KDA ratio ((kills + assists) / deaths)."""

    avg_cs: float
    """Average creep score (minions + neutral minions killed) per game."""

    avg_game_duration_minutes: float
    """Average game duration in minutes."""


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

    v4_region: RegionV4 | None = None
    """Platform region for v4 endpoints (defaults to client default)."""

    v5_region: RegionV5 | None = None
    """Regional region for v5 endpoints (defaults to client default)."""

    # Cached data (set after first fetch)
    _summoner: Summoner | None = None
    _league_entries: list[LeagueEntry] | None = None

    @classmethod
    async def create(
        cls,
        client: NexarClient,
        game_name: str,
        tag_line: str,
        *,
        v4_region: RegionV4 | None = None,
        v5_region: RegionV5 | None = None,
    ) -> Player:
        """
        Create a Player instance and fetch the riot account data immediately.

        Args:
            client: The client instance to use for API calls
            game_name: Player's game name (without #)
            tag_line: Player's tag line (without #)
            v4_region: Platform region for v4 endpoints (defaults to client default)
            v5_region: Regional region for v5 endpoints (defaults to client default)

        Returns:
            Player instance with riot account data pre-fetched

        """
        riot_account = await client.get_riot_account(
            game_name,
            tag_line,
            region=v5_region,
        )

        return cls(
            client=client,
            game_name=game_name,
            tag_line=tag_line,
            riot_account=riot_account,
            v4_region=v4_region,
            v5_region=v5_region,
        )

    @classmethod
    async def by_riot_id(
        cls,
        client: NexarClient,
        riot_id: str,
        *,
        v4_region: RegionV4 | None = None,
        v5_region: RegionV5 | None = None,
    ) -> Player:
        """
        Create a Player instance from a Riot ID in "username#tagline" format.

        Args:
            client: The client instance to use for API calls
            riot_id: Riot ID in "username#tagline" format (e.g., "bexli#bex")
            v4_region: Platform region for v4 endpoints (defaults to client default)
            v5_region: Regional region for v5 endpoints (defaults to client default)

        Returns:
            Player instance with riot account data pre-fetched

        Raises:
            ValueError: If riot_id is not in the correct format

        """
        if "#" not in riot_id:
            msg = f"Invalid Riot ID format: '{riot_id}'. Expected 'username#tagline'"
            raise ValueError(msg)

        game_name, tag_line = riot_id.split("#", 1)

        if not game_name or not tag_line:
            msg = f"Invalid Riot ID format: '{riot_id}'. Both username and tagline must be non-empty"
            raise ValueError(msg)

        return await cls.create(
            client=client,
            game_name=game_name,
            tag_line=tag_line,
            v4_region=v4_region,
            v5_region=v5_region,
        )

    async def get_summoner(self) -> Summoner:
        """
        Get the player's summoner information.

        Returns:
            Summoner with summoner information

        """
        if self._summoner is None:
            self._summoner = await self.client.get_summoner_by_puuid(
                self.riot_account.puuid,
                region=self.v4_region,
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
                region=self.v4_region,
            )
        return self._league_entries

    async def get_match_ids(
        self,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: QueueId | int | None = None,
        match_type: MatchType | str | None = None,
        start: int = 0,
        count: int = 20,
    ) -> list[str]:
        """
        Get match IDs for the player.

        Args:
            start_time: Epoch timestamp in seconds or datetime for match start filter
            end_time: Epoch timestamp in seconds or datetime for match end filter
            queue: Queue ID filter (int or QueueId enum)
            match_type: Match type filter (str or MatchType enum)
            start: Start index (0-based)
            count: Number of match IDs to return (0-100)

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
            region=self.v5_region,
        )

    async def get_matches(
        self,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: QueueId | int | None = None,
        match_type: MatchType | str | None = None,
        start: int = 0,
        count: int = 20,
    ) -> list[Match]:
        """
        Get match details for the player.

        Args:
            start_time: Epoch timestamp in seconds or datetime for match start filter
            end_time: Epoch timestamp in seconds or datetime for match end filter
            queue: Queue ID filter (int or QueueId enum)
            match_type: Match type filter (str or MatchType enum)
            start: Start index (0-based)
            count: Number of match IDs to return (0-100)

        Returns:
            List of Match objects with detailed match information

        """
        match_ids = await self.get_match_ids(
            start_time=start_time,
            end_time=end_time,
            queue=queue,
            match_type=match_type,
            start=start,
            count=count,
        )

        # Fetch all matches concurrently

        async def fetch_match(match_id: str) -> Match:
            return await self.client.get_match(match_id, region=self.v5_region)

        return await asyncio.gather(*[fetch_match(match_id) for match_id in match_ids])

    async def get_last_match(self) -> Match | None:
        """
        Get the player's most recent match.

        Returns:
            Most recent Match object, or None if no matches found

        """
        match_ids = await self.get_match_ids(count=1)
        if not match_ids:
            return None

        return await self.client.get_match(match_ids[0], region=self.v5_region)

    async def get_champion_stats(
        self,
        *,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
        queue: QueueId | int | None = None,
        match_type: MatchType | str | None = None,
        count: int = 20,
    ) -> list[ChampionStats]:
        """
        Get champion statistics for the player.

        Args:
            start_time: Epoch timestamp in seconds or datetime for match start filter
            end_time: Epoch timestamp in seconds or datetime for match end filter
            queue: Queue ID filter (int or QueueId enum)
            match_type: Match type filter (MatchType enum or string)
            count: Number of matches to analyze (0-100)

        Returns:
            List of ChampionStats objects sorted by games played (descending)

        """
        matches = await self.get_matches(
            start_time=start_time,
            end_time=end_time,
            queue=queue,
            match_type=match_type,
            count=count,
        )

        puuid = self.riot_account.puuid

        # Aggregate stats by champion
        champion_data: dict[int, dict[str, Any]] = {}

        for match in matches:
            # Find the participant for this player
            participant = None
            for p in match.info.participants:
                if p.puuid == puuid:
                    participant = p
                    break

            if not participant:
                continue

            champion_id = participant.champion_id
            champion_name = participant.champion_name

            if champion_id not in champion_data:
                champion_data[champion_id] = {
                    "champion_name": champion_name,
                    "games_played": 0,
                    "wins": 0,
                    "losses": 0,
                    "total_kills": 0,
                    "total_deaths": 0,
                    "total_assists": 0,
                }

            stats = champion_data[champion_id]
            stats["games_played"] += 1
            stats["total_kills"] += participant.kills
            stats["total_deaths"] += participant.deaths
            stats["total_assists"] += participant.assists

            if participant.win:
                stats["wins"] += 1
            else:
                stats["losses"] += 1

        # Convert to ChampionStats objects
        champion_stats = []
        for champion_id, data in champion_data.items():
            champion_stat = ChampionStats(
                champion_id=champion_id,
                champion_name=data["champion_name"],
                games_played=data["games_played"],
                wins=data["wins"],
                losses=data["losses"],
                total_kills=data["total_kills"],
                total_deaths=data["total_deaths"],
                total_assists=data["total_assists"],
            )
            champion_stats.append(champion_stat)

        # Sort by games played (descending)
        champion_stats.sort(key=lambda x: x.games_played, reverse=True)
        return champion_stats

    async def get_recent_performance(
        self,
        count: int = 20,
        queue: QueueId | int | None = None,
    ) -> PerformanceStats:
        """
        Get recent performance summary for the player.

        Args:
            count: Number of recent matches to analyze (1-100)
            queue: Optional queue type filter

        Returns:
            PerformanceStats with comprehensive performance metrics

        """
        matches = await self.get_matches(queue=queue, count=count)
        puuid = self.riot_account.puuid

        if not matches:
            return PerformanceStats(
                total_games=0,
                wins=0,
                losses=0,
                win_rate=0.0,
                avg_kills=0.0,
                avg_deaths=0.0,
                avg_assists=0.0,
                avg_kda=0.0,
                avg_cs=0.0,
                avg_game_duration_minutes=0.0,
            )

        total_games = len(matches)
        wins = 0
        total_kills = 0
        total_deaths = 0
        total_assists = 0
        total_cs = 0
        total_duration = 0

        for match in matches:
            # Find the participant for this player
            participant = None
            for p in match.info.participants:
                if p.puuid == puuid:
                    participant = p
                    break

            if not participant:
                continue

            if participant.win:
                wins += 1

            total_kills += participant.kills
            total_deaths += participant.deaths
            total_assists += participant.assists
            total_cs += participant.total_minions_killed + participant.neutral_minions_killed
            total_duration += match.info.game_duration

        losses = total_games - wins
        win_rate = (wins / total_games) * 100.0 if total_games > 0 else 0.0
        avg_kills = total_kills / total_games if total_games > 0 else 0.0
        avg_deaths = total_deaths / total_games if total_games > 0 else 0.0
        avg_assists = total_assists / total_games if total_games > 0 else 0.0
        avg_kda = (total_kills + total_assists) / total_deaths if total_deaths > 0 else 0.0
        avg_cs = total_cs / total_games if total_games > 0 else 0.0
        avg_game_duration_minutes = (total_duration / 60) / total_games if total_games > 0 else 0.0

        return PerformanceStats(
            total_games=total_games,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            avg_kills=avg_kills,
            avg_deaths=avg_deaths,
            avg_assists=avg_assists,
            avg_kda=avg_kda,
            avg_cs=avg_cs,
            avg_game_duration_minutes=avg_game_duration_minutes,
        )

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
            if entry.queue_type == QueueId.RANKED_SOLO_5x5:
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
            if entry.queue_type == QueueId.RANKED_FLEX_SR:
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

    async def get_top_champions(
        self,
        top_n: int = 5,
        count: int = 20,
        queue: QueueId | int | None = None,
        match_type: MatchType | str | None = None,
    ) -> list[ChampionStats]:
        """
        Get top played champions.

        Args:
            top_n: Number of top champions to return (default 5)
            count: Number of recent matches to analyze (default 20)
            queue: Optional queue type filter
            match_type: Optional match type filter

        Returns:
            List of ChampionStats sorted by games played (descending)

        """
        champion_stats = await self.get_champion_stats(
            queue=queue,
            match_type=match_type,
            count=count,
            start_time=None,
            end_time=None,
        )
        return sorted(champion_stats, key=lambda x: x.games_played, reverse=True)[:top_n]

    async def get_recent_performance_by_role(
        self,
        count: int = 50,
        queue: QueueId | int | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        Get performance statistics grouped by role.

        Args:
            count: Number of recent matches to analyze (default 50)
            queue: Optional queue type filter

        Returns:
            Dictionary with role names as keys and performance stats as values

        """
        matches = await self.get_matches(queue=queue, count=count)
        puuid = self.riot_account.puuid

        role_stats: dict[str, dict[str, Any]] = {}

        for match in matches:
            # Find the participant for this player
            participant = None
            for p in match.info.participants:
                if p.puuid == puuid:
                    participant = p
                    break

            if not participant:
                continue

            role = participant.team_position.value if participant.team_position else "UNKNOWN"

            if role not in role_stats:
                role_stats[role] = {
                    "games": 0,
                    "wins": 0,
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                }

            role_stats[role]["games"] += 1
            if participant.win:
                role_stats[role]["wins"] += 1
            role_stats[role]["kills"] += participant.kills
            role_stats[role]["deaths"] += participant.deaths
            role_stats[role]["assists"] += participant.assists

        # Calculate averages and percentages
        for stats in role_stats.values():
            games = stats["games"]
            if games > 0:
                stats["win_rate"] = (stats["wins"] / games) * 100.0
                stats["avg_kills"] = stats["kills"] / games
                stats["avg_deaths"] = stats["deaths"] / games
                stats["avg_assists"] = stats["assists"] / games
                stats["avg_kda"] = (stats["kills"] + stats["assists"]) / stats["deaths"] if stats["deaths"] > 0 else 0.0

        return role_stats

    async def is_on_win_streak(self, min_games: int = 3) -> bool:
        """
        Check if the player is currently on a win streak.

        Args:
            min_games: Minimum number of games to consider a streak (default 3)

        Returns:
            True if the player is on a win streak of at least min_games

        """
        matches = await self.get_matches(count=min_games * 2)  # Get extra to be safe
        puuid = self.riot_account.puuid

        wins_in_a_row = 0
        for match in matches:
            # Find the participant for this player
            participant = None
            for p in match.info.participants:
                if p.puuid == puuid:
                    participant = p
                    break

            if not participant:
                continue

            if participant.win:
                wins_in_a_row += 1
            else:
                break  # Streak broken

        return wins_in_a_row >= min_games

    def refresh_cache(self) -> None:
        """Clear all cached data to force fresh API calls."""
        self._summoner = None
        self._league_entries = None

    def __str__(self) -> str:
        """Return string representation of the player."""
        return f"{self.game_name}#{self.tag_line}"

    def __repr__(self) -> str:
        """Detailed string representation of the player."""
        return f"Player(game_name='{self.game_name}', tag_line='{self.tag_line}')"
