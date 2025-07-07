# Caching in Nexar

Nexar includes built-in caching functionality using `aiohttp-client-cache` to reduce API calls and improve performance.

## Quick Start

```python
import asyncio
from nexar import NexarClient, CacheConfig, RegionV4, RegionV5

async def main() -> None:
    # Basic caching (1 hour default TTL)
    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    ) as client:
        # Use client here
        pass

    # Custom cache configuration
    cache_config = CacheConfig(
        enabled=True,
        cache_name="my_cache",
        expire_after=3600,  # 1 hour in seconds
        backend="sqlite",   # or "memory", "filesystem", etc.
    )

    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=cache_config,
    ) as client:
        # Use client here
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

## Performance Comparison

Real-world performance improvements with caching:

```python
import asyncio
from nexar import NexarClient, SMART_CACHE_CONFIG, RegionV4, RegionV5

async def main() -> None:
    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as client:
        # First call hits the API (~200-400ms)
        player = client.get_player("bexli", "bex")

        # Second call uses cache (~2-5ms, 80-100x faster!)
        player = client.get_player("bexli", "bex")

if __name__ == "__main__":
    asyncio.run(main())
```
## Predefined Configurations

Nexar provides several predefined cache configurations:

### DEFAULT_CACHE_CONFIG
- Caches all endpoints for 1 hour
- Uses SQLite backend
- Good for general use

### SMART_CACHE_CONFIG
- Different TTL for different endpoint types:
  - Account/Summoner data: 24 hours (rarely changes)
  - Match data: Forever (matches are immutable)
  - League entries: 5 minutes (rankings change frequently)
  - Match IDs: 1 minute (new matches appear)

### LONG_CACHE_CONFIG
- Caches everything for 24 hours
- Good for development/testing

### PERMANENT_CACHE_CONFIG
- Caches everything forever
- Use with caution in production

### NO_CACHE_CONFIG
- Disables caching entirely
- Every request hits the API

```python
import asyncio
from nexar import NexarClient, SMART_CACHE_CONFIG, RegionV4, RegionV5

async def main() -> None:
    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as client:
        # Use client here
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

## Custom Endpoint Configuration

You can configure caching per endpoint:

```python
import asyncio
from nexar import NexarClient, CacheConfig, RegionV4, RegionV5

async def main() -> None:
    cache_config = CacheConfig(
        enabled=True,
        expire_after=60,  # Default 1 minute
        endpoint_config={
            # Cache account lookups for 1 hour
            "/riot/account/v1/accounts/by-riot-id": {"expire_after": 3600},
            
            # Cache match data forever (matches don't change)
            "/lol/match/v5/matches": {"expire_after": None},
            
            # Don't cache league entries at all
            "/lol/league/v4/entries/by-puuid": {"enabled": False},
        }
    )

    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=cache_config,
    ) as client:
        # Use client here
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

## Cache Management

```python
import asyncio
from nexar import NexarClient, RegionV4, RegionV5

async def main() -> None:
    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    ) as client:
        # Get cache information
        info = await client.get_cache_info()
        print(info)
        # {'enabled': True, 'backend': 'sqlite', 'cache_name': 'nexar_cache', ...}

        # Clear all cached data
        await client.clear_cache()

        # Check API call count (includes both fresh and cached calls)
        client.print_api_call_summary()

if __name__ == "__main__":
    asyncio.run(main())
```

## Logging

Enable logging to see cache hits and misses:

```python
import asyncio
import logging
from nexar import NexarClient, configure_logging, RegionV4, RegionV5

async def main() -> None:
    # Configure Nexar logging (default level is INFO)
    configure_logging(logging.INFO)

    # Or enable debug logging for more details
    configure_logging(logging.DEBUG)

    # Create your client and make API calls
    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    ) as client:
        # Make API calls here
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

This will show output like:
```
[nexar] API Call #1: /riot/account/v1/accounts/by-riot-id/bexli/bex (region: americas)
[nexar]   ✓ Success (Status: 200, fresh)
[nexar] API Call #2: /riot/account/v1/accounts/by-riot-id/bexli/bex (region: americas)
[nexar]   ✓ Success (Status: 200, from cache)
[nexar] API Stats: 2 calls total, 1 fresh, 1 cached (50.0% cache hit rate)
```

### Logging Levels

- **INFO**: Shows API calls, success/errors, and cache statistics
- **DEBUG**: Includes parameters, cache configuration details, and more verbose output

### Getting Statistics

You can programmatically access API call statistics:

```python
import asyncio
from nexar import NexarClient, RegionV4, RegionV5

async def main() -> None:
    async with NexarClient(
        riot_api_key="your_api_key",
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    ) as client:
        # Get detailed statistics
        stats = client.get_api_call_stats()
        print(f"Total calls: {stats['total_calls']}")
        print(f"Cache hits: {stats['cache_hits']}")
        print(f"Fresh calls: {stats['fresh_calls']}")

        # Print formatted summary
        client.print_api_call_summary()

if __name__ == "__main__":
    asyncio.run(main())
```

## Cache Storage

By default, caches are stored as SQLite files in the current working directory:
- `nexar_cache.sqlite` (default)
- Custom name: `{cache_name}.sqlite`

## Best Practices

1. **Use SMART_CACHE_CONFIG** for production applications - it provides sensible defaults
2. **Use longer TTLs for static data** like account information and match details
3. **Use shorter TTLs for dynamic data** like league rankings and recent matches
4. **Disable caching for real-time data** if you need the absolute latest information
5. **Clear cache periodically** if you're running long-lived applications
6. **Monitor cache size** in production to avoid disk space issues

## Performance Impact

Caching can significantly reduce API calls:
- First call: ~200-500ms (network request)
- Cached call: ~1-5ms (local database lookup)
- Typical cache hit rate: 70-90% in most applications

This helps you stay within Riot's rate limits while providing faster response times.
