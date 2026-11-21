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
        player = await client.get_player(riot_id="bexli#bex", region=Region.NA1)
        last_match = await player.get_last_match()
        assert last_match

        for team in last_match.info.teams:
            side = "Blue" if team.team_id == 100 else "Red"
            print(f"--- {side} Side ---")

            # Bans
            if team.bans:
                print("  Bans:")
                for ban in team.bans:
                    print(f"    Champion {ban.champion_id} (pick turn {ban.pick_turn})")

            # Objectives
            if team.objectives:
                obj = team.objectives
                print("  Objectives:")
                print(f"    Baron:       {'first!' if obj.baron.first else ''} {obj.baron.kills} kills")
                print(f"    Dragon:      {'first!' if obj.dragon.first else ''} {obj.dragon.kills} kills")
                print(f"    Rift Herald: {'first!' if obj.rift_herald.first else ''} {obj.rift_herald.kills} kills")
                print(f"    Tower:       {'first!' if obj.tower.first else ''} {obj.tower.kills} kills")
                print(f"    Inhibitor:   {'first!' if obj.inhibitor.first else ''} {obj.inhibitor.kills} kills")
                print(f"    Champion:    {'first!' if obj.champion.first else ''} {obj.champion.kills} kills")
            print()


if __name__ == "__main__":
    asyncio.run(main())
