"""High-level player objects for convenient API access."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from datetime import datetime

    from nexar.client import NexarClient
    from nexar.enums import MatchType, QueueId, RegionV4, RegionV5

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
class Player:
    """
    High-level player object for convenient access to player data.

    This class provides a convenient interface for accessing player data
    across multiple API endpoints. All data is fetched lazily and cached
    within the object to avoid repeated API calls.
    """

    client: NexarClient
    """The client instance to use for API calls."""

    game_name: str
    """Player's game name (without #)."""

    tag_line: str
    """Player's tag line (without #)."""

    v4_region: RegionV4 | None = None
    """Platform region for v4 endpoints (defaults to client default)."""

    v5_region: RegionV5 | None = None
    """Regional region for v5 endpoints (defaults to client default)."""

    # Cached data (set after first fetch)
    _riot_account: RiotAccount | None = None
    _summoner: Summoner | None = None
    _league_entries: list[LeagueEntry] | None = None

    async def get_riot_account(self) -> RiotAccount:
        """
        Get the player's Riot account.

        Returns:
            RiotAccount with account information

        """
        if self._riot_account is None:
            self._riot_account = await self.client.get_riot_account(
                self.game_name,
                self.tag_line,
                region=self.v5_region,
            )
        return self._riot_account

    async def get_summoner(self) -> Summoner:
        """
        Get the player's summoner information.

        Returns:
            Summoner with summoner information

        """
        if self._summoner is None:
            account = await self.get_riot_account()
            self._summoner = await self.client.get_summoner_by_puuid(
                account.puuid,
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
            account = await self.get_riot_account()
            self._league_entries = await self.client.get_league_entries_by_puuid(
                account.puuid,
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
        account = await self.get_riot_account()
        return await self.client.get_match_ids_by_puuid(
            account.puuid,
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
        import asyncio

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
        count: int = 100,
    ) -> list[ChampionStats]:
        """
        Get champion statistics for the player.

        Args:
            start_time: Epoch timestamp in seconds or datetime for match start filter
            end_time: Epoch timestamp in seconds or datetime for match end filter
            queue: Queue ID filter (int or QueueId enum)
            count: Number of matches to analyze (0-100)

        Returns:
            List of ChampionStats objects sorted by games played (descending)

        """
        matches = await self.get_matches(
            start_time=start_time,
            end_time=end_time,
            queue=queue,
            count=count,
        )

        account = await self.get_riot_account()
        puuid = account.puuid

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
            stats = ChampionStats(
                champion_id=champion_id,
                champion_name=data["champion_name"],
                games_played=data["games_played"],
                wins=data["wins"],
                losses=data["losses"],
                total_kills=data["total_kills"],
                total_deaths=data["total_deaths"],
                total_assists=data["total_assists"],
            )
            champion_stats.append(stats)

        # Sort by games played (descending)
        champion_stats.sort(key=lambda x: x.games_played, reverse=True)
        return champion_stats

    async def get_recent_performance(self, count: int = 10) -> dict[str, Any]:
        """
        Get recent performance summary for the player.

        Args:
            count: Number of recent matches to analyze (1-100)

        Returns:
            Dictionary with performance metrics

        """
        matches = await self.get_matches(count=count)
        account = await self.get_riot_account()
        puuid = account.puuid

        if not matches:
            return {
                "total_games": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "avg_kills": 0.0,
                "avg_deaths": 0.0,
                "avg_assists": 0.0,
                "avg_kda": 0.0,
            }

        total_games = len(matches)
        wins = 0
        total_kills = 0
        total_deaths = 0
        total_assists = 0

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

        losses = total_games - wins
        win_rate = (wins / total_games) * 100.0 if total_games > 0 else 0.0
        avg_kills = total_kills / total_games if total_games > 0 else 0.0
        avg_deaths = total_deaths / total_games if total_games > 0 else 0.0
        avg_assists = total_assists / total_games if total_games > 0 else 0.0
        avg_kda = (total_kills + total_assists) / total_deaths if total_deaths > 0 else 0.0

        return {
            "total_games": total_games,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "avg_kills": avg_kills,
            "avg_deaths": avg_deaths,
            "avg_assists": avg_assists,
            "avg_kda": avg_kda,
        }

    def __str__(self) -> str:
        """Return string representation of the player."""
        return f"{self.game_name}#{self.tag_line}"

    def __repr__(self) -> str:
        """Detailed string representation of the player."""
        return f"Player(game_name='{self.game_name}', tag_line='{self.tag_line}')"
