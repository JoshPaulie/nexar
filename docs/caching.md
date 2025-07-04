# Caching in Nexar

Nexar includes built-in caching functionality using `requests-cache` to reduce API calls and improve performance.

## Quick Start

```python
from nexar import NexarClient, CacheConfig, RegionV4, RegionV5

# Basic caching (1 hour default TTL)
client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
)

# Custom cache configuration
cache_config = CacheConfig(
    enabled=True,
    cache_name="my_cache",
    expire_after=3600,  # 1 hour in seconds
    backend="sqlite",   # or "memory", "filesystem", etc.
)

client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=cache_config,
)
```

## Performance Comparison

Real-world performance improvements with caching:

```python
from nexar import NexarClient, SMART_CACHE_CONFIG

client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

# First call hits the API (~200-400ms)
player = client.get_player("bexli", "bex")

# Second call uses cache (~2-5ms, 80-100x faster!)
player = client.get_player("bexli", "bex")
```

**Typical Performance Improvements:**
- Account lookup: 409ms → 5ms (81x faster)
- Summoner lookup: 376ms → 2ms (188x faster)  
- League entries: 133ms → 2ms (66x faster)
- Speed improvement: 80-200x faster
- Typical cache hit rate: 70-90%

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
from nexar import NexarClient, SMART_CACHE_CONFIG

client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)
```

## Custom Endpoint Configuration

You can configure caching per endpoint:

```python
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
```

## Cache Management

```python
# Get cache information
info = client.get_cache_info()
print(info)
# {'enabled': True, 'backend': 'sqlite', 'cache_name': 'nexar_cache', ...}

# Clear all cached data
client.clear_cache()

# Check API call count (includes both fresh and cached calls)
client.print_api_call_summary()
```

## Debugging

Enable debug mode to see cache hits and misses:

```bash
export NEXAR_DEBUG=1
```

This will show output like:
```
[NEXAR_DEBUG] API Call #1: /riot/account/v1/accounts/by-riot-id/bexli/bex (region: americas)
[NEXAR_DEBUG]   ✓ Success (Status: 200, fresh)
[NEXAR_DEBUG] API Call #2: /riot/account/v1/accounts/by-riot-id/bexli/bex (region: americas)
[NEXAR_DEBUG]   ✓ Success (Status: 200, from cache)
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
