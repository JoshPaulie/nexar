"""Example demonstrating the debug response feature."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5


async def demonstrate_debug_responses():
    """Demonstrate the debug response feature."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Enable debug output to see API responses
    os.environ["NEXAR_DEBUG_RESPONSES"] = "1"

    # Create async client
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as client:
        print("Debug responses are enabled. You'll see detailed output for each API call.")
        print("=" * 80)
        # Get a riot account - this will show the debug output
        print("1. Getting riot account...")
        riot_account = await client.get_riot_account("bexli", "bex")
        print(f"   Result: {riot_account.game_name}#{riot_account.tag_line}")
        print()

        # Get summoner info - this will show another debug output
        print("2. Getting summoner info...")
        summoner = await client.get_summoner_by_puuid(riot_account.puuid)
        print(f"   Result: Level {summoner.summoner_level} summoner")
        print()

        # Get match IDs with parameters - this will show params in debug output
        print("3. Getting match IDs with parameters...")
        match_ids = await client.get_match_ids_by_puuid(
            riot_account.puuid,
            count=5,  # This parameter will be shown in debug output
        )
        print(f"   Result: Found {len(match_ids)} match IDs")
        print()

        print("=" * 80)
        print("All API responses above showed detailed debug information!")
        print("To disable this output, unset the NEXAR_DEBUG_RESPONSES environment variable.")


if __name__ == "__main__":
    import asyncio

    asyncio.run(demonstrate_debug_responses())
