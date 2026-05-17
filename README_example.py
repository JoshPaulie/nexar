"""Example from README showing async player information retrieval."""

import asyncio
import contextlib
import os
import sys
from datetime import UTC, datetime

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region


async def main() -> None:
    """Demonstrate player information retrieval using the async API."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create async client
    # Note: Using SQLite cache (default) persists API responses to disk while rate limits stay in-memory
    client = NexarClient(
        riot_api_key=api_key,
        default_region=Region.NA1,
        cache_config=DEFAULT_CACHE_CONFIG,
    )

    async with client:
        print("Fetching player info...")
        # Get player information
        player = await client.get_player(riot_id="bexli#bex")

        print()
        riot_account = player.riot_account  # Immediately available!
        summoner = await player.get_summoner()
        rank = await player.get_solo_rank()

        print(f"Summoner: {riot_account.game_name}#{riot_account.tag_line}")
        print(f"Level: {summoner.summoner_level}")

        if rank:
            print(f"Solo Queue rank: {rank.tier} {rank.division}\n")

        print("Fetching recent matches...")
        # Get and display recent matches
        recent_matches = await player.get_matches(count=5)
        print(f"Recent Match History ({len(recent_matches)} matches):\n")

        for match in recent_matches:
            # Get participant stats of particular summoner
            participant = match.participants.by_puuid(player.puuid)

            if not participant:
                continue

            result = "Victory!" if participant.win else "Defeat."
            kda = participant.kda(as_str=True)
            kda_ratio = f"{participant.kda():.2f}"

            # Calculate time ago
            game_start = match.info.game_start_timestamp
            # Ensure game_start is timezone-aware
            if game_start.tzinfo is None:
                game_start = game_start.replace(tzinfo=UTC)

            days_ago = (datetime.now(tz=UTC) - game_start).days

            if days_ago == 0:
                time_str = "Today"
            elif days_ago == 1:
                time_str = "Yesterday"
            else:
                time_str = f"{days_ago} days ago"

            print(
                f"{time_str:<12} "
                f"{result:<9} "
                f"{participant.champion_name:<10} "
                f"{participant.team_position.value.title():<8} "
                f"{kda} ({kda_ratio})",
            )


if __name__ == "__main__":
    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(main())
