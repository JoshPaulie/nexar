#!/usr/bin/env python3
"""Example demonstrating rate limiting functionality with the Player API."""

import os
import sys
import time

from feature_logging import SMART_CACHE_CONFIG

from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.rate_limiter import RateLimit, RateLimiter

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if not api_key:
    sys.exit("Please set RIOT_API_KEY environment variable")


def print_rate_limit_status(client, title):
    """Print current rate limit status."""
    print(f"\n{title}")
    status = client.get_rate_limit_status()
    for limit_name, limit_info in status.items():
        usage = limit_info["current_usage"]
        limit = limit_info["requests"]
        window = limit_info["window_seconds"]
        print(f"  {limit_name}: {usage}/{limit} requests per {window}s")


# Example 1: Default rate limiting
print("=== Example 1: Default Rate Limiting ===")

client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

print_rate_limit_status(client, "Initial rate limit status:")

# Make several API calls and monitor rate limiting
print("\nMaking API calls with default rate limiting...")
player = client.get_player("bexli", "bex")

for i in range(5):
    print(f"\nAPI call {i + 1}:")
    start_time = time.time()

    # Access different player data (some may be cached)
    if i == 0:
        data = player.riot_account
        print(f"  Fetched account: {data.game_name}#{data.tag_line}")
    elif i == 1:
        data = player.summoner
        print(f"  Fetched summoner: Level {data.summoner_level}")
    elif i == 2:
        data = player.league_entries
        print(f"  Fetched {len(data)} league entries")
    elif i == 3:
        data = player.get_recent_matches(count=1)
        print(f"  Fetched {len(data)} recent matches")
    else:
        summary = player.get_performance_summary(count=5)
        print(f"  Calculated performance: {summary['win_rate']}% win rate")

    elapsed = time.time() - start_time
    print(f"  Time taken: {elapsed:.3f}s")

    print_rate_limit_status(client, "  Current status:")

# Example 2: Custom rate limiting
print("\n\n=== Example 2: Custom Rate Limiting ===")

# Create a more conservative rate limiter
conservative_rate_limiter = RateLimiter(
    [
        RateLimit(requests=10, window_seconds=1),  # 10 requests per second
        RateLimit(requests=50, window_seconds=120),  # 50 requests per 2 minutes
    ],
)

conservative_client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
    rate_limiter=conservative_rate_limiter,
)

print("Custom rate limiter configuration:")
print_rate_limit_status(conservative_client, "Conservative rate limits:")

# Example 3: Aggressive API usage with rate limiting protection
print("\n\n=== Example 3: Bulk Operations with Rate Limiting ===")

print("Attempting to fetch data for multiple operations rapidly...")
start_time = time.time()

# This will automatically be rate limited to prevent API errors
player = conservative_client.get_player("bexli", "bex")

operations = [
    ("Account data", lambda: player.riot_account),
    ("Summoner data", lambda: player.summoner),
    ("League entries", lambda: player.league_entries),
    ("Recent matches", lambda: player.get_recent_matches(count=3)),
    ("Performance summary", lambda: player.get_performance_summary(count=10)),
    ("Top champions", lambda: player.get_top_champions(top_n=3, count=20)),
]

for op_name, operation in operations:
    op_start = time.time()
    try:
        result = operation()
        op_time = time.time() - op_start
        print(f"  ✅ {op_name}: completed in {op_time:.3f}s")
    except Exception as e:
        op_time = time.time() - op_start
        print(f"  ❌ {op_name}: failed after {op_time:.3f}s - {e}")

total_time = time.time() - start_time
print(f"\nTotal time for all operations: {total_time:.3f}s")

print_rate_limit_status(conservative_client, "Final rate limit status:")

# Example 4: Rate limit recovery
print("\n\n=== Example 4: Rate Limit Management ===")

print("API call statistics:")
stats = conservative_client.get_api_call_stats()
for stat_name, count in stats.items():
    print(f"  {stat_name}: {count}")

# Reset rate limiter
print("\nResetting rate limiter...")
conservative_client.reset_rate_limiter()
print_rate_limit_status(conservative_client, "After reset:")

print("\n=== Rate Limiting Demo Complete ===")
print("Key takeaways:")
print("- Rate limiting prevents API errors and account suspension")
print("- Caching reduces the need for API calls")
print("- Custom rate limiters can be more conservative than defaults")
print("- The SDK automatically handles delays to stay within limits")
