from nexar.cache import CacheConfig
from nexar.client import NexarClient
from nexar.enums import Region

# --8<-- [start:smart-memory]

client = NexarClient(
    riot_api_key="your_api_key",
    cache_config=CacheConfig(backend="memory"),
    default_region=Region.NA1,
)
# --8<-- [end:smart-memory]

# --8<-- [start:smart-sqlite]
from nexar.cache import DEFAULT_CACHE_CONFIG

client = NexarClient(
    riot_api_key="your_api_key",
    cache_config=DEFAULT_CACHE_CONFIG,
    default_region=Region.NA1,
)
# --8<-- [end:smart-sqlite]

# --8<-- [start:cache-config]
from nexar.cache import CacheConfig

# SQLite cache with custom settings
custom_config = CacheConfig(
    backend="sqlite",
    expire_after=7200,  # 2 hours
)

# Memory cache with custom expiration
memory_config = CacheConfig(
    backend="memory",
    expire_after=900,  # 15 minutes
)
# --8<-- [end:cache-config]


