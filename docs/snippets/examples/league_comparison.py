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
        # Fetch multiple players
        riot_ids = [
            "bexli#bex",
            "mltsimpleton#na1",
            "roninalex#na1",
        ]
        players = await client.get_players(riot_ids)

        # Gather all solo queue league entries
        league_entries = []
        for player in players:
            solo_rank = await player.get_solo_rank()
            if solo_rank:
                league_entries.append(solo_rank)

        # is_higher_rank_than: compare two entries
        if len(league_entries) >= 2:
            a, b = league_entries[0], league_entries[1]
            print(f"{a.tier} {a.division} ({a.league_points} LP) vs {b.tier} {b.division} ({b.league_points} LP)")
            print(f"First is higher? {a.is_higher_rank_than(b)}")

        # rank_tuple: (tier_division_score, LP) for custom sorting
        print("\nSorted by rank:")
        for entry in sorted(league_entries, reverse=True):
            print(f"  {entry.tier} {entry.division} ({entry.league_points} LP)  winrate: {entry.win_rate:.0%}")

        # get_solo_rank_value on a Player directly
        for player in players:
            rank_val = await player.get_solo_rank_value()
            if rank_val:
                tier_score, lp = rank_val
                print(f"  {player} -> tier_score={tier_score}, LP={lp}")
            else:
                print(f"  {player} -> unranked")


if __name__ == "__main__":
    asyncio.run(main())
