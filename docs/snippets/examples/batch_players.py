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
    """Example of batch player retrieval using get_players method."""
    async with client:
        # List of riot IDs to fetch
        riot_ids = [
            "bexli#bex",
            "mltsimpleton#na1",
        ]

        print(f"Fetching {len(riot_ids)} players...")

        # Fetch all players in parallel
        players = await client.get_players(riot_ids)

        print(f"Successfully retrieved {len(players)} players!\n")


# --8<-- [end:demo]


async def other_region_demo() -> None:
    riot_ids: list[str] = []  # Imagine this is populated with Korean players

    # --8<-- [start:regions]
    async with client:
        players = await client.get_players(
            riot_ids,
            v4_region=RegionV4.KR,
            v5_region=RegionV5.ASIA,
        )
    # --8<-- [end:regions]


if __name__ == "__main__":
    asyncio.run(main())
