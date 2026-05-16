"""Cache configuration for the Nexar SDK."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from aiohttp_client_cache.backends.base import DictCache
from aiohttp_client_cache.backends.sqlite import SQLiteBackend


def ttl(*, minutes: int = 0, hours: int = 0, days: int = 0) -> int:
    """Helper to convert minutes/hours to seconds for TTL values."""
    return minutes * 60 + hours * 3600 + days * 86400


# Per-endpoint TTLs for data that has predictable freshness characteristics.
# Match detail is immutable once finished → cached forever.
# Account/summoner lookup data rarely changes → cached 24 hours.
# League entries change frequently → cached 5 minutes.
# Match ID lists change as new matches are played → cached 1 minute.
# Order matters: more specific patterns must come first (first match wins).
_SMART_ENDPOINT_TTLS: dict[str, int | None] = {
    "*/lol/match/v5/matches/by-puuid/*/ids": ttl(minutes=1),
    "*/lol/league/v4/entries/by-puuid/*": ttl(minutes=5),
    "*/lol/match/v5/matches/*": None,
    "*/riot/account/v1/accounts/by-riot-id/*": ttl(days=1),
    "*/lol/summoner/v4/summoners/by-puuid/*": ttl(days=1),
}


def create_cache_backend(config: CacheConfig) -> SQLiteBackend | DictCache:
    """Create an aiohttp-client-cache backend based on the provided configuration."""
    if config.backend == "sqlite":
        cache_dir = Path(config.cache_dir) if config.cache_dir else (Path.home() / ".nexar")
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{config.cache_name}.sqlite"
        return SQLiteBackend(
            cache_name=str(cache_path.with_suffix("")),
            expire_after=config.expire_after,
            urls_expire_after=_SMART_ENDPOINT_TTLS,
            allowed_codes=(200,),
        )

    if config.backend == "memory":
        return DictCache(
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

    expire_after: int | None = 3600
    """Default expiration time in seconds for endpoints not covered by smart TTLs."""

    timeout: int = 30
    """HTTP request timeout in seconds."""


DEFAULT_CACHE_CONFIG = CacheConfig()
"""Default cache: SQLite, 1-hour default TTL, plus smart endpoint TTLs."""

NO_CACHE_CONFIG = CacheConfig(enabled=False)
"""Configuration that disables caching entirely."""
