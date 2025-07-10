# Caching in Nexar

!!! note

    This is a bit of a more advanced topic, involving the actual under-the-hood API calls to Riot, which Nexar tries to hide from the user.

    By and large, simply use the SMART_CACHE_CONFIG:
    ```python
    -8<-- "quick_start/01_client_demo.py:declaration"
    ```

    This keeps a local, persistent storage of data to reduce API calls.

Nexar includes built-in caching functionality to reduce API calls and improve performance. Cached responses are stored locally and reused until they expire.

## Quick Start

By default, Nexar uses "dumb" caching, which caches all responses for an hour, regardless of the endpoint:

```python
import asyncio
from nexar import NexarClient, RegionV4, RegionV5

async def main() -> None:
    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    ) as client:
        # First call hits the API
        player = await client.get_player("bexli", "bex")
        
        # Second call uses cached data
        player = await client.get_player("bexli", "bex")

if __name__ == "__main__":
    asyncio.run(main())
```

## Cache Backends

Nexar supports two cache backends:

- **SQLite** (default): Persistent cache stored in a file
- **Memory**: Fast in-memory cache (cleared when application exits)

```python
from nexar import CacheConfig, MEMORY_CACHE_CONFIG

# Memory cache example
async with NexarClient(
    riot_api_key="your_api_key",
    cache_config=MEMORY_CACHE_CONFIG,
) as client:
    # Use client here
    pass
```

## Predefined Configurations

### DEFAULT_CACHE_CONFIG
Uses SQLite backend with 1-hour expiration for all endpoints.

### SMART_CACHE_CONFIG
Intelligently caches different endpoint types for optimal durations:

- Account/Summoner data: 24 hours (rarely changes)
- Match data: Forever (matches are immutable)
- League entries: 5 minutes (rankings change frequently)  
- Match IDs: 1 minute (new matches appear)

### MEMORY_CACHE_CONFIG
Uses in-memory caching with 30-minute expiration.

### NO_CACHE_CONFIG
Disables caching entirely - every request hits the API.

## Custom Cache Configuration

You can create your own cache configuration:

```python
from nexar import CacheConfig

# SQLite cache with custom settings
custom_config = CacheConfig(
    backend="sqlite",
    cache_dir="./my_cache",
    cache_name="riot_data",
    expire_after=7200,  # 2 hours
)

# Memory cache with custom expiration
memory_config = CacheConfig(
    backend="memory",
    expire_after=900,  # 15 minutes
)

# Per-endpoint configuration
advanced_config = CacheConfig(
    expire_after=3600,  # Default 1 hour
    endpoint_config={
        # Cache account lookups for 24 hours
        "/riot/account/v1/accounts/by-riot-id": {"expire_after": 86400},
        
        # Cache matches forever
        "/lol/match/v5/matches": {"expire_after": None},
        
        # Don't cache league entries
        "/lol/league/v4/entries/by-puuid": {"enabled": False},
    }
)

async with NexarClient(
    riot_api_key="your_api_key",
    cache_config=custom_config,
) as client:
    # Use client here
    pass
```

## Cache Management

```python
async with NexarClient(riot_api_key="your_api_key") as client:
    # Get cache information
    info = await client.get_cache_info()
    
    # Clear cached data
    await client.clear_cache()
    
    # View API call statistics
    client.print_api_call_summary()
```

## Best Practices

1. **Use SMART_CACHE_CONFIG** for most applications
2. **Use memory backend** for short-lived scripts or when you don't want persistent files
3. **Customize expiration times** based on how frequently your data changes
4. **Disable caching** for specific endpoints that need real-time data
