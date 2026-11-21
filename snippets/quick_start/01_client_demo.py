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
from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient

client = NexarClient(
    riot_api_key="your_api_key",
    cache_config=DEFAULT_CACHE_CONFIG,
)
# --8<-- [end:declaration-smart-cache]

# --8<-- [start:usage]
import asyncio
import os

# .. client declaration from above


async def main() -> None:
    # Use environment variable for API key in actual code
    real_key = os.environ.get("RIOT_API_KEY", "your_api_key")

    # Re-instantiate with real key for the demo to run
    async with NexarClient(riot_api_key=real_key, default_region=Region.NA1) as client:
        print("Ready to make API calls!")
        # ... do work here ...


if __name__ == "__main__":
    asyncio.run(main())

# --8<-- [end:usage]
