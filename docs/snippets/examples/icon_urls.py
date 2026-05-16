import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        player = await client.get_player(game_name="bexli", tag_line="bex", region=Region.NA1)

        # Summoner profile icon URL
        summoner = await player.get_summoner()
        print(f"Profile icon: {summoner.profile_icon_url}")

        # Champion icon URL from a recent match
        last_match = await player.get_last_match()
        assert last_match
        participant = last_match.participants.by_puuid(player.puuid)
        assert participant
        print(f"{participant.champion_name} icon: {participant.champion_icon_url}")


if __name__ == "__main__":
    asyncio.run(main())
