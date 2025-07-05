"""Nexar: A simple, Pythonic SDK for Riot's League of Legends API."""

from .cache import (
    DEFAULT_CACHE_CONFIG,
    LONG_CACHE_CONFIG,
    NO_CACHE_CONFIG,
    PERMANENT_CACHE_CONFIG,
    SMART_CACHE_CONFIG,
    CacheConfig,
)
from .client import NexarClient
from .enums import (
    Division,
    MapId,
    MatchParticipantPosition,
    MatchType,
    PlatformId,
    Queue,
    QueueId,
    RegionV4,
    RegionV5,
    Tier,
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
    Player,
    RiotAccount,
    Summoner,
    TeamInfo,
    TeamsInfo,
)
from .rate_limiter import RateLimit, RateLimiter

__version__ = "0.1.0"

__all__ = [
    "DEFAULT_CACHE_CONFIG",
    "LONG_CACHE_CONFIG",
    "NO_CACHE_CONFIG",
    "PERMANENT_CACHE_CONFIG",
    "SMART_CACHE_CONFIG",
    "CacheConfig",
    "ChampionStats",
    "Division",
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
    "PlatformId",
    "Player",
    "Queue",
    "QueueId",
    "RateLimit",
    "RateLimitError",
    "RateLimiter",
    "RegionV4",
    "RegionV5",
    "RiotAPIError",
    "RiotAccount",
    "Summoner",
    "TeamInfo",
    "TeamsInfo",
    "Tier",
    "UnauthorizedError",
    "configure_logging",
]
