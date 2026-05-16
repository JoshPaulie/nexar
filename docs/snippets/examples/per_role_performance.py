import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region, Queue

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        player = await client.get_player(game_name="bexli", tag_line="bex", region=Region.NA1)

        # Get per-role performance across recent solo queue matches
        role_perf = await player.get_recent_performance_by_role(
            count=30,
            queue=Queue.SOLO_QUEUE,
        )

        for role, stats in role_perf.items():
            kda = (stats["kills"] + stats["assists"]) / stats["deaths"] if stats["deaths"] > 0 else 0.0
            print(f"{role}:")
            print(f"  Games:  {stats['games']}")
            print(f"  Winrate:{stats['win_rate']:.0%}")
            print(f"  KDA:    {stats['avg_kills']:.1f}/{stats['avg_deaths']:.1f}/{stats['avg_assists']:.1f} ({kda:.2f})")
            print()


if __name__ == "__main__":
    asyncio.run(main())
