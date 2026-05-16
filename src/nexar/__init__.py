"""Nexar: A simple, Pythonic SDK for Riot's League of Legends API."""

from .cache import DEFAULT_CACHE_CONFIG, NO_CACHE_CONFIG, CacheConfig
from .client import CallStats, NexarClient
from .enums import (
    MapId,
    MatchParticipantPosition,
    MatchType,
    PlatformId,
    Queue,
    RankDivision,
    RankTier,
    Region,
)
from .exceptions import (
    BatchError,
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
    PerformanceStats,
    Player,
    RiotAccount,
    Summoner,
    TeamInfo,
    TeamsInfo,
)
from .rate_limiter import PERSONAL_LIMITS, PRODUCTION_LIMITS

__version__ = "1.0.0"

__all__ = [
    "DEFAULT_CACHE_CONFIG",
    "NO_CACHE_CONFIG",
    "PERSONAL_LIMITS",
    "PRODUCTION_LIMITS",
    "BatchError",
    "CacheConfig",
    "CallStats",
    "ChampionStats",
    "ForbiddenError",
    "LeagueEntry",
    "MapId",
    "Match",
    "MatchParticipantPosition",
    "MatchType",
    "MiniSeries",
    "NexarClient",
    "NexarError",
    "NotFoundError",
    "PerformanceStats",
    "PlatformId",
    "Player",
    "Queue",
    "RankDivision",
    "RankTier",
    "RateLimitError",
    "Region",
    "RiotAPIError",
    "RiotAccount",
    "Summoner",
    "TeamInfo",
    "TeamsInfo",
    "UnauthorizedError",
]
