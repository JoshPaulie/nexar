#!/usr/bin/env python3
"""Example demonstrating the caching functionality of Nexar."""

import os
import sys
import time

from nexar.cache import (
    DEFAULT_CACHE_CONFIG,
    NO_CACHE_CONFIG,
    SMART_CACHE_CONFIG,
    CacheConfig,
)
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if not api_key:
    sys.exit("Please set RIOT_API_KEY environment variable")


def time_operation(description: str, operation):
    """Time an operation and print the results."""
    print(f"\n{description}")
    start = time.time()
    result = operation()
    elapsed = time.time() - start
    print(f"  ⏱️  Time: {elapsed:.3f}s")
    return result


# Example 1: No caching vs default caching
print("=== Example 1: Caching Impact ===")

# Client without caching
no_cache_client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=NO_CACHE_CONFIG,
)

# Client with default caching
cached_client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=DEFAULT_CACHE_CONFIG,
)

# Compare performance without cache
player_no_cache = time_operation(
    "Getting player info (no cache):",
    lambda: no_cache_client.get_player("bexli", "bex"),
)

# First call with cache (fresh)
player_cached = time_operation(
    "Getting player info (first call with cache):",
    lambda: cached_client.get_player("bexli", "bex"),
)

# Second call with cache (should be faster)
player_cached_2 = time_operation(
    "Getting player info (second call with cache):",
    lambda: cached_client.get_player("bexli", "bex"),
)

print(f"Cache info: {cached_client.get_cache_info()}")

# Example 2: Smart caching configuration
print("\n\n=== Example 2: Smart Caching ===")
smart_client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

player = smart_client.get_player("bexli", "bex")

# Account data (cached for 24 hours in smart config)
time_operation("Getting account data (fresh):", lambda: player.riot_account)

time_operation("Getting account data (cached 24h):", lambda: player.riot_account)

# League entries (cached for 5 minutes in smart config)
time_operation("Getting league entries (fresh):", lambda: player.league_entries)

time_operation("Getting league entries (cached 5m):", lambda: player.league_entries)

print(f"Smart cache info: {smart_client.get_cache_info()}")

# Example 3: Custom cache configuration
print("\n\n=== Example 3: Custom Cache Configuration ===")

# Create a custom cache configuration
custom_cache_config = CacheConfig(
    enabled=True,
    cache_name="custom_nexar_cache",
    backend="sqlite",
    expire_after=1800,  # 30 minutes default
    endpoint_config={
        # Cache account data for 1 hour
        "/riot/account/v1/accounts/by-riot-id": {"expire_after": 3600},
        # Cache summoner data for 1 hour
        "/lol/summoner/v4/summoners/by-puuid": {"expire_after": 3600},
        # Cache match data forever (immutable)
        "/lol/match/v5/matches": {"expire_after": None},
        # Cache league data for only 2 minutes (frequently changing)
        "/lol/league/v4/entries/by-puuid": {"expire_after": 120},
    },
)

custom_client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=custom_cache_config,
)

print("Custom cache configuration:")
print(f"  Default expire: {custom_cache_config.expire_after}s")
print(f"  Cache backend: {custom_cache_config.backend}")
print(f"  Cache name: {custom_cache_config.cache_name}")

# Example 4: Cache management
print("\n\n=== Example 4: Cache Management ===")

# Show API call stats
print("Making some API calls to populate cache...")
player = smart_client.get_player("bexli", "bex")
_ = player.riot_account
_ = player.summoner
_ = player.league_entries

# Print API call statistics
print("\nAPI call statistics:")
stats = smart_client.get_api_call_stats()
for stat_name, count in stats.items():
    print(f"  {stat_name}: {count}")

# Clear cache
print("\nClearing cache...")
smart_client.clear_cache()
print("Cache cleared!")

# Show cache is now empty
print(f"Cache info after clearing: {smart_client.get_cache_info()}")

print("\n=== Caching Demo Complete ===")
print("Tips:")
print("- Use SMART_CACHE_CONFIG for most applications")
print("- Use NO_CACHE_CONFIG for development/testing")
print("- Create custom configs for specific needs")
print("- Monitor cache hits with get_api_call_stats()")
