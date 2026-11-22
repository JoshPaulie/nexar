import asyncio
import os

from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    default_region=Region.NA1,
)


async def main() -> None:
    async with client:
        player = await client.get_player(riot_id="bexli#bex", region=Region.NA1)

        # All masteries, highest points first
        masteries = await player.get_champion_masteries()
        for mastery in masteries[:3]:
            # champion_name resolves offline; the id covers a champion newer than the snapshot
            name = mastery.champion_name or f"champion {mastery.champion_id}"
            print(f"Champion {name}: level {mastery.champion_level}, {mastery.champion_points:,} points")

        # Single-champion lookup (skipped when the account has no masteries yet)
        if masteries:
            favorite = await client.get_champion_mastery(player.puuid, masteries[0].champion_id)
            print(f"Chest earned on favorite: {favorite.chest_granted}")

        # Total mastery score across all champions
        score = await client.get_champion_mastery_score(player.puuid)
        print(f"Total mastery score: {score:,}")


if __name__ == "__main__":
    asyncio.run(main())
