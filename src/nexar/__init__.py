"""Nexar: A simple, Pythonic SDK for Riot's League of Legends API."""

from .client import NexarClient
from .enums import Division, Queue, RegionV4, RegionV5, Tier
from .exceptions import (
    ForbiddenError,
    NexarError,
    NotFoundError,
    RateLimitError,
    RiotAPIError,
    UnauthorizedError,
)
from .models import Match, RiotAccount, Summoner, TeamInfo, TeamsInfo

__version__ = "0.1.0"

__all__ = [
    "NexarClient",
    "RegionV4",
    "RegionV5",
    "Queue",
    "Tier",
    "Division",
    "Match",
    "TeamInfo",
    "TeamsInfo",
    "RiotAccount",
    "Summoner",
    "NexarError",
    "RiotAPIError",
    "RateLimitError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
]
