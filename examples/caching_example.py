"""Example demonstrating the caching functionality of Nexar."""

import os
import time

from nexar import (
    NO_CACHE_CONFIG,
    SMART_CACHE_CONFIG,
    CacheConfig,
    NexarClient,
    RegionV4,
    RegionV5,
)


# Example of different cache configurations
def main():
    """Demonstrate caching functionality."""
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        print("Please set RIOT_API_KEY environment variable")
        return

    # Example 1: Default caching (1 hour for everything)
    print("=== Example 1: Default Caching ===")
    client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )

    # Make the same call twice to demonstrate caching
    print("First call (fresh):")
    start = time.time()
    account = client.get_riot_account("bexli", "bex")
    elapsed = time.time() - start
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Account: {account.game_name}#{account.tag_line}")

    print("Second call (cached):")
    start = time.time()
    account = client.get_riot_account("bexli", "bex")
    elapsed = time.time() - start
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Account: {account.game_name}#{account.tag_line}")

    print(f"Cache info: {client.get_cache_info()}")
    print()

    # Example 2: Smart caching (different TTL per endpoint type)
    print("=== Example 2: Smart Caching ===")
    smart_client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    )

    # Account data (cached for 24 hours)
    account = smart_client.get_riot_account("bexli", "bex")
    summoner = smart_client.get_summoner_by_puuid(account.puuid)
    print(f"Summoner level: {summoner.summoner_level}")

    # League entries (cached for 5 minutes)
    leagues = smart_client.get_league_entries_by_puuid(account.puuid)
    print(f"League entries: {len(leagues)}")

    print(f"Smart cache info: {smart_client.get_cache_info()}")
    print()

    # Example 3: No caching
    print("=== Example 3: No Caching ===")
    no_cache_client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=NO_CACHE_CONFIG,
    )

    print("All calls will be fresh (no caching):")
    start = time.time()
    account = no_cache_client.get_riot_account("bexli", "bex")
    elapsed = time.time() - start
    print(f"  First call time: {elapsed:.3f}s")

    start = time.time()
    account = no_cache_client.get_riot_account("bexli", "bex")
    elapsed = time.time() - start
    print(f"  Second call time: {elapsed:.3f}s")

    print(f"No cache info: {no_cache_client.get_cache_info()}")
    print()

    # Example 4: Custom cache configuration
    print("=== Example 4: Custom Configuration ===")
    custom_config = CacheConfig(
        enabled=True,
        cache_name="custom_cache",
        backend="sqlite",
        expire_after=60,  # 1 minute default
        endpoint_config={
            # Cache account lookups for 1 hour
            "/riot/account/v1/accounts/by-riot-id": {"expire_after": 3600},
            # Don't cache league entries (they change frequently)
            "/lol/league/v4/entries/by-puuid": {"enabled": False},
        },
    )

    custom_client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=custom_config,
    )

    # This will be cached for 1 hour
    account = custom_client.get_riot_account("bexli", "bex")

    # This will NOT be cached (fresh every time)
    leagues = custom_client.get_league_entries_by_puuid(account.puuid)
    print(f"League entries (not cached): {len(leagues)}")

    print(f"Custom cache info: {custom_client.get_cache_info()}")

    # Clear cache
    custom_client.clear_cache()
    print("Cache cleared!")


if __name__ == "__main__":
    main()
