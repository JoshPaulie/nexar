"""Example demonstrating rate limiting functionality with the Player API."""

import asyncio
import os
import sys
import time

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.rate_limiter import RateLimit, RateLimiter


def print_rate_limit_status(client, title: str) -> None:
    """Print current rate limit status."""
    print(f"\n{title}")
    status = client.get_rate_limit_status()
    for limit_name, limit_info in status.items():
        usage = limit_info["current_usage"]
        limit = limit_info["requests"]
        window = limit_info["window_seconds"]
        print(f"  {limit_name}: {usage}/{limit} requests per {window}s")


async def main() -> None:
    """Demonstrate rate limiting functionality with the Player API."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Example 1: Default rate limiting
    print("=== Example 1: Default Rate Limiting ===")

    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as client:
        print_rate_limit_status(client, "Initial rate limit status:")

        # Make several API calls and monitor rate limiting
        print("\nMaking API calls with default rate limiting...")
        player = await client.get_player("bexli", "bex")

        for i in range(5):
            print(f"\nAPI call {i + 1}:")
            try:
                if i == 0:
                    # riot account immediately available
                    print("  ✓ Got riot account (immediate)")
                elif i == 1:
                    await player.get_summoner()
                    print("  ✓ Got summoner data")
                elif i == 2:
                    await player.get_league_entries()
                    print("  ✓ Got league entries")
                elif i == 3:
                    await player.get_matches(count=3)
                    print("  ✓ Got recent matches")
                else:
                    await player.get_rank()
                    print("  ✓ Got rank info")

                print_rate_limit_status(client, f"Rate limits after call {i + 1}:")
            except Exception as e:
                print(f"  ✗ Failed: {e}")

    # Example 2: Custom conservative rate limiting
    print("\n\n=== Example 2: Custom Conservative Rate Limiting ===")

    # Create a more conservative rate limiter
    conservative_rate_limiter = RateLimiter(
        rate_limits=[
            RateLimit(requests=10, window_seconds=60),  # 10 requests per minute
            RateLimit(requests=50, window_seconds=120),  # 50 requests per 2 minutes
        ],
    )

    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
        rate_limiter=conservative_rate_limiter,
    ) as conservative_client:
        print("Custom rate limiter configuration:")
        print_rate_limit_status(conservative_client, "Conservative rate limits:")

        # Example 3: Bulk operations with rate limiting protection
        print("\n\n=== Example 3: Bulk Operations with Rate Limiting ===")

        print("Attempting to fetch data for multiple operations rapidly...")
        start_time = time.time()

        # Make aggressive API calls
        player = await conservative_client.get_player("bexli", "bex")
        operations = [
            ("Get riot account", lambda: conservative_client.get_player("bexli", "bex")),
            ("Get summoner", lambda: player.get_summoner()),
            ("Get league entries", lambda: player.get_league_entries()),
            ("Get matches", lambda: player.get_matches(count=3)),
            ("Get rank", lambda: player.get_rank()),
        ]

        for i, (operation_name, operation) in enumerate(operations):
            try:
                print(f"Operation {i + 1}: {operation_name}...")
                await operation()
                print(f"  ✓ {operation_name} completed")
                print_rate_limit_status(conservative_client, f"After operation {i + 1}:")
            except Exception as e:
                print(f"  ✗ {operation_name} failed: {e}")

        elapsed_time = time.time() - start_time
        print(f"\nCompleted {len(operations)} operations in {elapsed_time:.2f} seconds")

        print("\n=== Rate Limiting Demo Complete ===")
        print("Key takeaways:")
        print("- Rate limiting prevents API quota exhaustion")
        print("- Custom rate limiters can be more conservative than defaults")
        print("- The SDK automatically handles delays to stay within limits")
        print("- Conservative rate limits help avoid hitting API limits")


if __name__ == "__main__":
    asyncio.run(main())
