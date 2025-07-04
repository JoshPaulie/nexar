#!/usr/bin/env python3
"""Example demonstrating the high-level Player API."""

import os

from nexar import NexarClient, QueueId, RegionV4, RegionV5


def main():
    """Demonstrate Player functionality."""
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
            print(f"{i}. {result} - {player_participant.champion_name} ({kda})")

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


if __name__ == "__main__":
    main()
