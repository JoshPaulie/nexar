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
        last_match = await player.get_last_match()
        assert last_match

        participant = last_match.participants.by_puuid(player.puuid)
        assert participant

        perks = participant.perks
        if not perks:
            print("No perk data available for this match.")
            return

        # Stat shards (defense, flex, offense)
        print(f"{participant.champion_name} stat shards:")
        print(f"  Offense: {perks.stat_perks.offense}")
        print(f"  Flex:    {perks.stat_perks.flex}")
        print(f"  Defense: {perks.stat_perks.defense}")

        # Rune pages (primary + secondary)
        print("\nRune pages:")
        for style in perks.styles:
            print(f"  {style.description} (style {style.style}):")
            for sel in style.selections:
                print(f"    Perk {sel.perk} (var1={sel.var1}, var2={sel.var2}, var3={sel.var3})")


if __name__ == "__main__":
    asyncio.run(main())
