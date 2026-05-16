# Caching

!!! Tip

    TLDR: Simply use the default caching for most projects:

    ```python
    -8<-- "quick_start/01_client_demo.py:declaration-smart-cache"
    ```

Caching is "smart" by using varying TTLs (time-to-live) for each endpoint:

| Endpoint           | Cache Duration |
| ------------------ | -------------- |
| Matches            | Forever        |
| Accounts/Summoners | 24 hours       |
| League Entries     | 5 minutes      |
| Match IDs          | 1 minute       |

All other requests use the default expiration time (1 hour).

Use `CacheConfig` to specify a default cache time, pick a storage backend, and configure the cache location.

## Quick Start

By default, caching uses a 1-hour TTL and stores responses to a SQLite file in `~/.nexar/`:

```python
-8<-- "caching/default.py"
```

## Cache Backends

Two cache backends are supported, both of which respect the smart TTL overrides:

- SQLite (default): Persistent cache stored in a file. Best for long-running applications and CLI tools.
- Memory: Ephemeral in-memory cache. Best for one-off scripts, tests, and environments without write access.

Configure the backend using `CacheConfig`:

```python
-8<-- "caching/custom_backend.py"
```

### SQLite Cache Location

The SQLite backend creates `nexar_cache.sqlite` in `~/.nexar/` by default. The name and location can be customized:

```python
config = CacheConfig(
    backend="sqlite",
    cache_name="my_app_cache",  # Creates my_app_cache.sqlite
    cache_dir="/tmp/cache"      # Saves to /tmp/cache/my_app_cache.sqlite
)
```

## Custom Cache Configuration

Create custom configurations for specific expiration times:

```python
-8<-- "caching/demo.py:cache-config"
```

## Predefined Configurations

### DEFAULT_CACHE_CONFIG
Uses the SQLite backend with a 1-hour default TTL. The smart endpoint overrides (Matches, Accounts, etc.) are active by default.

### NO_CACHE_CONFIG
Disables caching entirely, every request hits the API.

## Cache Management

Manage the cache and view statistics through the client:

```python
async with NexarClient(riot_api_key="your_api_key") as client:
    # Get cache information (size, backend, count)
    info = await client.get_cache_info()
    
    # Clear all cached data
    await client.clear_cache()
    
    # View API call statistics (hits, fresh calls, rate)
    stats = client.get_api_call_stats()
    client.print_api_call_summary()
```

### Manual Refresh

Models like `Player` provide a `refresh_cache()` method to clear their internal state and force fresh API calls on the next access.

## Best Practices

1. Use the default cache for most applications. The SQLite backend with its smart endpoint-specific TTLs is optimized for Riot's API.
2. Use the SQLite backend when you want data to persist between runs. This speeds up API calls and saves rate limits.
3. Use the Memory backend for scripts where persistence isn't needed or where file system access is restricted.
4. Disable caching only when you need real-time data for every request. Use `NO_CACHE_CONFIG` sparingly.
