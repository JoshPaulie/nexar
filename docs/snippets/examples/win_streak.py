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

        # Check if on a 3-game win streak (default min_games=3)
        on_streak = await player.is_on_win_streak()
        print(f"On a 3+ win streak? {on_streak}")

        # Check for a longer streak
        on_5_streak = await player.is_on_win_streak(min_games=5)
        print(f"On a 5+ win streak? {on_5_streak}")


if __name__ == "__main__":
    asyncio.run(main())
