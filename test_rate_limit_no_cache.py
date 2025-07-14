import asyncio
import logging
import os
import time

from nexar.cache import CacheConfig
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.exceptions import RateLimitError
from nexar.logging import configure_logging

configure_logging(logging.INFO)

mem_cache = CacheConfig(backend="memory")

client = NexarClient(
    os.getenv("RIOT_API_KEY"),  # type: ignore[arg-type]
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=None,
)


async def main() -> None:
    async with client:
        count = 0
        try:
            for _ in range(110):
                start_time = time.perf_counter()
                await client.get_player("bexli", "bex")
                await client.clear_cache()
                # print(f"Retreive from cache took: {time.perf_counter() - start_time}s")
                count += 1
        except RateLimitError:
            print(f":( {count}")


if __name__ == "__main__":
    asyncio.run(main())
