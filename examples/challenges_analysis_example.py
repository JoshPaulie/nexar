"""Example demonstrating analysis of match challenges data."""

import os
import sys

from nexar.client import NexarClient
from nexar.enums import QueueId, RegionV4, RegionV5

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
print(f"Analyzing challenges for: {account.game_name}#{account.tag_line}\n")

# Get recent ranked match IDs
match_ids = client.get_match_ids_by_puuid(
    puuid, queue=QueueId.RANKED_SOLO_5x5, count=5
)

if not match_ids:
    print("No recent ranked matches found.")
    sys.exit(1)

print(f"Analyzing {len(match_ids)} recent ranked matches...\n")

for i, match_id in enumerate(match_ids, 1):
    print(f"=== Match {i}: {match_id} ===")
    
    # Get match details
    match = client.get_match(match_id)
    
    # Find the player's participant data
    player_participant = None
    for participant in match.info.participants:
        if participant.puuid == puuid:
            player_participant = participant
            break
    
    if not player_participant:
        print("Player not found in this match")
        continue
    
    # Basic match info
    result = "WIN" if player_participant.win else "LOSS"
    kda = f"{player_participant.kills}/{player_participant.deaths}/{player_participant.assists}"
    print(f"Result: {result} - {player_participant.champion_name} ({kda})")
    print(f"Duration: {match.info.game_duration // 60}m {match.info.game_duration % 60}s")
    
    # Challenges analysis
    challenges = player_participant.challenges
    if challenges:
        print("\n--- Key Performance Metrics ---")
        
        # Core stats
        if challenges.kda is not None:
            print(f"KDA Ratio: {challenges.kda:.2f}")
        if challenges.kill_participation is not None:
            print(f"Kill Participation: {challenges.kill_participation:.1%}")
        if challenges.damage_per_minute is not None:
            print(f"Damage Per Minute: {challenges.damage_per_minute:.0f}")
        if challenges.gold_per_minute is not None:
            print(f"Gold Per Minute: {challenges.gold_per_minute:.0f}")
        if challenges.vision_score_per_minute is not None:
            print(f"Vision Score Per Minute: {challenges.vision_score_per_minute:.1f}")
        
        print("\n--- Notable Achievements ---")
        
        # Epic monster performance
        epic_achievements = []
        if challenges.baron_takedowns and challenges.baron_takedowns > 0:
            epic_achievements.append(f"Baron kills: {challenges.baron_takedowns}")
        if challenges.dragon_takedowns and challenges.dragon_takedowns > 0:
            epic_achievements.append(f"Dragon kills: {challenges.dragon_takedowns}")
        if challenges.rift_herald_takedowns and challenges.rift_herald_takedowns > 0:
            epic_achievements.append(f"Herald kills: {challenges.rift_herald_takedowns}")
        
        if epic_achievements:
            print("Epic Monsters: " + ", ".join(epic_achievements))
        
        # Special achievements
        special_achievements = []
        if challenges.solo_kills and challenges.solo_kills > 0:
            special_achievements.append(f"Solo kills: {challenges.solo_kills}")
        if challenges.multikills and challenges.multikills > 0:
            special_achievements.append(f"Multikills: {challenges.multikills}")
        if challenges.perfect_game and challenges.perfect_game > 0:
            special_achievements.append("Perfect game!")
        if challenges.flawless_aces and challenges.flawless_aces > 0:
            special_achievements.append(f"Flawless aces: {challenges.flawless_aces}")
        
        if special_achievements:
            print("Special: " + ", ".join(special_achievements))
        
        # Vision and map control
        vision_achievements = []
        if challenges.control_wards_placed and challenges.control_wards_placed > 0:
            vision_achievements.append(f"Control wards: {challenges.control_wards_placed}")
        if challenges.stealth_wards_placed and challenges.stealth_wards_placed > 0:
            vision_achievements.append(f"Stealth wards: {challenges.stealth_wards_placed}")
        if challenges.ward_takedowns and challenges.ward_takedowns > 0:
            vision_achievements.append(f"Wards destroyed: {challenges.ward_takedowns}")
        
        if vision_achievements:
            print("Vision: " + ", ".join(vision_achievements))
        
        # Early game performance
        early_game = []
        if challenges.takedowns_first_25_minutes and challenges.takedowns_first_25_minutes > 0:
            early_game.append(f"Takedowns <25min: {challenges.takedowns_first_25_minutes}")
        if challenges.first_turret_killed and challenges.first_turret_killed > 0:
            early_game.append("First turret!")
        if challenges.lane_minions_first_10_minutes and challenges.lane_minions_first_10_minutes > 0:
            early_game.append(f"CS @10min: {challenges.lane_minions_first_10_minutes}")
        
        if early_game:
            print("Early Game: " + ", ".join(early_game))
        
        # Team fight performance
        if challenges.team_damage_percentage is not None:
            print(f"Team Damage Share: {challenges.team_damage_percentage:.1%}")
        if challenges.damage_taken_on_team_percentage is not None:
            print(f"Team Damage Taken: {challenges.damage_taken_on_team_percentage:.1%}")
    
    else:
        print("No challenges data available for this match")
    
    print()  # Empty line between matches

print("Analysis complete!")
print("\nNote: Challenges data provides detailed performance metrics beyond basic KDA.")
print("This includes vision control, objective participation, early game impact, and much more.")
