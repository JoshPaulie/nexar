"""The declared seam shared by the NexarClient topic mixins.

``NexarCore`` is never instantiated on its own: the topic mixins in
``client_*.py`` inherit it so the state and cross-file calls they share have
one written-down surface, and ``NexarClient`` assembles the mixins. State is
declared as annotations matching the assignments in ``NexarClient.__init__``;
cross-file calls are ``TYPE_CHECKING`` stubs whose signatures are copied from
the real definitions in ``client_plumbing.py``.
"""

from typing import TYPE_CHECKING, Any

import aiohttp
from aiohttp_client_cache.session import CachedSession

from .cache import CacheConfig
from .enums import Region
from .rate_limiter import RateLimiter


class NexarCore:
    """Declared state and cross-file calls shared by the topic mixins."""

    riot_api_key: str
    default_region: Region | None
    cache_config: CacheConfig
    rate_limiter: RateLimiter
    _api_call_count: int
    _call_stats: dict[str, int]
    _session: CachedSession | aiohttp.ClientSession | None

    if TYPE_CHECKING:

        def _resolve_region(self, region: Region | None) -> Region: ...

        async def _make_api_call(
            self,
            endpoint: str,
            platform_region: str,
            routing_region: str | None = None,
            params: dict[str, Any] | None = None,
            max_retries: int = 5,
        ) -> dict[str, Any]: ...
