"""Cache configuration for the Nexar SDK."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypedDict

from aiohttp_client_cache.backends import DictCache  # type: ignore[attr-defined]
from aiohttp_client_cache.backends.sqlite import SQLiteBackend


class EndpointCacheConfig(TypedDict, total=False):
    """
    Configuration for individual endpoint caching.

    Attributes:
        expire_after: Expiration time in seconds (None for no expiration)
        enabled: Whether caching is enabled for this endpoint

    """

    expire_after: int | None
    """Expiration time in seconds (None for no expiration)"""

    enabled: bool
    """Whether caching is enabled for this endpoint"""


def create_cache_backend(config: "CacheConfig") -> SQLiteBackend | DictCache:
    """
    Create a cache backend based on the configuration.

    Args:
        config: Cache configuration

    Returns:
        Configured cache backend

    Raises:
        ValueError: If an unsupported backend is specified

    """
    if config.backend == "sqlite":
        cache_path = config.get_full_cache_path()
        return SQLiteBackend(
            cache_name=str(cache_path.with_suffix("")),  # Remove .sqlite extension
            expire_after=config.expire_after,
        )
    if config.backend == "memory":
        return DictCache(expire_after=config.expire_after)

    msg = f"Unsupported cache backend: {config.backend}"
    raise ValueError(msg)


@dataclass
class CacheConfig:
    """
    Configuration for API response caching.

    Attributes:
        enabled: Whether caching is enabled
        cache_name: Name of the cache file (without extension)
        backend: Cache backend to use ('sqlite', 'memory')
        cache_dir: Directory path for cache storage (None for current working directory)
        expire_after: Default expiration time in seconds (None for no expiration)
        endpoint_config: Per-endpoint cache configuration

    """

    enabled: bool = True
    cache_name: str = "nexar_cache"
    backend: Literal["sqlite", "memory"] = "sqlite"
    cache_dir: str | Path | None = None
    expire_after: int | None = 3600  # 1 hour default
    endpoint_config: dict[str, EndpointCacheConfig] = field(default_factory=dict)

    def get_cache_path(self) -> Path:
        """
        Get the full path for cache storage.

        Returns:
            Path object for cache storage location

        """
        base_dir = Path.cwd() if self.cache_dir is None else Path(self.cache_dir)
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def get_full_cache_path(self) -> Path:
        """
        Get the full path including cache name for SQLite backend.

        Returns:
            Full path to cache file

        """
        cache_path = self.get_cache_path()
        return cache_path / f"{self.cache_name}.sqlite"

    def get_endpoint_expire_after(self, endpoint: str) -> int | None:
        """
        Get expiration time for a specific endpoint.

        Args:
            endpoint: The API endpoint path

        Returns:
            Expiration time in seconds, or None for no expiration

        """
        if endpoint in self.endpoint_config:
            expire = self.endpoint_config[endpoint].get("expire_after", self.expire_after)
            return expire if expire is None else int(expire)
        return self.expire_after

    def is_endpoint_cached(self, endpoint: str) -> bool:
        """
        Check if a specific endpoint should be cached.

        Args:
            endpoint: The API endpoint path

        Returns:
            True if the endpoint should be cached

        """
        if not self.enabled:
            return False

        if endpoint in self.endpoint_config:
            return bool(self.endpoint_config[endpoint].get("enabled", True))

        return True


# Predefined cache configurations for different use cases
DEFAULT_CACHE_CONFIG = CacheConfig()
"""CacheConfig with defaults"""

# Shared endpoint config for smart cache
SMART_CACHE_ENDPOINTS: dict[str, EndpointCacheConfig] = {
    # --- Riot API ---
    # Account and summoner data changes rarely
    "/riot/account/v1/accounts/by-riot-id": {"expire_after": 86400},  # 24 hours
    "/lol/summoner/v4/summoners/by-puuid": {"expire_after": 86400},  # 24 hours
    # Match data is immutable once finished
    "/lol/match/v5/matches": {"expire_after": None},  # Cache forever
    # League entries change frequently
    "/lol/league/v4/entries/by-puuid": {"expire_after": 300},  # 5 minutes
    # New Match IDs are created as new matches are played
    "/lol/match/v5/matches/by-puuid": {"expire_after": 60},  # 1 minute
}

SMART_CACHE_CONFIG = CacheConfig(
    expire_after=3600,  # 1 hour default
    endpoint_config=SMART_CACHE_ENDPOINTS,
)
"""
Inteligently cache different endpoints for varying durations.

Static data is cached longer, immutable data is cached forever, live data is cached shorter.
"""

SMART_CACHE_CONFIG_MEMORY = CacheConfig(
    backend="memory",
    expire_after=3600,  # 1 hour default
    endpoint_config=SMART_CACHE_ENDPOINTS,
)
"""
Identical to SMART_CACHE_CONFIG but uses in-memory storage, meaning cache is lost upon application exit.

Inteligently cache different endpoints for varying durations.

Static data is cached longer, immutable data is cached forever, live data is cached shorter.
"""

PERMANENT_CACHE_CONFIG = CacheConfig(expire_after=None)
"""Cache everything forever (use with caution, almost certainly a bad idea)"""

NO_CACHE_CONFIG = CacheConfig(enabled=False)
"""Disable caching entirely (good for troubleshooting)"""
