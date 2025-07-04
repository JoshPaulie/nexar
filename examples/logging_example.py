"""Example demonstrating Nexar logging functionality."""

import logging
import os
import sys

import nexar

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if not api_key:
    sys.exit("Please set RIOT_API_KEY environment variable")

# Configure logging to see API calls and cache hits/misses
nexar.configure_logging(logging.INFO)

# Initialize the client
client = nexar.NexarClient(
    riot_api_key=api_key,
    default_v4_region=nexar.RegionV4.NA1,
    default_v5_region=nexar.RegionV5.AMERICAS,
    cache_config=nexar.SMART_CACHE_CONFIG,  # Enable smart caching
)

try:
    # Make the same API call twice to demonstrate caching
    print("Making first API call (should be fresh)...")
    account1 = client.get_riot_account("bexli", "bex")
    print(f"Found account: {account1.game_name}#{account1.tag_line}")

    print("\nMaking second API call (should be from cache)...")
    account2 = client.get_riot_account("bexli", "bex")
    print(f"Found account: {account2.game_name}#{account2.tag_line}")

    print("\nAPI Call Summary:")
    client.print_api_call_summary()

    print("\nDetailed Statistics:")
    stats = client.get_api_call_stats()
    print(f"  Total calls: {stats['total_calls']}")
    print(f"  Fresh calls: {stats['fresh_calls']}")
    print(f"  Cache hits: {stats['cache_hits']}")

    if stats["total_calls"] > 0:
        cache_hit_rate = (stats["cache_hits"] / stats["total_calls"]) * 100
        print(f"  Cache hit rate: {cache_hit_rate:.1f}%")

except nexar.RiotAPIError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Error: {e}")
