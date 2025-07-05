#!/usr/bin/env python3
"""Advanced example showing role-based performance analysis using the Player API."""

import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import QueueId, RegionV4, RegionV5

# Constants for analysis
TOP_CHAMPIONS_PER_ROLE = 3  # Show top N champions per role
MIN_GAMES_PER_CHAMPION = 2  # Only show champions with at least N games
MIN_GAMES_PER_ROLE = 3  # Minimum games played to consider a role for best/worst analysis
CHUNK_SIZE = 5  # Number of games per trend chunk
TOTAL_RECENT = 20  # Number of recent games to analyze for trends

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
print(f"Advanced role analysis for {player}")

# Get performance by role from recent ranked games
print("\n=== Performance by Role (Ranked Solo Queue) ===")
role_performance = player.get_recent_performance_by_role(
    count=50,
    queue=QueueId.RANKED_SOLO_5x5,
)

if not role_performance:
    print("No recent ranked games found")
    sys.exit()

# Sort roles by games played
sorted_roles = sorted(role_performance.items(), key=lambda x: x[1]["games_played"], reverse=True)

for role, stats in sorted_roles:
    if stats["games_played"] == 0:
        continue

    print(f"\n{role}:")
    print(f"  Games Played: {stats['games_played']}")
    print(f"  Win Rate: {stats['win_rate']}% ({stats['wins']}W/{stats['games_played'] - stats['wins']}L)")
    print(f"  Average KDA: {stats['avg_kills']}/{stats['avg_deaths']}/{stats['avg_assists']} ({stats['avg_kda']})")
    print(f"  Average CS: {stats['avg_cs']}")

# Find best and worst performing roles
best_role = max(
    [(role, stats) for role, stats in role_performance.items() if stats["games_played"] >= MIN_GAMES_PER_ROLE],
    key=lambda x: x[1]["win_rate"],
    default=(None, None),
)

worst_role = min(
    [(role, stats) for role, stats in role_performance.items() if stats["games_played"] >= MIN_GAMES_PER_ROLE],
    key=lambda x: x[1]["win_rate"],
    default=(None, None),
)

if best_role[0] and worst_role[0]:
    print(f"\n🎯 Best Role: {best_role[0]} ({best_role[1]['win_rate']}% win rate)")
    print(f"❌ Worst Role: {worst_role[0]} ({worst_role[1]['win_rate']}% win rate)")

# Advanced champion analysis by role
print("\n=== Champion Performance by Role ===")

# Get recent matches for detailed analysis
recent_matches = player.get_recent_matches(count=50, queue=QueueId.RANKED_SOLO_5x5)

role_champion_stats = {}

for match in recent_matches:
    # Find this player's participant data
    player_participant = None
    for participant in match.info.participants:
        if participant.puuid == player.puuid:
            player_participant = participant
            break

    if not player_participant:
        continue

    role = player_participant.team_position.value if player_participant.team_position else "UNKNOWN"
    champion = player_participant.champion_name

    if role not in role_champion_stats:
        role_champion_stats[role] = {}

    if champion not in role_champion_stats[role]:
        role_champion_stats[role][champion] = {
            "games": 0,
            "wins": 0,
            "total_kills": 0,
            "total_deaths": 0,
            "total_assists": 0,
        }

    stats = role_champion_stats[role][champion]
    stats["games"] += 1
    stats["total_kills"] += player_participant.kills
    stats["total_deaths"] += player_participant.deaths
    stats["total_assists"] += player_participant.assists

    if player_participant.win:
        stats["wins"] += 1

# Display top champions per role
for role, champions in role_champion_stats.items():
    if not champions:
        continue

    print(f"\n{role} Champions:")

    # Sort champions by games played, then by win rate
    sorted_champions = sorted(
        champions.items(),
        key=lambda x: (x[1]["games"], x[1]["wins"] / max(x[1]["games"], 1)),
        reverse=True,
    )

    for champion, stats in sorted_champions[:TOP_CHAMPIONS_PER_ROLE]:  # Top N champions per role
        if stats["games"] < MIN_GAMES_PER_CHAMPION:  # Only show champions with at least N games
            continue

        win_rate = (stats["wins"] / stats["games"]) * 100
        avg_kda = (stats["total_kills"] + stats["total_assists"]) / max(
            stats["total_deaths"],
            1,
        )

        print(
            f"  {champion}: {stats['games']} games, {win_rate:.1f}% WR, {avg_kda:.2f} KDA",
        )

# Performance trends analysis
print("\n=== Recent Performance Trends ===")

# Analyze last TOTAL_RECENT games in chunks of CHUNK_SIZE to see trends
for i in range(0, TOTAL_RECENT, CHUNK_SIZE):
    chunk_matches = (
        player.get_recent_matches(count=CHUNK_SIZE, queue=QueueId.RANKED_SOLO_5x5)[i : i + CHUNK_SIZE] if i == 0 else []
    )

    if i > 0:  # Skip chunks after first since get_recent_matches always gets most recent
        break

    if not chunk_matches:
        continue

    wins = 0
    total_kda = 0

    for match in chunk_matches:
        player_participant = None
        for participant in match.info.participants:
            if participant.puuid == player.puuid:
                player_participant = participant
                break

        if player_participant:
            if player_participant.win:
                wins += 1

            kda = (player_participant.kills + player_participant.assists) / max(
                player_participant.deaths,
                1,
            )
            total_kda += kda

    games_count = len(chunk_matches)
    win_rate = (wins / games_count) * 100 if games_count > 0 else 0
    avg_kda = total_kda / games_count if games_count > 0 else 0

    print(f"Last {CHUNK_SIZE} games: {win_rate:.1f}% WR, {avg_kda:.2f} avg KDA")

print("\n=== Analysis Complete ===")
print("Tips for improvement based on role performance:")
if best_role[0]:
    print(f"- Focus on playing {best_role[0]} (your best role)")
if worst_role[0] and worst_role[0] != best_role[0]:
    print(f"- Consider avoiding {worst_role[0]} or practice it more")
print("- Play your most successful champions in ranked")
print("- Track performance trends to identify improvement or decline")
