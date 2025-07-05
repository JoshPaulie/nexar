#!/usr/bin/env python3
"""Basic example showing how to get player information using the Player API."""

import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if not api_key:
    sys.exit("Please set RIOT_API_KEY environment variable")

# Create client
client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

# Create a player object (abstracts away riot id lookup)
player = client.get_player("bexli", "bex")
print(f"Analyzing player: {player}")

# Access basic player info
print(f"Summoner Level: {player.summoner.summoner_level}")
print(f"PUUID: {player.puuid}")

# Check rank
if player.rank:
    rank = player.rank
    print(
        f"Solo Queue Rank: {rank.tier.value} {rank.rank.value} ({rank.league_points} LP)"
    )
    print(f"Win Rate: {rank.win_rate:.1f}% ({rank.wins}W/{rank.losses}L)")
    if rank.mini_series:
        print(f"In Promos: {rank.mini_series.progress}")
else:
    print("Solo Queue Rank: Unranked")

if player.flex_rank:
    flex = player.flex_rank
    print(
        f"Flex Queue Rank: {flex.tier.value} {flex.rank.value} ({flex.league_points} LP)"
    )
else:
    print("Flex Queue Rank: Unranked")

# Show league entries (all queues)
print("\nAll League Entries:")
for entry in player.league_entries:
    print(f"  {entry.queue_type.value}: {entry.tier.value} {entry.rank.value}")
