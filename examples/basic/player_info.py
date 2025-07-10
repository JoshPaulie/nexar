"""Basic example showing how to get player information using the Player API."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5


async def main() -> None:
    """Demonstrate basic player information retrieval."""
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
        # Create a player object (riot account fetched immediately)
        player = await client.get_player("bexli", "bex")
        print(f"Analyzing player: {player}")

        # Access basic player info (riot account already available)
        riot_account = player.riot_account  # No await needed!
        summoner = await player.get_summoner()
        league_entries = await player.get_league_entries()

        print(f"Summoner Level: {summoner.summoner_level}")
        print(f"PUUID: {riot_account.puuid}")

        # Find Solo Queue rank using the async helper methods
        solo_queue_entry = await player.get_solo_rank()
        flex_queue_entry = await player.get_flex_rank()

        # Check Solo Queue rank
        if solo_queue_entry:
            print(
                f"Solo Queue Rank: {solo_queue_entry.tier.value} {solo_queue_entry.division.value} "
                f"({solo_queue_entry.league_points} LP)",
            )
            total_games = solo_queue_entry.wins + solo_queue_entry.losses
            win_rate = (solo_queue_entry.wins / total_games) * 100 if total_games > 0 else 0
            print(f"Win Rate: {win_rate:.1f}% ({solo_queue_entry.wins}W/{solo_queue_entry.losses}L)")
            if solo_queue_entry.mini_series:
                print(f"In Promos: {solo_queue_entry.mini_series.progress}")
        else:
            print("Solo Queue Rank: Unranked")

        # Check Flex Queue rank
        if flex_queue_entry:
            print(
                f"Flex Queue Rank: {flex_queue_entry.tier.value} {flex_queue_entry.division.value} "
                f"({flex_queue_entry.league_points} LP)",
            )
        else:
            print("Flex Queue Rank: Unranked")

        # Show all league entries
        print("\nAll League Entries:")
        for entry in league_entries:
            print(f"  {entry.queue_type.value}: {entry.tier.value} {entry.division.value}")


if __name__ == "__main__":
    asyncio.run(main())
