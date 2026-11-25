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
