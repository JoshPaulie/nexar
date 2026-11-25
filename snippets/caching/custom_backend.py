import asyncio
import os
from nexar.client import NexarClient
from nexar.cache import CacheConfig
from nexar.enums import Region


async def main() -> None:
    api_key = os.environ.get("RIOT_API_KEY")
    if not api_key:
        print("Please set RIOT_API_KEY environment variable.")
        return

    # 1. Custom SQLite Configuration
    # Useful for separating dev/prod caches or specific tool caches
    sqlite_config = CacheConfig(
        backend="sqlite",
        cache_name="my_custom_cache",  # Creates my_custom_cache.sqlite
        expire_after=3600,  # 1 hour default expiration
    )

    print("--- Using Custom SQLite Backend ---")
    async with NexarClient(riot_api_key=api_key, cache_config=sqlite_config) as client:
        # Note: Using get_player which returns a Player object with both account and summoner data
        player = await client.get_player(riot_id="Agurin#EUW", region=Region.EUW1)
        print(f"Got player (SQLite): {player.game_name}#{player.tag_line}")

    # 2. Memory Configuration
    # Useful for tests, scripts, or read-only environments (Lambda/Cloud Run)
    memory_config = CacheConfig(
        backend="memory",
        expire_after=600,  # 10 minutes default
    )

    print("\n--- Using Memory Backend ---")
    async with NexarClient(riot_api_key=api_key, cache_config=memory_config) as client:
        player = await client.get_player(riot_id="Agurin#EUW", region=Region.EUW1)
        print(f"Got player (Memory): {player.game_name}#{player.tag_line}")


if __name__ == "__main__":
    asyncio.run(main())
