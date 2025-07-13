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


async def main() -> None:
    async with client:
        # --8<-- [start:demo]
        from nexar.utils import sort_players_by_rank

        # Get players
        riot_ids = [
            "bexli#bex",
            "mltsimpleton#na1",
            "roninalex#na1",
            "poydok#na1",
            "boxrog#na1",
            "vynle#na1",
        ]

        print(f"Fetching {len(riot_ids)} players...\n")

        # Fetch all players in parallel
        players = await client.get_players(riot_ids)

        # Players sorted by rank
        sorted_players = await sort_players_by_rank(players)

        # Print them!
        for player in sorted_players:
            solo_rank = await player.get_solo_rank()
            rank_text = (
                f"{solo_rank.tier} {solo_rank.division:<3} ({solo_rank.league_points} LP)"
                if solo_rank  # Handle unranked
                else "Unranked!"
            )
            print(f"{player.game_name:<12} :: {rank_text}")
        # --8<-- [end:demo]


if __name__ == "__main__":
    asyncio.run(main())
