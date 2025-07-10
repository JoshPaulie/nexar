"""Cache configuration for the Nexar SDK."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CacheConfig:
    """
    Configuration for API response caching.

    Attributes:
        enabled: Whether caching is enabled
        cache_name: Name of the cache file (without extension)
        backend: Cache backend to use ('sqlite', 'filesystem', 'memory', etc.)
        expire_after: Default expiration time in seconds (None for no expiration)
        endpoint_config: Per-endpoint cache configuration

    """

    enabled: bool = True
    cache_name: str = "nexar_cache"
    backend: str = "sqlite"
    expire_after: int | None = 3600  # 1 hour default
    endpoint_config: dict[str, dict[str, Any]] = field(default_factory=dict)

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

SMART_CACHE_CONFIG = CacheConfig(
    expire_after=3600,  # 1 hour default
    endpoint_config={
        # Account and summoner data changes rarely
        "/riot/account/v1/accounts/by-riot-id": {"expire_after": 86400},  # 24 hours
        "/lol/summoner/v4/summoners/by-puuid": {"expire_after": 86400},  # 24 hours
        # Match data is immutable once finished
        "/lol/match/v5/matches": {"expire_after": None},  # Cache forever
        # League entries change frequently
        "/lol/league/v4/entries/by-puuid": {"expire_after": 300},  # 5 minutes
        # Match IDs change as new matches are played
        "/lol/match/v5/matches/by-puuid": {"expire_after": 60},  # 1 minute
    },
)
"""
Inteligently cache different endpoints for varying durations.

Static data is cached longer, immutable data is cached forever, live data is cached shorter.
"""

LONG_CACHE_CONFIG = CacheConfig(
    expire_after=86400,  # 24 hours
)
"""Cache everything for 24 hours"""

PERMANENT_CACHE_CONFIG = CacheConfig(expire_after=None)
"""Cache everything forever (use with caution, almost certainly a bad idea)"""

NO_CACHE_CONFIG = CacheConfig(enabled=False)
"""Disable caching entirely (good for troubleshooting)"""
