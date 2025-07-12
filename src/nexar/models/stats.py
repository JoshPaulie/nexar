"""Dataclasses for holding statistics."""

from dataclasses import dataclass


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
