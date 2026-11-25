# --8<-- [start:declaration]
from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key="your_api_key",
    default_region=Region.NA1,
)
# --8<-- [end:declaration]

# --8<-- [start:usage]
import asyncio
import os

from nexar.client import NexarClient
from nexar.enums import Region


async def main() -> None:
    async with NexarClient(
        riot_api_key=os.environ["RIOT_API_KEY"],
        default_region=Region.NA1,
    ) as client:
        print("Ready to make API calls!")
        # ... do work here ...


if __name__ == "__main__":
    asyncio.run(main())
# --8<-- [end:usage]
