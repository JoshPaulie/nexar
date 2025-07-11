# Caching in Nexar

!!! Tip

    This is a bit of a more advanced topic, involving the actual under the hood API calls to Riot, which Nexar tries to hide from the user.

    By and large, simply use the SMART_CACHE_CONFIG:
    ```python
    -8<-- "quick_start/01_client_demo.py:declaration"
    ```

    This keeps a local, persistent storage of data to reduce API calls.

Nexar includes built-in caching functionality to reduce API calls and improve performance. Cached responses are either stored locally (sqlite file) or in memory, and reused until they expire.

Via `CacheConfig`, one can specify a default cache time, pick your storage backend, and configure endpoint TTLs (time-to-live's).

## Quick Start

By default, Nexar uses "dumb" caching, which caches all responses for an hour to an SQLite file in your CWD, regardless of the endpoint:

```python
-8<-- "caching/default.py"
```

## Cache Backends

Nexar supports two cache backends:

- **SQLite** (default): Persistent cache stored in a file

```python
-8<-- "caching/demo.py:smart-sqlite"
```

- **Memory**: Fast in-memory cache (cleared when application exits)

```python
-8<-- "caching/demo.py:smart-memory"
```

## Custom Cache Configuration

!!! note

    For creating your own endpoint config, consult [the Riot API docs](https://developer.riotgames.com/apis)

You can create your own cache configuration, and set things like the path to your database file or a custom endpoint durations, etc.

```python
-8<-- "caching/demo.py:cache-config"
```

On, even easier, use the same endpoint config as the "smart" presets 

```python
-8<-- "caching/demo.py:smart-custom"
```

## Predefined Configurations

### DEFAULT_CACHE_CONFIG
Uses SQLite backend with 1-hour expiration for all endpoints.

### SMART_CACHE_CONFIG/SMART_CACHE_CONFIG_MEMORY
Intelligently caches different endpoint types for optimal durations:

- Account/Summoner data: 24 hours (rarely changes)
- Match data: Forever (matches are immutable)
- League entries: 5 minutes (rankings change frequently)  
- Match IDs: 1 minute (new matches appear)

### MEMORY_CACHE_CONFIG
Uses in-memory caching with 30-minute expiration.

### NO_CACHE_CONFIG
Disables caching entirely - every request hits the API.

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
