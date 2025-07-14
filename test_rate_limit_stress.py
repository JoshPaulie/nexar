import asyncio
import os
import sys
from pathlib import Path

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.logging import configure_logging

configure_logging()

cache_file = Path("nexar_cache.sqlite")
if cache_file.exists():
    "Deleting existing cache for testing."
    cache_file.unlink()


async def main() -> None:
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    )

    async with client:
        players = await client.get_players(["bexli#bex", "mltsimpleton#na1", "roninalex#na1", "REborn503#na1"])

        for player in players:
            print(f"== {player.game_name} ==\n")
            matches = await player.get_matches()
            champ_history = matches.get_champion_stats()

            for champ in champ_history:
                print(champ.champion_name)
            print()


if __name__ == "__main__":
    asyncio.run(main())
