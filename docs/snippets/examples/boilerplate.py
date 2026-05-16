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
        player = await client.get_player(
            game_name="bexli",
            tag_line="bex",
            region=Region.NA1,
        )


if __name__ == "__main__":
    asyncio.run(main())
