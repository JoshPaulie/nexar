"""Nexar: A simple, Pythonic SDK for Riot's League of Legends API."""

import logging

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
    ChampionMastery,
    ChampionRotations,
    ChampionStats,
    LeagueEntry,
    LeagueItem,
    LeagueList,
    Match,
    MiniSeries,
    PerformanceStats,
    PlatformStatus,
    Player,
    RiotAccount,
    Summoner,
    Timeline,
)
from .rate_limiter import PERSONAL_LIMITS, PRODUCTION_LIMITS

# Library logging contract: the package loggers carry a NullHandler, so the
# SDK is silent unless the application configures logging. Without one, the
# logging module's last-resort handler printed handled 4xx errors and
# parse fallbacks to stderr with zero configuration. Child loggers
# (nexar.cache) inherit the handler through the chain.
logging.getLogger("nexar").addHandler(logging.NullHandler())

__version__ = "2.0.0"

__all__ = [
    "DEFAULT_CACHE_CONFIG",
    "NO_CACHE_CONFIG",
    "PERSONAL_LIMITS",
    "PRODUCTION_LIMITS",
    "BatchError",
    "CacheConfig",
    "CallStats",
    "ChampionMastery",
    "ChampionRotations",
    "ChampionStats",
    "ForbiddenError",
    "LeagueEntry",
    "LeagueItem",
    "LeagueList",
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
    "PlatformStatus",
    "Player",
    "Queue",
    "RankDivision",
    "RankTier",
    "RateLimitError",
    "Region",
    "RiotAPIError",
    "RiotAccount",
    "Summoner",
    "Timeline",
    "UnauthorizedError",
]
