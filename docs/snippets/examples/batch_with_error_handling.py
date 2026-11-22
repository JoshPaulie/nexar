import asyncio
import os

from nexar.client import NexarClient
from nexar.enums import Region
from nexar.exceptions import BatchError

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    default_region=Region.NA1,
)


async def main() -> None:
    async with client:
        riot_ids = [
            "bexli#bex",
            "nonexistent#user",  # Will fail with NotFoundError
            "mltsimpleton#na1",
            "alsobad#user",  # Will fail with NotFoundError
        ]

        try:
            players = await client.get_players(riot_ids)
        except BatchError as exc:
            print(f"{len(exc.successful_results)} players fetched successfully")
            print(f"{len(exc.errors)} errors occurred\n")

            # errors are labeled by the Riot ID that was passed in
            for riot_id, error in exc.errors:
                print(f"  {riot_id}: {type(error).__name__}: {error}")

            # successful_results contains the players that were fetched
            for player in exc.successful_results:
                print(f"  {player} -> {player.puuid}")


if __name__ == "__main__":
    asyncio.run(main())
