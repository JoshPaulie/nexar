import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5, Queue

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


async def main() -> None:
    async with client:
        # --8<-- [start:demo]
        import datetime as dt

        # Get player
        player = await client.get_player("bexli", "bex")

        # Get last 20 matches
        matches = await player.get_matches()

        # Get last 5 solo queue matches
        matches = await player.get_matches(count=5, queue=Queue.SOLO_QUEUE)

        # Get last week's matches
        past_week = dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=7)
        past_week_matches = await player.get_matches(start_time=past_week)

        # Get last match
        last_match = await player.get_last_match()
        # --8<-- [end:demo]


if __name__ == "__main__":
    asyncio.run(main())
