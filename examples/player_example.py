#!/usr/bin/env python3
"""Example demonstrating the high-level Player API."""

import os
import sys

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

# Get recent matches (reduced from 20 to 10 to save API calls)
print("\n--- Recent Matches ---")
recent_matches = player.get_last_20(queue=QueueId.RANKED_SOLO_5x5)
for i, match in enumerate(recent_matches[:5], 1):
    # Find this player's participant
    player_participant = None
    for participant in match.info.participants:
        if participant.puuid == player.puuid:
            player_participant = participant
            break

    if player_participant:
        result = "WIN" if player_participant.win else "LOSS"
        kda = f"{player_participant.kills}/{player_participant.deaths}/{player_participant.assists}"
        
        # Add challenges insights
        challenges_info = ""
        if player_participant.challenges:
            c = player_participant.challenges
            insights = []
            if c.kda is not None:
                insights.append(f"KDA: {c.kda:.1f}")
            if c.kill_participation is not None:
                insights.append(f"KP: {c.kill_participation:.0%}")
            if c.damage_per_minute is not None:
                insights.append(f"DPM: {c.damage_per_minute:.0f}")
            if insights:
                challenges_info = f" | {' | '.join(insights)}"
        
        print(f"{i}. {result} - {player_participant.champion_name} ({kda}){challenges_info}")

# Get champion statistics (reduced from 50 to 20 games to save API calls)
print("\n--- Top Champions (Last 20 games) ---")
top_champions = player.get_top_champions(top_n=3, count=20)
for i, champ_stats in enumerate(top_champions, 1):
    print(f"{i}. {champ_stats.champion_name}")
    print(f"   Games: {champ_stats.games_played} ({champ_stats.win_rate:.1f}% WR)")
    print(
        f"   Avg KDA: {champ_stats.avg_kda:.1f} ({champ_stats.avg_kills:.1f}/{champ_stats.avg_deaths:.1f}/{champ_stats.avg_assists:.1f})"
    )

# Get all champion stats (reduced from 100 to 20 games to save API calls)
print("\n--- All Champions (Last 20 games) ---")
all_stats = player.get_champion_stats(count=20)
print(f"Total unique champions played: {len(all_stats)}")

# Example of analyzing challenges across multiple matches
print("\n--- Performance Analysis (Last 5 matches) ---")
performance_metrics = {
    "total_matches": 0,
    "avg_kda": 0,
    "avg_kill_participation": 0,
    "avg_damage_per_minute": 0,
    "avg_vision_score_per_minute": 0,
    "multikills_total": 0,
    "solo_kills_total": 0,
}

valid_matches = 0
for match in recent_matches[:5]:
    for participant in match.info.participants:
        if participant.puuid == player.puuid and participant.challenges:
            c = participant.challenges
            performance_metrics["total_matches"] += 1
            valid_matches += 1
            
            if c.kda is not None:
                performance_metrics["avg_kda"] += c.kda
            if c.kill_participation is not None:
                performance_metrics["avg_kill_participation"] += c.kill_participation
            if c.damage_per_minute is not None:
                performance_metrics["avg_damage_per_minute"] += c.damage_per_minute
            if c.vision_score_per_minute is not None:
                performance_metrics["avg_vision_score_per_minute"] += c.vision_score_per_minute
            if c.multikills is not None:
                performance_metrics["multikills_total"] += c.multikills
            if c.solo_kills is not None:
                performance_metrics["solo_kills_total"] += c.solo_kills
            break

if valid_matches > 0:
    print(f"Average KDA: {performance_metrics['avg_kda'] / valid_matches:.2f}")
    print(f"Average Kill Participation: {performance_metrics['avg_kill_participation'] / valid_matches:.1%}")
    print(f"Average Damage Per Minute: {performance_metrics['avg_damage_per_minute'] / valid_matches:.0f}")
    print(f"Average Vision Score Per Minute: {performance_metrics['avg_vision_score_per_minute'] / valid_matches:.1f}")
    print(f"Total Multikills: {performance_metrics['multikills_total']}")
    print(f"Total Solo Kills: {performance_metrics['solo_kills_total']}")
else:
    print("No matches with challenges data found.")
