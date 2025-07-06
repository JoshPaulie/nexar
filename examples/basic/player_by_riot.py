"""Demonstrate Player.by_riot_id() usage."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.models import Player

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


async def main() -> None:
    """Demonstrate Player.by_riot_id() usage."""
    # Use async context manager to properly handle client lifecycle
    async with client:
        # Create a player using the convenient by_riot_id() method
        # This accepts the standard "username#tagline" format
        player = Player.by_riot_id(client, "bexli#bex")

        print(f"Player: {player}")

        # Get basic player information
        summoner = await player.get_summoner()
        print(f"Summoner level: {summoner.summoner_level}")

        # Get rank information
        rank = await player.get_rank()
        if rank:
            print(f"Solo queue rank: {rank.tier} {rank.rank} ({rank.league_points} LP)")
        else:
            print("Player is unranked in solo queue")

        # Get recent performance
        performance = await player.get_recent_performance(count=10)
        print("Recent performance (last 10 games):")
        print(f"  Win rate: {performance['win_rate']:.1f}%")
        print(f"  Average KDA: {performance['avg_kda']:.2f}")

        # You can also specify custom regions when creating the player
        print("\n=== Creating EU player ===")
        eu_player = Player.by_riot_id(
            client,
            "Thebausffs#COOL",
            v4_region=RegionV4.EUW1,
            v5_region=RegionV5.EUROPE,
        )
        print(f"EU Player created: {eu_player}")

        print("Getting EU player summoner info...")
        eu_summoner = await eu_player.get_summoner()
        print(f"EU Player summoner level: {eu_summoner.summoner_level}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
