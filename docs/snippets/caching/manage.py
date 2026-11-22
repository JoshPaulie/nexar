"""Example: inspecting and clearing the cache."""

import asyncio

from nexar.client import NexarClient


async def main() -> None:
    async with NexarClient(riot_api_key="your_api_key") as client:
        info = await client.get_cache_info()
        print(f"Cache: {info.backend}, {info.cached_responses} rows")

        await client.clear_cache()

        stats = client.get_api_call_stats()
        print(f"Calls: {stats.fresh_calls} fresh, {stats.cache_hits} cached")
        client.print_api_call_summary()


if __name__ == "__main__":
    asyncio.run(main())
