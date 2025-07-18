"""Nexar: A simple, Pythonic SDK for Riot's League of Legends API."""

from .cache import (
    DEFAULT_CACHE_CONFIG,
    NO_CACHE_CONFIG,
    PERMANENT_CACHE_CONFIG,
    SMART_CACHE_CONFIG,
    CacheConfig,
)
from .client import NexarClient
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
    ForbiddenError,
    NexarError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)
from .logging import configure_logging
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
from .rate_limiter import RateLimiter

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_CACHE_CONFIG",
    "LONG_CACHE_CONFIG",
    "NO_CACHE_CONFIG",
    "PERMANENT_CACHE_CONFIG",
    "SMART_CACHE_CONFIG",
    "CacheConfig",
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
    "RateLimiter",
    "RegionV4",
    "RegionV5",
    "RiotAPIError",
    "RiotAccount",
    "Summoner",
    "TeamInfo",
    "TeamsInfo",
    "UnauthorizedError",
    "configure_logging",
]
