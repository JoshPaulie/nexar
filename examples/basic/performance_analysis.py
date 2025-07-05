#!/usr/bin/env python3
"""Basic example showing champion statistics and performance summary."""

import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import QueueId, RegionV4, RegionV5

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

# Create player object
player = client.get_player("bexli", "bex")
print(f"Analyzing performance for {player}")

# Get performance summary from last 20 games
print("\n=== Performance Summary (Last 20 Games) ===")
summary = player.get_performance_summary(count=20)

print(f"Total Games: {summary['total_games']}")
print(f"Win Rate: {summary['win_rate']}% ({summary['wins']}W/{summary['losses']}L)")
print(
    f"Average KDA: {summary['avg_kills']}/{summary['avg_deaths']}/{summary['avg_assists']} ({summary['avg_kda']})"
)
print(f"Average CS: {summary['avg_cs']}")
print(f"Average Game Duration: {summary['avg_game_duration_minutes']} minutes")

# Check if on win streak
if player.is_on_win_streak(min_games=3):
    print("\n🔥 Player is on a WIN STREAK! 🔥")
else:
    print("\n📈 Not currently on a win streak")

# Get top champions (from last 50 games)
print("\n=== Top Champions (Last 50 Games) ===")
top_champions = player.get_top_champions(top_n=5, count=50)

for i, champ in enumerate(top_champions, 1):
    print(f"{i}. {champ.champion_name}")
    print(f"   Games: {champ.games_played} | Win Rate: {champ.win_rate:.1f}%")
    print(
        f"   Avg KDA: {champ.avg_kills:.1f}/{champ.avg_deaths:.1f}/{champ.avg_assists:.1f} ({champ.avg_kda:.2f})"
    )

# Get ranked performance summary
print("\n=== Ranked Solo Queue Performance (Last 20 Games) ===")
ranked_summary = player.get_performance_summary(count=20, queue=QueueId.RANKED_SOLO_5x5)

if ranked_summary["total_games"] > 0:
    print(f"Ranked Games: {ranked_summary['total_games']}")
    print(f"Ranked Win Rate: {ranked_summary['win_rate']}%")
    print(f"Ranked Avg KDA: {ranked_summary['avg_kda']}")
else:
    print("No recent ranked games found")
