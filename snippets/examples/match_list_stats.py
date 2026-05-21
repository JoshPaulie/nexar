import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        player = await client.get_player(riot_id="bexli#bex", region=Region.NA1)
        matches = await player.get_matches(count=20)

        # Average any stat across matches with a lambda
        avg_kda = matches.get_average_stat(lambda p: (p.kills + p.assists) / max(p.deaths, 1))
        print(f"Avg KDA: {avg_kda:.2f}")

        avg_cs = matches.get_average_stat(lambda p: p.creep_score)
        print(f"Avg CS:  {avg_cs:.1f}")

        avg_vision = matches.get_average_stat(lambda p: p.vision_score)
        print(f"Avg Vision Score: {avg_vision:.1f}")

        avg_gold_per_min = matches.get_average_stat(lambda p: p.challenges.gold_per_minute)
        print(f"Avg Gold/min: {avg_gold_per_min:.1f}")


if __name__ == "__main__":
    asyncio.run(main())
