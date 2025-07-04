"""Nexar: A simple, Pythonic SDK for Riot's League of Legends API."""

from .client import NexarClient
from .enums import Division, MatchType, Queue, QueueId, RegionV4, RegionV5, Tier
from .exceptions import (
    ForbiddenError,
    NexarError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)
from .models import (
    ChampionStats,
    LeagueEntry,
    Match,
    MiniSeries,
    Player,
    RiotAccount,
    Summoner,
    TeamInfo,
    TeamsInfo,
)

__version__ = "0.1.0"

__all__ = [
    "NexarClient",
    "RegionV4",
    "RegionV5",
    "Queue",
    "QueueId",
    "MatchType",
    "Tier",
    "Division",
    "Match",
    "TeamInfo",
    "TeamsInfo",
    "RiotAccount",
    "Summoner",
    "LeagueEntry",
    "MiniSeries",
    "Player",
    "ChampionStats",
    "NexarError",
    "RiotAPIError",
    "RateLimitError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
]
