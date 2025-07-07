"""Example demonstrating the caching functionality of Nexar."""

import asyncio
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


async def time_operation(description: str, operation) -> object:
    """Time an async operation and print the results."""
    print(f"\n{description}")
    start = time.time()
    result = await operation()
    elapsed = time.time() - start
    print(f"  ⏱️  Time: {elapsed:.3f}s")
    return result


async def main() -> None:
    """Demonstrate the caching functionality of Nexar."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Example 1: No caching vs default caching
    print("=== Example 1: Caching Impact ===")

    # Test without caching
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=NO_CACHE_CONFIG,
    ) as no_cache_client:
        # Compare performance without cache
        player_no_cache = await time_operation(
            "Getting player info (no cache):",
            lambda: no_cache_client.get_player("bexli", "bex"),
        )

    # Test with default caching
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=DEFAULT_CACHE_CONFIG,
    ) as cached_client:
        player = await cached_client.get_player("bexli", "bex")

        # First call with cache (fresh)
        player_cached = await time_operation(
            "Getting player info (first call with cache):",
            lambda: cached_client.get_player("bexli", "bex"),
        )

        # Second call with cache (should be faster)
        player_cached_2 = await time_operation(
            "Getting player info (second call with cache):",
            lambda: cached_client.get_player("bexli", "bex"),
        )

        print(f"Cache info: {cached_client.get_cache_info()}")

    # Example 2: Smart caching configuration
    print("\n\n=== Example 2: Smart Caching ===")
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as smart_client:
        player = await smart_client.get_player("bexli", "bex")

        # Account data (cached for 24 hours in smart config)
        await time_operation("Getting account data (fresh):", lambda: smart_client.get_player("bexli", "bex"))
        await time_operation("Getting account data (cached 24h):", lambda: smart_client.get_player("bexli", "bex"))

        # League entries (cached for 5 minutes in smart config)
        await time_operation("Getting league entries (fresh):", lambda: player.get_league_entries())
        await time_operation("Getting league entries (cached 5m):", lambda: player.get_league_entries())

        # Matches (cached for 30 minutes in smart config)
        await time_operation("Getting matches (fresh):", lambda: player.get_matches(count=5))
        await time_operation("Getting matches (cached 30m):", lambda: player.get_matches(count=5))

        print(f"Smart cache info: {smart_client.get_cache_info()}")

    # Example 3: Custom cache configuration
    print("\n\n=== Example 3: Custom Cache Configuration ===")
    custom_cache_config = CacheConfig(
        expire_after=3600,  # 1 hour default
        endpoint_config={
            # Cache riot account for 2 hours
            "/riot/account/v1/accounts/by-riot-id": {"expire_after": 7200},
            # Cache league entries for 30 seconds (very short for demo)
            "/lol/league/v4/entries/by-puuid": {"expire_after": 30},
            # No caching for matches
            "/lol/match/v5/matches/by-puuid": {"expire_after": 0},
            # Cache summoner for 1 hour
            "/lol/summoner/v4/summoners/by-puuid": {"expire_after": 3600},
        },
    )

    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=custom_cache_config,
    ) as custom_client:
        player = await custom_client.get_player("bexli", "bex")

        print("Using custom cache configuration:")
        print("- Riot account: 2 hours")
        print("- League entries: 30 seconds")
        print("- Matches: no caching")
        print("- Summoner: 1 hour")

        # Test the custom configuration
        await time_operation("Getting account (2h cache):", lambda: custom_client.get_player("bexli", "bex"))
        await time_operation("Getting account (cached):", lambda: custom_client.get_player("bexli", "bex"))

        await time_operation("Getting league entries (30s cache):", lambda: player.get_league_entries())
        await time_operation("Getting league entries (cached):", lambda: player.get_league_entries())

        await time_operation("Getting matches (no cache):", lambda: player.get_matches(count=3))
        await time_operation("Getting matches (no cache again):", lambda: player.get_matches(count=3))

        print(f"Custom cache info: {custom_client.get_cache_info()}")

    # Example 4: Cache configuration comparison
    print("\n\n=== Example 4: Cache Configuration Summary ===")
    print("NO_CACHE_CONFIG: No caching (always fresh data)")
    print("DEFAULT_CACHE_CONFIG: Balanced caching for most use cases")
    print("SMART_CACHE_CONFIG: Optimized caching for common patterns")
    print("Custom CacheConfig: Tailored to your specific needs")

    print("\n=== Caching Examples Complete ===")
    print("Choose the cache configuration that best fits your use case:")
    print("- Use NO_CACHE_CONFIG for always fresh data")
    print("- Use DEFAULT_CACHE_CONFIG for balanced performance")
    print("- Use SMART_CACHE_CONFIG for optimized common patterns")
    print("- Create custom CacheConfig for specific requirements")


if __name__ == "__main__":
    asyncio.run(main())
