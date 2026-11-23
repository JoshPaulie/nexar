import asyncio
import os

from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    default_region=Region.NA1,
)


async def main() -> None:
    async with client:
        player = await client.get_player(riot_id="bexli#bex")


if __name__ == "__main__":
    asyncio.run(main())
