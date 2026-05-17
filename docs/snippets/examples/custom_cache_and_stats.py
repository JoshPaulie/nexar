import asyncio
import os

from nexar.cache import CacheConfig, NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=CacheConfig(
        enabled=True,
        cache_name="my_custom_cache",
        backend="memory",
        expire_after=600,
        timeout=60,
    ),
)


async def main() -> None:
    async with client:
        player = await client.get_player(riot_id="bexli#bex", region=Region.NA1)

        # Inspect cache state
        cache_info = await client.get_cache_info()
        print(f"Backend:       {cache_info['backend']}")
        print(f"Cache name:    {cache_info['cache_name']}")
        print(f"Default TTL:   {cache_info['default_expire_after']}s")
        print(f"Cached items:  {cache_info['cached_responses']}")

        # API call stats
        stats = client.get_api_call_stats()
        print(f"Total calls:   {stats.total_calls}")
        print(f"Cache hits:    {stats.cache_hits}")
        print(f"Fresh calls:   {stats.fresh_calls}")
        print(f"Retries:       {stats.retries}")
        print(f"Errors:        {stats.errors}")

        client.print_api_call_summary()

        # Clear the cache
        await client.clear_cache()

        # Disable caching entirely
        no_cache_client = NexarClient(
            riot_api_key=os.getenv("RIOT_API_KEY", ""),
            cache_config=NO_CACHE_CONFIG,
        )


if __name__ == "__main__":
    asyncio.run(main())
