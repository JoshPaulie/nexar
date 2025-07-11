from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

# --8<-- [start:smart-memory]
from nexar.cache import SMART_CACHE_CONFIG_MEMORY

client = NexarClient(
    riot_api_key="your_api_key",
    cache_config=SMART_CACHE_CONFIG_MEMORY,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
)
# --8<-- [end:smart-memory]

# --8<-- [start:smart-sqlite]
from nexar.cache import SMART_CACHE_CONFIG

client = NexarClient(
    riot_api_key="your_api_key",
    cache_config=SMART_CACHE_CONFIG,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
)
# --8<-- [end:smart-sqlite]

# --8<-- [start:cache-config]
from nexar import CacheConfig

# SQLite cache with custom settings
custom_config = CacheConfig(
    backend="sqlite",
    cache_dir="/var/cache/nexar/",
    expire_after=7200,  # Default 2 hours
)

# Memory cache with custom expiration
memory_config = CacheConfig(
    backend="memory",
    expire_after=900,  # 15 minutes
)
# --8<-- [end:cache-config]

# --8<-- [start:smart-custom]
from nexar.cache import SMART_CACHE_ENDPOINTS

# SQLite cache with custom settings
custom_config = CacheConfig(
    backend="sqlite",
    cache_dir="./my_cache",
    endpoint_config=SMART_CACHE_ENDPOINTS,
)

# Memory cache with custom expiration
memory_config = CacheConfig(
    backend="memory",
    endpoint_config=SMART_CACHE_ENDPOINTS,
)
# --8<-- [end:smart-custom]
