"""Demonstrate get_players method for efficient batch player retrieval."""

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
    """Example of champion performance method."""
    async with client:
        # Get player
        player = await client.get_player("bexli", "bex")

        champ_performance = await player.get_champion_stats()
        for champ in champ_performance:
            print(champ.champion_name)
            print(f"{champ.wins} wins / {champ.losses} losses ({champ.win_rate:.2g}%)")
            kda = f"{champ.avg_kills:.2g}/{champ.avg_deaths:.2g}/{champ.avg_assists:.2g}"
            print(f"Average KDA: {kda} ({champ.avg_kda:.2g})\n")


# --8<-- [end:demo]


if __name__ == "__main__":
    asyncio.run(main())
