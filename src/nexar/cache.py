"""Cache configuration for the Nexar SDK."""

from __future__ import annotations

import logging
import pickle
import sqlite3
from dataclasses import dataclass
from http.cookies import CookieError
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from aiohttp_client_cache.backends.base import CacheBackend
from aiohttp_client_cache.backends.sqlite import SQLiteBackend

if TYPE_CHECKING:
    from datetime import datetime

    from aiohttp import ClientResponse
    from aiohttp_client_cache.cache_control import ExpirationTime
    from aiohttp_client_cache.response import CachedResponse

logger = logging.getLogger("nexar.cache")

__all__ = [
    "DEFAULT_CACHE_CONFIG",
    "NO_CACHE_CONFIG",
    "CacheConfig",
    "NexarSQLiteBackend",
    "create_cache_backend",
    "ttl",
]


def ttl(*, minutes: int = 0, hours: int = 0, days: int = 0) -> int:
    """Helper to convert minutes/hours to seconds for TTL values."""
    return minutes * 60 + hours * 3600 + days * 86400


# Per-endpoint TTLs for data that has predictable freshness characteristics.
# Match detail is immutable once finished → cached forever.
# Account/summoner lookup data rarely changes → cached 24 hours.
# League entries change frequently → cached 5 minutes.
# Champion mastery changes only through play → cached 30 minutes.
# Match ID lists change as new matches are played → cached 1 minute.
# Order matters: more specific patterns must come first (first match wins).
_SMART_ENDPOINT_TTLS: dict[str, ExpirationTime] = {
    "*/lol/match/v5/matches/by-puuid/*/ids": ttl(minutes=1),
    "*/lol/league/v4/entries/by-puuid/*": ttl(minutes=5),
    "*/lol/champion-mastery/v4/champion-masteries/by-puuid/*": ttl(minutes=30),
    "*/lol/champion-mastery/v4/scores/by-puuid/*": ttl(minutes=30),
    # aiohttp-client-cache's never-expire sentinel. A None value here is skipped
    # by the library's coalesce (indistinguishable from no pattern match), which
    # silently resolved immutable match URLs to the 1-hour session default.
    "*/lol/match/v5/matches/*": -1,
    "*/riot/account/v1/accounts/by-riot-id/*": ttl(days=1),
    "*/lol/summoner/v4/summoners/by-puuid/*": ttl(days=1),
}


class NexarSQLiteBackend(SQLiteBackend):
    """SQLite backend that never caches cookies and drops rows it cannot load.

    Riot's API responses carry a Cloudflare ``__cf_bm`` Set-Cookie whose ``Partitioned``
    attribute ``http.cookies`` rejects when a cached row is unpickled. aiohttp-client-cache
    pickles the whole response — cookies included — and its deserialize guard does not catch
    ``CookieError``, so a single cached cookie made every later read of that row crash.
    Cookies are anti-bot session noise, not API data: they are stripped before the row is
    written, and a row written by an older version that still fails to load is deleted and
    treated as a cache miss, so a poisoned cache heals itself on the next fetch.
    """

    async def save_response(
        self,
        response: ClientResponse,
        cache_key: str | None = None,
        expires: datetime | None = None,
    ) -> None:
        """Save a response with its cookie jar emptied.

        The jar on the live response is a parsed copy nobody consumes — the session's
        cookie jar was already updated when the response arrived, so nothing is lost.
        """
        response.cookies.clear()
        for redirected in response.history:
            redirected.cookies.clear()
        await super().save_response(response, cache_key, expires)

    async def get_response(self, key: str) -> CachedResponse | None:
        """Read a cached response, treating an unreadable row as a cache miss."""
        try:
            return await super().get_response(key)
        except (CookieError, pickle.UnpicklingError, EOFError, sqlite3.Error):
            logger.warning("Dropping cached row %s: it cannot be loaded. Refetching.", key)
            # kv-level delete: CacheBackend.delete() deserializes the row first,
            # which would raise again.
            await self.responses.delete(key)
            return None


def create_cache_backend(config: CacheConfig) -> CacheBackend:
    """Create an aiohttp-client-cache backend based on the provided configuration."""
    if config.backend == "sqlite":
        cache_dir = Path(config.cache_dir) if config.cache_dir else (Path.home() / ".nexar")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{config.cache_name}.sqlite"
        return NexarSQLiteBackend(
            cache_name=str(cache_path.with_suffix("")),
            expire_after=config.expire_after,
            urls_expire_after=_SMART_ENDPOINT_TTLS,
            allowed_codes=(200,),
        )

    if config.backend == "memory":
        # CacheBackend with its default in-memory DictCache storage. Passing a bare
        # DictCache here does not work: it is a storage, not a backend, and CachedSession
        # silently swaps out a falsy cache for a default one, dropping the TTL wiring.
        return CacheBackend(
            expire_after=config.expire_after,
            urls_expire_after=_SMART_ENDPOINT_TTLS,
            allowed_codes=(200,),
        )

    msg = f"Unsupported cache backend: {config.backend}"
    raise ValueError(msg)


@dataclass(frozen=True)
class CacheConfig:
    """Configuration for API response caching."""

    enabled: bool = True
    """Whether caching is enabled."""

    cache_name: str = "nexar_cache"
    """Name of the cache file (without extension)."""

    backend: Literal["sqlite", "memory"] = "sqlite"
    """Cache backend to use ('sqlite' for persistence, 'memory' for ephemeral)."""

    cache_dir: str | Path | None = None
    """Directory path for cache storage (defaults to ~/.nexar/)."""

    expire_after: int | None = ttl(hours=1)
    """Default expiration time in seconds for endpoints not covered by smart TTLs."""

    timeout: int = 30
    """HTTP request timeout in seconds."""


DEFAULT_CACHE_CONFIG = CacheConfig()
"""Default cache: SQLite, 1-hour default TTL, plus smart endpoint TTLs."""

NO_CACHE_CONFIG = CacheConfig(enabled=False)
"""Configuration that disables caching entirely."""
