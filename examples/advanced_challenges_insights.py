"""Advanced challenges analysis showing detailed performance insights."""

import os
import sys

from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

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
print(f"Advanced Performance Analysis for: {account.game_name}#{account.tag_line}\n")

# Get recent matches for comprehensive analysis
match_ids = client.get_match_ids_by_puuid(puuid, count=10)

if not match_ids:
    print("No recent matches found.")
    sys.exit(1)

print(f"Analyzing {len(match_ids)} recent matches for advanced insights...\n")

# Collect data for aggregated analysis
performance_data = {
    "matches_analyzed": 0,
    "wins": 0,
    "epic_monster_performance": {
        "baron_takedowns": 0,
        "dragon_takedowns": 0,
        "herald_takedowns": 0,
        "elder_dragon_kills": 0,
    },
    "vision_mastery": {
        "avg_vision_score_per_min": 0,
        "control_wards_placed": 0,
        "wards_destroyed": 0,
        "stealth_wards_placed": 0,
    },
    "combat_excellence": {
        "multikills": 0,
        "solo_kills": 0,
        "perfect_games": 0,
        "flawless_aces": 0,
        "killing_sprees": 0,
    },
    "macro_play": {
        "first_turret_kills": 0,
        "turret_plates_taken": 0,
        "teleport_takedowns": 0,
        "jungle_monsters_stolen": 0,
    },
    "consistency_metrics": {
        "avg_kda": 0,
        "avg_kill_participation": 0,
        "avg_damage_per_minute": 0,
        "avg_gold_per_minute": 0,
    },
    "special_achievements": {
        "twelve_assist_streaks": 0,
        "survived_single_digit_hp": 0,
        "outnumbered_kills": 0,
        "lane_opponent_advantages": 0,
    },
}

for match_id in match_ids:
    match = client.get_match(match_id)

    # Find player's participant
    player_participant = None
    for participant in match.info.participants:
        if participant.puuid == puuid:
            player_participant = participant
            break

    if not player_participant or not player_participant.challenges:
        continue

    performance_data["matches_analyzed"] += 1
    c = player_participant.challenges

    # Track wins
    if player_participant.win:
        performance_data["wins"] += 1

    # Epic monster performance
    epic = performance_data["epic_monster_performance"]
    if c.baron_takedowns:
        epic["baron_takedowns"] += c.baron_takedowns
    if c.dragon_takedowns:
        epic["dragon_takedowns"] += c.dragon_takedowns
    if c.rift_herald_takedowns:
        epic["herald_takedowns"] += c.rift_herald_takedowns
    if c.elder_dragon_multikills:
        epic["elder_dragon_kills"] += c.elder_dragon_multikills

    # Vision mastery
    vision = performance_data["vision_mastery"]
    if c.vision_score_per_minute:
        vision["avg_vision_score_per_min"] += c.vision_score_per_minute
    if c.control_wards_placed:
        vision["control_wards_placed"] += c.control_wards_placed
    if c.ward_takedowns:
        vision["wards_destroyed"] += c.ward_takedowns
    if c.stealth_wards_placed:
        vision["stealth_wards_placed"] += c.stealth_wards_placed

    # Combat excellence
    combat = performance_data["combat_excellence"]
    if c.multikills:
        combat["multikills"] += c.multikills
    if c.solo_kills:
        combat["solo_kills"] += c.solo_kills
    if c.perfect_game:
        combat["perfect_games"] += c.perfect_game
    if c.flawless_aces:
        combat["flawless_aces"] += c.flawless_aces
    if c.killing_sprees:
        combat["killing_sprees"] += c.killing_sprees

    # Macro play
    macro = performance_data["macro_play"]
    if c.first_turret_killed:
        macro["first_turret_kills"] += c.first_turret_killed
    if c.turret_plates_taken:
        macro["turret_plates_taken"] += c.turret_plates_taken
    if c.teleport_takedowns:
        macro["teleport_takedowns"] += c.teleport_takedowns
    if c.enemy_jungle_monster_kills:
        macro["jungle_monsters_stolen"] += c.enemy_jungle_monster_kills

    # Consistency metrics
    consistency = performance_data["consistency_metrics"]
    if c.kda:
        consistency["avg_kda"] += c.kda
    if c.kill_participation:
        consistency["avg_kill_participation"] += c.kill_participation
    if c.damage_per_minute:
        consistency["avg_damage_per_minute"] += c.damage_per_minute
    if c.gold_per_minute:
        consistency["avg_gold_per_minute"] += c.gold_per_minute

    # Special achievements
    special = performance_data["special_achievements"]
    if c.twelve_assist_streak_count:
        special["twelve_assist_streaks"] += c.twelve_assist_streak_count
    if c.survived_single_digit_hp_count:
        special["survived_single_digit_hp"] += c.survived_single_digit_hp_count
    if c.outnumbered_kills:
        special["outnumbered_kills"] += c.outnumbered_kills
    if c.max_level_lead_lane_opponent and c.max_level_lead_lane_opponent > 1:
        special["lane_opponent_advantages"] += 1

# Generate comprehensive report
matches_count = performance_data["matches_analyzed"]
if matches_count == 0:
    print("No matches with challenges data found.")
    sys.exit(1)

print("=== COMPREHENSIVE PERFORMANCE REPORT ===")
print(f"Matches Analyzed: {matches_count}")
print(
    f"Win Rate: {performance_data['wins']}/{matches_count} ({performance_data['wins'] / matches_count:.1%})"
)
print()

print("🏆 EPIC MONSTER MASTERY")
epic = performance_data["epic_monster_performance"]
print(
    f"  Baron Takedowns: {epic['baron_takedowns']} (avg: {epic['baron_takedowns'] / matches_count:.1f}/game)"
)
print(
    f"  Dragon Takedowns: {epic['dragon_takedowns']} (avg: {epic['dragon_takedowns'] / matches_count:.1f}/game)"
)
print(
    f"  Herald Takedowns: {epic['herald_takedowns']} (avg: {epic['herald_takedowns'] / matches_count:.1f}/game)"
)
print(f"  Elder Dragon Participation: {epic['elder_dragon_kills']} times")
print()

print("👁️ VISION MASTERY")
vision = performance_data["vision_mastery"]
print(
    f"  Average Vision Score/Min: {vision['avg_vision_score_per_min'] / matches_count:.1f}"
)
print(
    f"  Control Wards Placed: {vision['control_wards_placed']} (avg: {vision['control_wards_placed'] / matches_count:.1f}/game)"
)
print(
    f"  Wards Destroyed: {vision['wards_destroyed']} (avg: {vision['wards_destroyed'] / matches_count:.1f}/game)"
)
print(
    f"  Stealth Wards Placed: {vision['stealth_wards_placed']} (avg: {vision['stealth_wards_placed'] / matches_count:.1f}/game)"
)
print()

print("⚔️ COMBAT EXCELLENCE")
combat = performance_data["combat_excellence"]
print(f"  Total Multikills: {combat['multikills']}")
print(f"  Total Solo Kills: {combat['solo_kills']}")
print(f"  Perfect Games: {combat['perfect_games']}")
print(f"  Flawless Aces: {combat['flawless_aces']}")
print(f"  Killing Sprees: {combat['killing_sprees']}")
print()

print("🗺️ MACRO PLAY")
macro = performance_data["macro_play"]
print(f"  First Turret Kills: {macro['first_turret_kills']}")
print(
    f"  Turret Plates Taken: {macro['turret_plates_taken']} (avg: {macro['turret_plates_taken'] / matches_count:.1f}/game)"
)
print(f"  Teleport-Assisted Takedowns: {macro['teleport_takedowns']}")
print(
    f"  Enemy Jungle Monsters: {macro['jungle_monsters_stolen']:.0f} (avg: {macro['jungle_monsters_stolen'] / matches_count:.1f}/game)"
)
print()

print("📊 CONSISTENCY METRICS")
consistency = performance_data["consistency_metrics"]
print(f"  Average KDA: {consistency['avg_kda'] / matches_count:.2f}")
print(
    f"  Average Kill Participation: {consistency['avg_kill_participation'] / matches_count:.1%}"
)
print(
    f"  Average Damage/Min: {consistency['avg_damage_per_minute'] / matches_count:.0f}"
)
print(f"  Average Gold/Min: {consistency['avg_gold_per_minute'] / matches_count:.0f}")
print()

print("⭐ SPECIAL ACHIEVEMENTS")
special = performance_data["special_achievements"]
print(f"  12+ Assist Streaks: {special['twelve_assist_streaks']}")
print(f"  Survived Single-Digit HP: {special['survived_single_digit_hp']}")
print(f"  Outnumbered Kills: {special['outnumbered_kills']}")
print(
    f"  Games with Lane Advantage: {special['lane_opponent_advantages']}/{matches_count}"
)
print()

# Performance rating
total_score = 0
max_score = 0

# Win rate component (0-25 points)
win_rate = performance_data["wins"] / matches_count
total_score += win_rate * 25
max_score += 25

# KDA component (0-20 points)
avg_kda = consistency["avg_kda"] / matches_count
kda_score = min(avg_kda / 3.0 * 20, 20)  # Cap at 20 for KDA of 3.0+
total_score += kda_score
max_score += 20

# Kill participation (0-15 points)
avg_kp = consistency["avg_kill_participation"] / matches_count
kp_score = avg_kp * 15
total_score += kp_score
max_score += 15

# Vision score (0-15 points)
avg_vision = vision["avg_vision_score_per_min"] / matches_count
vision_score = min(avg_vision / 2.0 * 15, 15)  # Cap at 15 for 2.0+ vision/min
total_score += vision_score
max_score += 15

# Epic monster participation (0-15 points)
epic_total = (
    epic["baron_takedowns"] + epic["dragon_takedowns"] + epic["herald_takedowns"]
)
epic_score = min(
    epic_total / matches_count / 2.0 * 15, 15
)  # Cap at 15 for 2+ epic/game
total_score += epic_score
max_score += 15

# Special achievements bonus (0-10 points)
special_total = (
    combat["multikills"]
    + combat["solo_kills"]
    + combat["perfect_games"] * 3
    + combat["flawless_aces"] * 2
)
special_score = min(special_total / matches_count * 10, 10)
total_score += special_score
max_score += 10

performance_rating = (total_score / max_score) * 100

print("📈 OVERALL PERFORMANCE RATING")
print(f"  Score: {total_score:.1f}/{max_score} ({performance_rating:.1f}%)")

if performance_rating >= 90:
    rating_text = "🏆 LEGENDARY"
elif performance_rating >= 80:
    rating_text = "💎 DIAMOND"
elif performance_rating >= 70:
    rating_text = "🥇 GOLD"
elif performance_rating >= 60:
    rating_text = "🥈 SILVER"
else:
    rating_text = "🥉 BRONZE"

print(f"  Rating: {rating_text}")
print()
print("This analysis leverages the rich challenges data to provide insights")
print("beyond traditional stats, focusing on macro play, vision control,")
print("objective participation, and clutch moments.")
