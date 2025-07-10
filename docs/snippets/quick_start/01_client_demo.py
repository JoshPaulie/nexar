# --8<-- [start:declaration]
from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

client = NexarClient(
    riot_api_key="your_api_key",
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)
# --8<-- [end:declaration]

# --8<-- [start:usage]
import asyncio


async def main() -> None:
    async with client:
        ...


if __name__ == "__main__":
    asyncio.run(main())

# --8<-- [end:usage]
