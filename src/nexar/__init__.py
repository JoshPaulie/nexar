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
    "NexarClient",
    "configure_logging",
    "CacheConfig",
    "DEFAULT_CACHE_CONFIG",
    "SMART_CACHE_CONFIG",
    "LONG_CACHE_CONFIG",
    "PERMANENT_CACHE_CONFIG",
    "NO_CACHE_CONFIG",
    "RateLimit",
    "RateLimiter",
    "RegionV4",
    "RegionV5",
    "Queue",
    "QueueId",
    "MapId",
    "PlatformId",
    "MatchType",
    "MatchParticipantPosition",
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
