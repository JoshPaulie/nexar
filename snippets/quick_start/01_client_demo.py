# --8<-- [start:declaration]
from nexar.client import NexarClient

client = NexarClient(
    riot_api_key="your_api_key",
)
# --8<-- [end:declaration]

# --8<-- [start:declaration-default-region]
from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key="your_api_key",
    default_region=Region.NA1,
)
# --8<-- [end:declaration-default-region]

# --8<-- [start:declaration-smart-cache]
from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient

client = NexarClient(
    riot_api_key="your_api_key",
    cache_config=SMART_CACHE_CONFIG,
)
# --8<-- [end:declaration-smart-cache]

# --8<-- [start:usage]
import asyncio

# .. client declaration from above


async def main() -> None:
    async with client:
        ...


if __name__ == "__main__":
    asyncio.run(main())

# --8<-- [end:usage]
