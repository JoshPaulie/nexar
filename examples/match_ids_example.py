"""Example usage of the get_match_ids_by_puuid method."""

import os
import sys
from datetime import datetime, timedelta

from nexar.client import NexarClient
from nexar.enums import MatchType, QueueId, RegionV4, RegionV5

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if api_key is None:
    sys.exit("No RIOT_API_KEY environment variable found")

# Initialize the client
client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
)

# Get PUUID from a riot account (using test account as example)
account = client.get_riot_account("bexli", "bex")
puuid = account.puuid
print(f"Found account: {account.game_name}#{account.tag_line} (PUUID: {puuid[:5]}..)\n")

# Basic usage - get the last 20 match IDs
match_ids = client.get_match_ids_by_puuid(puuid)
print(f"Last 20 match IDs: {match_ids}\n")

# Get ranked solo/duo matches only
ranked_matches = client.get_match_ids_by_puuid(
    puuid, queue=QueueId.RANKED_SOLO_5x5, match_type=MatchType.RANKED, count=10
)
print(f"Last 10 ranked solo/duo matches: {ranked_matches}\n")

# Get matches from a specific time period
one_week_ago = datetime.today() - timedelta(days=7)
recent_matches = client.get_match_ids_by_puuid(puuid, start_time=one_week_ago, count=50)
print(f"Matches from the last week: {recent_matches}\n")

# Get ARAM matches using raw queue ID
aram_matches = client.get_match_ids_by_puuid(
    puuid,
    queue=450,  # ARAM queue ID
    match_type="normal",
)
print(f"ARAM matches: {aram_matches}\n")

# Pagination example - get matches 21-40
next_page = client.get_match_ids_by_puuid(puuid, start=20, count=20)
print(f"All matches, 21-40: {next_page}\n")

# Example: Get detailed match data with challenges
print("=== Detailed Match Analysis ===")
if ranked_matches:
    latest_match_id = ranked_matches[0]
    print(f"Analyzing match: {latest_match_id}")

    match = client.get_match(latest_match_id)

    # Find player's participant
    player_participant = None
    for participant in match.info.participants:
        if participant.puuid == puuid:
            player_participant = participant
            break

    if player_participant:
        result = "WIN" if player_participant.win else "LOSS"
        print(f"Result: {result} - {player_participant.champion_name}")
        print(
            f"KDA: {player_participant.kills}/{player_participant.deaths}/{player_participant.assists}"
        )

        # Show challenges data highlights
        challenges = player_participant.challenges
        if challenges:
            print("\nKey Performance Metrics:")
            if challenges.kda is not None:
                print(f"  KDA Ratio: {challenges.kda:.2f}")
            if challenges.kill_participation is not None:
                print(f"  Kill Participation: {challenges.kill_participation:.1%}")
            if challenges.damage_per_minute is not None:
                print(f"  Damage Per Minute: {challenges.damage_per_minute:.0f}")
            if challenges.vision_score_per_minute is not None:
                print(
                    f"  Vision Score Per Minute: {challenges.vision_score_per_minute:.1f}"
                )

"""
Example response:

Found account: bexli#bex (PUUID: 0wKS4..)

Last 20 match IDs: ['NA1_5316329415', 'NA1_5316316196', 'NA1_5316300873', ...]

Last 10 ranked solo/duo matches: ['NA1_5316329415', 'NA1_5316316196', 'NA1_5316300873', ...]

Matches from the last week: ['NA1_5316329415', 'NA1_5316316196', 'NA1_5316300873',  ...]

ARAM matches: ['NA1_5181786118', 'NA1_5136680640', 'NA1_4987837612', 'NA1_4987822377',  ...]

All matches, 21-40: ['NA1_5295223771', 'NA1_5294414398', 'NA1_5294398478',  ...]

=== Detailed Match Analysis ===
Analyzing match: NA1_5316329415
Result: WIN - Jinx
KDA: 12/2/8

Key Performance Metrics:
  KDA Ratio: 10.00
  Kill Participation: 0.87
  Damage Per Minute: 687
  Vision Score Per Minute: 1.2
"""
