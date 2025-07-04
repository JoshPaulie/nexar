#!/usr/bin/env python3
"""Simple demo showing the Player API without making too many requests."""

import os

from nexar import NexarClient, RegionV4, RegionV5


def main():
    """Simple Player API demo."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        print("Please set RIOT_API_KEY environment variable")
        return

    # Create client
    client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )

    print("=== Nexar Player API Demo ===")

    # Create a player object (abstracts away riot id lookup)
    print("Creating player object...")
    player = client.get_player("bexli", "bex")
    print(f"Player: {player}")

    # Access basic info (cached after first access)
    print(f"PUUID: {player.puuid}")
    print(f"Summoner Level: {player.summoner.summoner_level}")

    # Check ranks
    print("\n--- Rank Information ---")
    if player.rank:
        rank = player.rank
        print(
            f"Solo Queue: {rank.tier.value} {rank.rank.value} ({rank.league_points} LP)"
        )
        print(f"Solo Queue WR: {rank.win_rate:.1f}% ({rank.wins}W/{rank.losses}L)")
    else:
        print("Solo Queue: Unranked")

    if player.flex_rank:
        flex = player.flex_rank
        print(
            f"Flex Queue: {flex.tier.value} {flex.rank.value} ({flex.league_points} LP)"
        )
    else:
        print("Flex Queue: Unranked")

    print("\nDemo completed successfully!")
    print("\nThe Player class provides these additional methods:")
    print("- player.get_last_20() - Get last 20 matches")
    print("- player.get_recent_matches(count=50, queue=QueueId.RANKED_SOLO_5x5)")
    print("- player.get_top_champions(top_n=5) - Get most played champions")
    print("- player.get_champion_stats() - Get detailed champion statistics")
    print("- player.get_performance_summary() - Get performance overview")
    print("- player.is_on_win_streak() - Check for win streaks")
    print("- player.get_recent_performance_by_role() - Stats by role")
    print("- player.refresh_cache() - Clear cached data")


if __name__ == "__main__":
    main()
