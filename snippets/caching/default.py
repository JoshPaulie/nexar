import asyncio

from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key="your_api_key",
    default_region=Region.NA1,
)


async def main() -> None:
    async with client:
        # First call hits the API
        player = await client.get_player("bexli", "bex")

        # Second call uses cached data
        player = await client.get_player("bexli", "bex")


if __name__ == "__main__":
    asyncio.run(main())
