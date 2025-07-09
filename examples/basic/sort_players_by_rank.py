"""Example showing how to sort players by solo queue rank using async sort function."""

import asyncio
import os
import sys

from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.utils import sort_players_by_rank


async def main() -> None:
    """Demonstrate sorting players by solo queue rank."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create async client
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    ) as client:
        # Example player names and tags (replace with real ones as needed)
        players_info = [
            ("bexli", "bex"),
            ("roninalex", "na1"),
            ("MltSimpleton", "na1"),
        ]

        # Create list of Player objects
        players = []
        for name, tag in players_info:
            player = await client.get_player(name, tag)
            players.append(player)

        # Sort list of players by solo queue rank (highest first)
        sorted_players = await sort_players_by_rank(players)

        print("Players sorted by solo queue rank (highest to lowest):")
        for player in sorted_players:
            rank = await player.get_solo_rank()
            if rank:
                print(f"{player.game_name}: {rank.tier.value.title()} {rank.rank.value}")
            else:
                print(f"{player.game_name}: Unranked")

        # To sort by flex queue rank instead, use:
        # from nexar.enums import Queue
        # sorted_players = await sort_players_by_rank(players, queue_type=Queue.RANKED_FLEX_SR)


if __name__ == "__main__":
    asyncio.run(main())
