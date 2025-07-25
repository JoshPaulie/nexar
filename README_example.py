"""Example from README showing async player information retrieval."""

import asyncio
import os
import sys
from datetime import UTC, datetime

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5


async def main() -> None:
    """Demonstrate player information retrieval using the async API."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create async client
    client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    )

    async with client:
        # Get player information
        player = await client.get_player("bexli", "bex")

        print()
        riot_account = player.riot_account  # Immediately available!
        summoner = await player.get_summoner()
        rank = await player.get_solo_rank()

        print(f"Summoner: {riot_account.game_name}")
        print(f"Level: {summoner.summoner_level}")

        if rank:
            print(f"Solo Queue rank: {rank.tier} {rank.division}\n")

        # Get and display recent matches
        recent_matches = await player.get_matches(count=5)
        print(f"Recent Match History ({len(recent_matches)} matches):\n")

        for match in recent_matches:
            # Get participant stats of particular summoner
            participant = match.participants.by_puuid(player.puuid)

            result = "Victory!" if participant.win else "Defeat."
            kda = participant.kda(as_str=True)
            kda_ratio = f"{participant.challenges.kda:.2f}"

            days_ago = (datetime.now(tz=UTC) - match.info.game_start_timestamp).days
            days_ago_str = f"{days_ago} {'day' if days_ago == 1 else 'days'} ago"

            print(
                f"{days_ago_str:<10} "
                f"{result:<9} "
                f"{participant.champion_name:<8} "
                f"{participant.team_position.value.title():<6} "
                f"{kda} ({kda_ratio})",
            )


if __name__ == "__main__":
    asyncio.run(main())
