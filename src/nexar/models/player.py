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


class Player:
    """High-level player object that provides convenient access to player data."""

    def __init__(
        self,
        client: NexarClient,
        game_name: str,
        tag_line: str,
        v4_region: RegionV4 | None = None,
        v5_region: RegionV5 | None = None,
    ) -> None:
        """
        Initialize a Player.

        Args:
            client: The NexarClient instance
            game_name: Player's game name (without #)
            tag_line: Player's tag line (without #)
            v4_region: Platform region for v4 endpoints (defaults to client default)
            v5_region: Regional region for v5 endpoints (defaults to client default)

        """
        self._client = client
        self.game_name = game_name
        self.tag_line = tag_line
        self._v4_region = v4_region or client.default_v4_region
        self._v5_region = v5_region or client.default_v5_region

        # Cache these expensive lookups
        self._riot_account: RiotAccount | None = None
        self._summoner: Summoner | None = None
        self._league_entries: list[LeagueEntry] | None = None

    @property
    def riot_account(self) -> RiotAccount:
        """Get the player's Riot account. Cached after first access."""
        if self._riot_account is None:
            self._riot_account = self._client.get_riot_account(
                self.game_name,
                self.tag_line,
                region=self._v5_region,
            )
        return self._riot_account

    @property
    def summoner(self) -> Summoner:
        """Get the player's summoner information. Cached after first access."""
        if self._summoner is None:
            self._summoner = self._client.get_summoner_by_puuid(
                self.riot_account.puuid,
                region=self._v4_region,
            )
        return self._summoner

    @property
    def puuid(self) -> str:
        """Get the player's PUUID."""
        return self.riot_account.puuid

    @property
    def league_entries(self) -> list[LeagueEntry]:
        """Get all league entries for the player. Cached after first access."""
        if self._league_entries is None:
            self._league_entries = self._client.get_league_entries_by_puuid(
                self.puuid,
                region=self._v4_region,
            )
        return self._league_entries

    @property
    def rank(self) -> LeagueEntry | None:
        """
        Get the player's solo queue rank.

        - API queue type: RANKED_SOLO_5x5
        - Map: Summoner's Rift
        - Colloquial name: Solo/Duo; Solo Queue
        """
        from nexar.enums import Queue

        for entry in self.league_entries:
            if entry.queue_type == Queue.RANKED_SOLO_5x5:
                return entry
        return None

    @property
    def flex_rank(self) -> LeagueEntry | None:
        """
        Get the player's flex queue rank.

        - API queue type: RANKED_FLEX_SR
        - Map: Summoner's Rift
        - Colloquial name: Flex Queue
        """
        from nexar.enums import Queue

        for entry in self.league_entries:
            if entry.queue_type == Queue.RANKED_FLEX_SR:
                return entry
        return None

    @property
    def solo_rank_value(self) -> int | None:
        """
        Combined tier/rank value for the player's solo queue rank.

        Returns None if the player is unranked in solo queue.

        Useful for comparing or sorting players by solo queue rank.
        """
        if self.rank is not None:
            return self.rank.rank_value
        return None

    def get_recent_matches(
        self,
        count: int = 20,
        queue: QueueId | int | None = None,
        match_type: MatchType | str | None = None,
        start_time: int | datetime | None = None,
        end_time: int | datetime | None = None,
    ) -> list[Match]:
        """Get recent matches for the player.

        Args:
            count: Number of matches to retrieve (1-100, default 20)
            queue: Queue type filter (None for all matches)
            match_type: Match type filter
            start_time: Start time filter
            end_time: End time filter

        Returns:
            List of Match objects

        """
        match_ids = self._client.get_match_ids_by_puuid(
            self.puuid,
            count=count,
            queue=queue,
            match_type=match_type,
            start_time=start_time,
            end_time=end_time,
            region=self._v5_region,
        )

        matches = []
        for match_id in match_ids:
            match = self._client.get_match(match_id, region=self._v5_region)
            matches.append(match)

        return matches

    def get_champion_stats(
        self,
        count: int = 20,
        queue: QueueId | int | None = None,
        match_type: MatchType | str | None = None,
    ) -> list[ChampionStats]:
        """Get champion statistics from recent matches.

        Args:
            count: Number of recent matches to analyze (default 20)
            queue: Optional queue type filter
            match_type: Optional match type filter

        Returns:
            List of ChampionStats sorted by games played (descending)

        """
        matches = self.get_recent_matches(
            count=count,
            queue=queue,
            match_type=match_type,
        )

        # Group stats by champion
        champion_data: dict[int, dict[str, Any]] = {}

        for match in matches:
            # Find this player's participant data
            player_participant = None
            for participant in match.info.participants:
                if participant.puuid == self.puuid:
                    player_participant = participant
                    break

            if player_participant is None:
                continue

            champion_id = player_participant.champion_id
            if champion_id not in champion_data:
                champion_data[champion_id] = {
                    "champion_id": champion_id,
                    "champion_name": player_participant.champion_name,
                    "games_played": 0,
                    "wins": 0,
                    "losses": 0,
                    "total_kills": 0,
                    "total_deaths": 0,
                    "total_assists": 0,
                }

            stats = champion_data[champion_id]
            stats["games_played"] += 1
            stats["total_kills"] += player_participant.kills
            stats["total_deaths"] += player_participant.deaths
            stats["total_assists"] += player_participant.assists

            if player_participant.win:
                stats["wins"] += 1
            else:
                stats["losses"] += 1

        # Convert to ChampionStats objects and sort by games played
        champion_stats = [ChampionStats(**data) for data in champion_data.values()]
        champion_stats.sort(key=lambda x: x.games_played, reverse=True)

        return champion_stats

    def get_top_champions(
        self,
        top_n: int = 5,
        count: int = 20,
        queue: QueueId | int | None = None,
        match_type: MatchType | str | None = None,
    ) -> list[ChampionStats]:
        """Get top played champions.

        Args:
            top_n: Number of top champions to return (default 5)
            count: Number of recent matches to analyze (default 20)
            queue: Optional queue type filter
            match_type: Optional match type filter

        Returns:
            List of top ChampionStats by games played

        """
        all_stats = self.get_champion_stats(
            count=count,
            queue=queue,
            match_type=match_type,
        )
        return all_stats[:top_n]

    def get_performance_summary(
        self,
        count: int = 20,
        queue: QueueId | int | None = None,
        match_type: MatchType | str | None = None,
    ) -> dict[str, Any]:
        """Get a performance summary from recent matches.

        Args:
            count: Number of recent matches to analyze (default 20)
            queue: Optional queue type filter
            match_type: Optional match type filter

        Returns:
            Dictionary with performance statistics

        """
        matches = self.get_recent_matches(
            count=count,
            queue=queue,
            match_type=match_type,
        )

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
                "avg_cs": 0.0,
                "avg_game_duration_minutes": 0.0,
            }

        total_games = len(matches)
        wins = 0
        total_kills = 0
        total_deaths = 0
        total_assists = 0
        total_cs = 0
        total_duration_seconds = 0

        for match in matches:
            # Find this player's participant data
            player_participant = None
            for participant in match.info.participants:
                if participant.puuid == self.puuid:
                    player_participant = participant
                    break

            if player_participant is None:
                continue

            if player_participant.win:
                wins += 1

            total_kills += player_participant.kills
            total_deaths += player_participant.deaths
            total_assists += player_participant.assists
            total_cs += player_participant.total_minions_killed + player_participant.neutral_minions_killed
            total_duration_seconds += match.info.game_duration

        losses = total_games - wins
        win_rate = (wins / total_games * 100) if total_games > 0 else 0.0
        avg_kills = total_kills / total_games if total_games > 0 else 0.0
        avg_deaths = total_deaths / total_games if total_games > 0 else 0.0
        avg_assists = total_assists / total_games if total_games > 0 else 0.0
        avg_kda = (total_kills + total_assists) / total_deaths if total_deaths > 0 else 0.0
        avg_cs = total_cs / total_games if total_games > 0 else 0.0
        avg_duration_minutes = (total_duration_seconds / 60) / total_games if total_games > 0 else 0.0

        return {
            "total_games": total_games,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 1),
            "avg_kills": round(avg_kills, 1),
            "avg_deaths": round(avg_deaths, 1),
            "avg_assists": round(avg_assists, 1),
            "avg_kda": round(avg_kda, 2),
            "avg_cs": round(avg_cs, 1),
            "avg_game_duration_minutes": round(avg_duration_minutes, 1),
        }

    def is_on_win_streak(self, min_games: int = 3) -> bool:
        """Check if the player is currently on a win streak.

        Args:
            min_games: Minimum number of games to consider a streak (default 3)

        Returns:
            True if player is on a win streak of at least min_games

        """
        recent_matches = self.get_recent_matches(count=min_games)

        if len(recent_matches) < min_games:
            return False

        for match in recent_matches:
            # Find this player's participant data
            player_participant = None
            for participant in match.info.participants:
                if participant.puuid == self.puuid:
                    player_participant = participant
                    break

            if player_participant is None or not player_participant.win:
                return False

        return True

    def get_recent_performance_by_role(
        self,
        count: int = 50,
        queue: QueueId | int | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Get performance statistics grouped by role.

        Args:
            count: Number of recent matches to analyze (default 50)
            queue: Optional queue type filter

        Returns:
            Dictionary with role names as keys and performance stats as values

        """
        matches = self.get_recent_matches(count=count, queue=queue)

        role_stats: dict[str, dict[str, Any]] = {}

        for match in matches:
            # Find this player's participant data
            player_participant = None
            for participant in match.info.participants:
                if participant.puuid == self.puuid:
                    player_participant = participant
                    break

            if player_participant is None:
                continue

            role = player_participant.team_position.value if player_participant.team_position else "UNKNOWN"

            if role not in role_stats:
                role_stats[role] = {
                    "games_played": 0,
                    "wins": 0,
                    "total_kills": 0,
                    "total_deaths": 0,
                    "total_assists": 0,
                    "total_cs": 0,
                }

            stats = role_stats[role]
            stats["games_played"] += 1
            stats["total_kills"] += player_participant.kills
            stats["total_deaths"] += player_participant.deaths
            stats["total_assists"] += player_participant.assists
            stats["total_cs"] += player_participant.total_minions_killed + player_participant.neutral_minions_killed

            if player_participant.win:
                stats["wins"] += 1

        # Calculate derived stats
        for role, stats in role_stats.items():
            games = stats["games_played"]
            if games > 0:
                stats["win_rate"] = round((stats["wins"] / games) * 100, 1)
                stats["avg_kills"] = round(stats["total_kills"] / games, 1)
                stats["avg_deaths"] = round(stats["total_deaths"] / games, 1)
                stats["avg_assists"] = round(stats["total_assists"] / games, 1)
                stats["avg_cs"] = round(stats["total_cs"] / games, 1)
                stats["avg_kda"] = (
                    round(
                        (stats["total_kills"] + stats["total_assists"]) / stats["total_deaths"],
                        2,
                    )
                    if stats["total_deaths"] > 0
                    else 0.0
                )

        return role_stats

    def refresh_cache(self) -> None:
        """Clear all cached data to force fresh API calls."""
        self._riot_account = None
        self._summoner = None
        self._league_entries = None

    def __str__(self) -> str:
        """String representation of the player."""
        return f"Player({self.game_name}#{self.tag_line})"

    def __repr__(self) -> str:
        """Detailed string representation of the player."""
        return f"Player(game_name='{self.game_name}', tag_line='{self.tag_line}')"
