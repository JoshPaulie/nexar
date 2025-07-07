"""Example demonstrating match challenges analysis using the Player API."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import QueueId, RegionV4, RegionV5


async def main() -> None:
    """Demonstrate match challenges analysis using the Player API."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create async client
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as client:
        print("=== Match Challenges Analysis Example ===")

        # Create player object
        player = await client.get_player("bexli", "bex")
        riot_account = player.riot_account  # Immediately available!
        print(f"Analyzing challenges for {riot_account.game_name}")

        # Get recent ranked matches for challenges analysis
        print("\nGetting recent ranked matches for challenges analysis...")
        matches = await player.get_matches(count=5, queue=QueueId.RANKED_SOLO_5x5)

        if not matches:
            print("No recent ranked matches found.")
            return

        print(f"Found {len(matches)} recent ranked matches\n")

        # Analyze challenges across matches
        total_kda_values = []
        total_kill_participation = []
        total_damage_per_minute = []
        total_vision_score_per_minute = []

        print("=== Individual Match Challenges ===")

        for i, match in enumerate(matches, 1):
            # Find this player's participant data
            player_participant = None
            for participant in match.info.participants:
                if participant.puuid == riot_account.puuid:
                    player_participant = participant
                    break

            if not player_participant:
                continue

            challenges = player_participant.challenges
            if not challenges:
                print(f"Match {i}: No challenges data available")
                continue

            print(f"\nMatch {i} - {player_participant.champion_name}:")
            print(f"  Result: {'WIN' if player_participant.win else 'LOSS'}")
            print(f"  Duration: {match.info.game_duration // 60}m {match.info.game_duration % 60}s")

            # Core performance metrics
            if challenges.kda is not None:
                print(f"  KDA: {challenges.kda:.2f}")
                total_kda_values.append(challenges.kda)

            if challenges.kill_participation is not None:
                print(f"  Kill Participation: {challenges.kill_participation:.1%}")
                total_kill_participation.append(challenges.kill_participation)

            if challenges.damage_per_minute is not None:
                print(f"  Damage per Minute: {challenges.damage_per_minute:.0f}")
                total_damage_per_minute.append(challenges.damage_per_minute)

            if challenges.vision_score_per_minute is not None:
                print(f"  Vision Score per Minute: {challenges.vision_score_per_minute:.2f}")
                total_vision_score_per_minute.append(challenges.vision_score_per_minute)

            # Interesting specific challenges
            interesting_challenges = []

            if challenges.twelve_assist_streak_count and challenges.twelve_assist_streak_count > 0:
                interesting_challenges.append(f"12+ assist streaks: {challenges.twelve_assist_streak_count}")

            if challenges.earliest_baron and challenges.earliest_baron > 0:
                baron_time = challenges.earliest_baron // 60
                interesting_challenges.append(f"Early baron at {baron_time}m")

            if challenges.earliest_dragon_takedown and challenges.earliest_dragon_takedown > 0:
                dragon_time = challenges.earliest_dragon_takedown // 60
                interesting_challenges.append(f"Early dragon at {dragon_time}m")

            if challenges.perfect_game and challenges.perfect_game > 0:
                interesting_challenges.append("Perfect game!")

            if challenges.solo_kills and challenges.solo_kills > 0:
                interesting_challenges.append(f"Solo kills: {challenges.solo_kills}")

            if interesting_challenges:
                print(f"  Notable: {', '.join(interesting_challenges)}")

    # Calculate averages
    print(f"\n=== Average Performance Across {len(matches)} Matches ===")

    if total_kda_values:
        avg_kda = sum(total_kda_values) / len(total_kda_values)
        print(f"Average KDA: {avg_kda:.2f}")

    if total_kill_participation:
        avg_kp = sum(total_kill_participation) / len(total_kill_participation)
        print(f"Average Kill Participation: {avg_kp:.1%}")

    if total_damage_per_minute:
        avg_dpm = sum(total_damage_per_minute) / len(total_damage_per_minute)
        print(f"Average Damage per Minute: {avg_dpm:.0f}")

    if total_vision_score_per_minute:
        avg_vspm = sum(total_vision_score_per_minute) / len(total_vision_score_per_minute)
        print(f"Average Vision Score per Minute: {avg_vspm:.2f}")

    # Find best and worst performances
    if total_kda_values:
        best_kda = max(total_kda_values)
        worst_kda = min(total_kda_values)
        print(f"\nKDA Range: {worst_kda:.2f} - {best_kda:.2f}")

    if total_kill_participation:
        best_kp = max(total_kill_participation)
        worst_kp = min(total_kill_participation)
        print(f"Kill Participation Range: {worst_kp:.1%} - {best_kp:.1%}")

    # Advanced challenges analysis
    print("\n=== Advanced Challenges Summary ===")

    # Count occurrences of special achievements
    special_achievements = {
        "Perfect Games": 0,
        "Solo Kills": 0,
        "Early Barons": 0,
        "Early Dragons": 0,
        "12+ Assist Streaks": 0,
    }

    for match in matches:
        for participant in match.info.participants:
            if participant.puuid == riot_account.puuid and participant.challenges:
                challenges = participant.challenges

                if challenges.perfect_game and challenges.perfect_game > 0:
                    special_achievements["Perfect Games"] += challenges.perfect_game

                if challenges.solo_kills and challenges.solo_kills > 0:
                    special_achievements["Solo Kills"] += challenges.solo_kills

                if challenges.earliest_baron and challenges.earliest_baron > 0:
                    special_achievements["Early Barons"] += 1

                if challenges.earliest_dragon_takedown and challenges.earliest_dragon_takedown > 0:
                    special_achievements["Early Dragons"] += 1

                if challenges.twelve_assist_streak_count and challenges.twelve_assist_streak_count > 0:
                    special_achievements["12+ Assist Streaks"] += challenges.twelve_assist_streak_count

    for achievement, count in special_achievements.items():
        if count > 0:
            print(f"{achievement}: {count}")

    print("\n=== Challenges Analysis Complete ===")
    print("Challenges data provides detailed performance metrics beyond basic KDA.")
    print("Use this data to identify strengths and areas for improvement:")
    print("- High kill participation shows good teamfight presence")
    print("- High damage per minute indicates strong damage output")
    print("- High vision score shows good map awareness")
    print("- Special achievements highlight exceptional plays")


if __name__ == "__main__":
    asyncio.run(main())
