"""Basic example showing champion statistics and performance summary."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import QueueId, RegionV4, RegionV5


async def main() -> None:
    """Demonstrate performance analysis for a player."""
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
        # Create player object
        player = await client.get_player("bexli", "bex")
        print(f"Analyzing performance for {player}")

        # Get performance summary from last 20 games
        print("\n=== Performance Summary (Last 20 Games) ===")
        performance = await player.get_recent_performance(count=20)

        print(f"Total Games: {performance['total_games']}")
        print(f"Win Rate: {performance['win_rate']:.1f}% ({performance['wins']}W/{performance['losses']}L)")
        print(
            f"Average KDA: {performance['avg_kills']:.1f}/{performance['avg_deaths']:.1f}/"
            f"{performance['avg_assists']:.1f} ({performance['avg_kda']:.2f})",
        )

        # Get champion statistics from last 10 games
        print("\n=== Champion Statistics (Last 10 Games) ===")
        champion_stats = await player.get_champion_stats(count=10)

        if champion_stats:
            print(f"Champions played: {len(champion_stats)}")
            print("\nTop 5 most played champions:")
            # Sort by games played
            sorted_champions = sorted(champion_stats, key=lambda x: x.games_played, reverse=True)
            for i, champ in enumerate(sorted_champions[:5], 1):
                print(f"{i}. {champ.champion_name}")
                print(f"   Games: {champ.games_played} | Win Rate: {champ.win_rate:.1f}%")
                print(
                    f"   Avg KDA: {champ.avg_kills:.1f}/{champ.avg_deaths:.1f}/"
                    f"{champ.avg_assists:.1f} ({champ.avg_kda:.2f})",
                )

        # Get ranked performance summary
        print("\n=== Ranked Solo Queue Performance (Last 10 Games) ===")
        ranked_performance = await player.get_recent_performance(count=10, queue=QueueId.RANKED_SOLO_5x5)

        if ranked_performance["total_games"] > 0:
            print(f"Ranked Games: {ranked_performance['total_games']}")
            print(f"Ranked Win Rate: {ranked_performance['win_rate']:.1f}%")
            print(f"Ranked Avg KDA: {ranked_performance['avg_kda']:.2f}")
        else:
            print("No recent ranked games found")


if __name__ == "__main__":
    asyncio.run(main())
