"""Example showing team performance analysis using challenges data."""

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
print(f"Team Performance Analysis for: {account.game_name}#{account.tag_line}\n")

# Get recent ranked match for team analysis
match_ids = client.get_match_ids_by_puuid(
    puuid, queue=QueueId.RANKED_SOLO_5x5, count=3
)

if not match_ids:
    print("No recent ranked matches found.")
    sys.exit(1)

for match_num, match_id in enumerate(match_ids, 1):
    print(f"=== MATCH {match_num}: {match_id} ===")
    
    match = client.get_match(match_id)
    
    # Determine which team the player was on
    player_team_id = None
    for participant in match.info.participants:
        if participant.puuid == puuid:
            player_team_id = participant.team_id
            break
    
    if player_team_id is None:
        print("Player not found in this match")
        continue
    
    # Analyze team performance using challenges data
    team_stats = {
        "total_kills": 0,
        "total_deaths": 0,
        "total_assists": 0,
        "total_damage": 0,
        "total_gold": 0,
        "vision_score": 0,
        "epic_monsters": {
            "baron": 0,
            "dragon": 0,
            "herald": 0,
        },
        "objectives": {
            "turret_plates": 0,
            "turrets": 0,
            "control_wards": 0,
        },
        "team_fight_performance": {
            "multikills": 0,
            "perfect_games": 0,
            "team_damage_share": [],
            "damage_taken_share": [],
        }
    }
    
    enemy_stats = {
        "total_kills": 0,
        "total_deaths": 0,
        "epic_monsters": {"baron": 0, "dragon": 0, "herald": 0},
    }
    
    print(f"Match Duration: {match.info.game_duration // 60}m {match.info.game_duration % 60}s")
    print(f"Result: {'WIN' if any(p.win for p in match.info.participants if p.team_id == player_team_id) else 'LOSS'}")
    print()
    
    # Collect team data
    team_participants = []
    enemy_participants = []
    
    for participant in match.info.participants:
        if participant.team_id == player_team_id:
            team_participants.append(participant)
            # Basic stats
            team_stats["total_kills"] += participant.kills
            team_stats["total_deaths"] += participant.deaths
            team_stats["total_assists"] += participant.assists
            
            # Challenges-based analysis
            if participant.challenges:
                c = participant.challenges
                
                if c.damage_per_minute and match.info.game_duration > 0:
                    team_stats["total_damage"] += c.damage_per_minute * (match.info.game_duration / 60)
                if c.gold_per_minute and match.info.game_duration > 0:
                    team_stats["total_gold"] += c.gold_per_minute * (match.info.game_duration / 60)
                if c.vision_score_per_minute and match.info.game_duration > 0:
                    team_stats["vision_score"] += c.vision_score_per_minute * (match.info.game_duration / 60)
                
                # Epic monsters
                if c.baron_takedowns:
                    team_stats["epic_monsters"]["baron"] += c.baron_takedowns
                if c.dragon_takedowns:
                    team_stats["epic_monsters"]["dragon"] += c.dragon_takedowns
                if c.rift_herald_takedowns:
                    team_stats["epic_monsters"]["herald"] += c.rift_herald_takedowns
                
                # Objectives
                if c.turret_plates_taken:
                    team_stats["objectives"]["turret_plates"] += c.turret_plates_taken
                if c.turret_takedowns:
                    team_stats["objectives"]["turrets"] += c.turret_takedowns
                if c.control_wards_placed:
                    team_stats["objectives"]["control_wards"] += c.control_wards_placed
                
                # Team fight performance
                if c.multikills:
                    team_stats["team_fight_performance"]["multikills"] += c.multikills
                if c.perfect_game:
                    team_stats["team_fight_performance"]["perfect_games"] += c.perfect_game
                if c.team_damage_percentage is not None:
                    team_stats["team_fight_performance"]["team_damage_share"].append(c.team_damage_percentage)
                if c.damage_taken_on_team_percentage is not None:
                    team_stats["team_fight_performance"]["damage_taken_share"].append(c.damage_taken_on_team_percentage)
        else:
            enemy_participants.append(participant)
            enemy_stats["total_kills"] += participant.kills
            enemy_stats["total_deaths"] += participant.deaths
            
            if participant.challenges:
                c = participant.challenges
                if c.baron_takedowns:
                    enemy_stats["epic_monsters"]["baron"] += c.baron_takedowns
                if c.dragon_takedowns:
                    enemy_stats["epic_monsters"]["dragon"] += c.dragon_takedowns
                if c.rift_herald_takedowns:
                    enemy_stats["epic_monsters"]["herald"] += c.rift_herald_takedowns
    
    print("🎯 TEAM PERFORMANCE BREAKDOWN")
    print(f"  Team KDA: {team_stats['total_kills']}/{team_stats['total_deaths']}/{team_stats['total_assists']}")
    if team_stats['total_deaths'] > 0:
        team_kda = (team_stats['total_kills'] + team_stats['total_assists']) / team_stats['total_deaths']
        print(f"  Team KDA Ratio: {team_kda:.2f}")
    
    print(f"  Total Team Damage: {team_stats['total_damage']:.0f}")
    print(f"  Total Team Gold: {team_stats['total_gold']:.0f}")
    print(f"  Total Vision Score: {team_stats['vision_score']:.0f}")
    
    print("\n🏆 OBJECTIVE CONTROL")
    epic = team_stats["epic_monsters"]
    enemy_epic = enemy_stats["epic_monsters"]
    print(f"  Baron Control: {epic['baron']} vs {enemy_epic['baron']} (enemy)")
    print(f"  Dragon Control: {epic['dragon']} vs {enemy_epic['dragon']} (enemy)")
    print(f"  Herald Control: {epic['herald']} vs {enemy_epic['herald']} (enemy)")
    
    obj = team_stats["objectives"]
    print(f"  Turret Plates: {obj['turret_plates']}")
    print(f"  Turret Takedowns: {obj['turrets']}")
    print(f"  Control Wards: {obj['control_wards']}")
    
    print("\n⚔️ TEAM FIGHT ANALYSIS")
    tf = team_stats["team_fight_performance"]
    print(f"  Total Multikills: {tf['multikills']}")
    print(f"  Perfect Performances: {tf['perfect_games']}")
    
    if tf["team_damage_share"]:
        damage_distribution = tf["team_damage_share"]
        print(f"  Damage Distribution Balance: {max(damage_distribution) - min(damage_distribution):.1%} spread")
        most_damage = max(damage_distribution)
        print(f"  Highest Damage Contributor: {most_damage:.1%}")
    
    if tf["damage_taken_share"]:
        tank_distribution = tf["damage_taken_share"]
        print(f"  Tank Distribution Balance: {max(tank_distribution) - min(tank_distribution):.1%} spread")
        most_tanked = max(tank_distribution)
        print(f"  Primary Tank: {most_tanked:.1%} of team damage taken")
    
    print("\n👥 INDIVIDUAL HIGHLIGHTS")
    # Find standout performers using challenges data
    for participant in team_participants:
        highlights = []
        if participant.challenges:
            c = participant.challenges
            
            # High impact plays
            if c.solo_kills and c.solo_kills > 1:
                highlights.append(f"{c.solo_kills} solo kills")
            if c.multikills and c.multikills > 1:
                highlights.append(f"{c.multikills} multikills")
            if c.perfect_game and c.perfect_game > 0:
                highlights.append("perfect game")
            if c.baron_takedowns and c.baron_takedowns > 1:
                highlights.append(f"{c.baron_takedowns} barons")
            
            # Vision contributions
            if c.vision_score_per_minute and c.vision_score_per_minute > 2.5:
                highlights.append(f"excellent vision ({c.vision_score_per_minute:.1f}/min)")
            if c.control_wards_placed and c.control_wards_placed > 5:
                highlights.append(f"{c.control_wards_placed} control wards")
            
            # Special achievements
            if c.first_turret_killed:
                highlights.append("first turret")
            if c.killing_sprees and c.killing_sprees > 1:
                highlights.append(f"{c.killing_sprees} killing sprees")
        
        player_marker = " 🎮" if participant.puuid == puuid else ""
        if highlights:
            print(f"  {participant.champion_name}{player_marker}: {', '.join(highlights)}")
        else:
            kda = f"{participant.kills}/{participant.deaths}/{participant.assists}"
            print(f"  {participant.champion_name}{player_marker}: {kda}")
    
    print("-" * 60)
    print()

print("Analysis complete!")
print("\nThis team analysis leverages challenges data to provide insights into:")
print("- Objective control and map presence")
print("- Team fight coordination and damage distribution")
print("- Individual impact and special achievements")
print("- Vision control and macro play effectiveness")
