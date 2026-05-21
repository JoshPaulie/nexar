import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.exceptions import BatchError

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        riot_ids = [
            "bexli#bex",
            "nonexistent#user",       # Will fail with NotFoundError
            "mltsimpleton#na1",
            "alsobad#user",           # Will fail with NotFoundError
        ]

        try:
            players = await client.get_players(riot_ids)
        except BatchError as exc:
            print(f"{len(exc.successful_results)} players fetched successfully")
            print(f"{len(exc.errors)} errors occurred\n")

            for idx_key, error in exc.errors:
                idx = int(idx_key.replace("item[", "").replace("]", ""))
                print(f"  [{idx}] {riot_ids[idx]}: {type(error).__name__}: {error}")

            # successful_results contains the players that were fetched
            for player in exc.successful_results:
                print(f"  {player} -> {player.puuid}")


if __name__ == "__main__":
    asyncio.run(main())
