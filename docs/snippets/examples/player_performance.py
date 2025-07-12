"""Demonstrate player performance statistics for a player's recent matches."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if api_key is None:
    sys.exit("Please set RIOT_API_KEY environment variable")

client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)


# --8<-- [start:demo]
async def main() -> None:
    """Example of player performance statistics."""
    async with client:
        # Get player
        player = await client.get_player("bexli", "bex")

        # Get recent performance stats
        performance = await player.get_recent_performance(count=20)

        print(f"Performance over {performance.total_games} recent games:")
        print(f"Win Rate: {performance.win_rate:.1f}% ({performance.wins}W/{performance.losses}L)")

        kda_str = f"{performance.avg_kills:.1f}/{performance.avg_deaths:.1f}/{performance.avg_assists:.1f}"
        print(f"Average KDA: {kda_str} ({performance.avg_kda:.2f})")
        print(f"Average CS: {performance.avg_cs:.1f}")
        print(f"Average Game Duration: {performance.avg_game_duration_minutes:.1f} minutes")


# --8<-- [end:demo]


if __name__ == "__main__":
    asyncio.run(main())
