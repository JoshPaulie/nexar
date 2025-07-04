#!/usr/bin/env python3
"""Example demonstrating API monitoring and logging functionality."""

import logging
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.logging import configure_logging

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if not api_key:
    sys.exit("Please set RIOT_API_KEY environment variable")

# Example 1: Basic logging
print("=== Example 1: Basic Logging ===")

# Enable INFO level logging to see API calls
print("Enabling INFO level logging...")
configure_logging(logging.INFO)

client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

print("\nMaking API calls (watch the log output):")
player = client.get_player("bexli", "bex")

# These calls will show in logs with timing and cache info
print("- Getting account data...")
account = player.riot_account

print("- Getting summoner data...")
summoner = player.summoner

print("- Getting league entries...")
league_entries = player.league_entries

print("- Getting recent matches...")
matches = player.get_recent_matches(count=3)

# Example 2: Debug logging
print("\n\n=== Example 2: Debug Logging ===")

print("Enabling DEBUG level logging for detailed information...")
configure_logging(logging.DEBUG)

# Clear the client's cache to force fresh API calls
client.clear_cache()

print("\nMaking API calls with DEBUG logging:")
# This will show even more detailed information
performance_summary = player.get_performance_summary(count=5)
print(f"Performance: {performance_summary['win_rate']}% win rate")

# Example 3: Logging statistics
print("\n\n=== Example 3: API Call Statistics ===")

# Set back to INFO to reduce noise
configure_logging(logging.INFO)

print("Current API call statistics:")
stats = client.get_api_call_stats()
for stat_name, count in stats.items():
    print(f"  {stat_name}: {count}")

# Print a summary of all API calls made
print("\nAPI call summary:")
client.print_api_call_summary()

# Example 4: Monitoring cache performance
print("\n\n=== Example 4: Cache Performance Monitoring ===")

# Reset stats to start fresh
client._reset_api_call_count()

print("Making duplicate API calls to demonstrate cache effectiveness:")

# First round - fresh calls
print("\nRound 1 (fresh calls):")
player2 = client.get_player("bexli", "bex")
_ = player2.riot_account
_ = player2.summoner
_ = player2.league_entries

client.print_api_call_summary()

# Second round - should be mostly cached
print("\nRound 2 (cached calls):")
player3 = client.get_player("bexli", "bex")
_ = player3.riot_account
_ = player3.summoner
_ = player3.league_entries

client.print_api_call_summary()

# Example 5: Disabling logging
print("\n\n=== Example 5: Disabling Logging ===")

print("Disabling logging...")
configure_logging(logging.WARNING)  # Only show warnings and errors

print("Making API calls with minimal logging:")
top_champions = player.get_top_champions(top_n=3, count=10)
print(f"Top champions: {[champ.champion_name for champ in top_champions]}")

# Final statistics
print("\nFinal API statistics:")
stats = client.get_api_call_stats()
for stat_name, count in stats.items():
    print(f"  {stat_name}: {count}")

print("\n=== Logging Demo Complete ===")
print("Logging levels:")
print("- DEBUG: Very detailed information for debugging")
print("- INFO: General information about API calls and cache hits")
print("- WARNING: Only warnings and errors (minimal output)")
print("- Use configure_logging() to control verbosity")
