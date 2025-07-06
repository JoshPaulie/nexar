"""Demonstrate get_players method for efficient batch player retrieval."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5


async def main() -> None:
    """Demonstrate batch player retrieval using get_players method."""
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
        # List of riot IDs to fetch
        riot_ids = [
            "bexli#bex",
            "mltsimpleton#na1",
        ]

        print(f"Fetching {len(riot_ids)} players efficiently using get_players()...")

        # Fetch all players in parallel
        players = await client.get_players(riot_ids)

        print(f"Successfully retrieved {len(players)} players!\n")

        # Display basic info for each player
        for i, player in enumerate(players, 1):
            print(f"=== Player {i}: {player} ===")

            # Get summoner info (riot account was pre-fetched during get_players)
            summoner = await player.get_summoner()
            print(f"Level: {summoner.summoner_level}")

            # Get rank info
            rank = await player.get_rank()
            if rank:
                print(f"Solo Queue: {rank.tier.value} {rank.rank.value} ({rank.league_points} LP)")
                win_rate = (rank.wins / (rank.wins + rank.losses)) * 100 if (rank.wins + rank.losses) > 0 else 0
                print(f"Win Rate: {win_rate:.1f}% ({rank.wins}W/{rank.losses}L)")
            else:
                print("Solo Queue: Unranked")

            # Get recent performance
            performance = await player.get_recent_performance(count=5)
            print(f"Recent 5 games: {performance['win_rate']:.1f}% WR, {performance['avg_kda']:.2f} KDA")
            print()


if __name__ == "__main__":
    asyncio.run(main())
