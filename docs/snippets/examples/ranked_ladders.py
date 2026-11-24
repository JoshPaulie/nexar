import asyncio
import os

from nexar.client import NexarClient
from nexar.enums import Queue, RankDivision, RankTier, Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
)


async def main() -> None:
    async with client:
        # Apex ladders arrive whole in one response, pre-sorted by LP.
        challenger = await client.get_challenger_league(Queue.RANKED_SOLO_5x5, Region.NA1)
        print(f"{challenger.tier} ({challenger.queue_raw}): {len(challenger.entries)} players")
        for item in challenger.entries[:5]:
            games = item.wins + item.losses
            win_rate = item.wins / games if games else 0.0
            print(f"  {item.league_points} LP - {item.wins}W/{item.losses}L ({win_rate:.0%})")

        # Division ladders paginate: each page holds 205 players (the wire does
        # not sort a page by LP; sort with rank_tuple if you need rank order).
        page_one = await client.get_league_entries(
            Queue.RANKED_SOLO_5x5,
            RankTier.GOLD,
            RankDivision.ONE,
            Region.NA1,
        )
        print(f"\nGold I, page 1: {len(page_one)} players")
        if page_one:
            first = page_one[0]
            print(f"  First row of the page: {first.league_points} LP, {first.total_games} games played")
        by_rank = sorted(page_one, reverse=True)
        print(f"  Highest LP on the page: {by_rank[0].league_points}")

        # Walk deeper with page, or use the expanded-league variant of the same ladder.
        page_two = await client.get_league_entries(
            Queue.RANKED_SOLO_5x5,
            RankTier.GOLD,
            RankDivision.ONE,
            Region.NA1,
            page=2,
        )
        exp_page_one = await client.get_league_exp_entries(
            Queue.RANKED_SOLO_5x5,
            RankTier.GOLD,
            RankDivision.ONE,
            Region.NA1,
        )
        print(f"Gold I, page 2: {len(page_two)} players; league-exp page 1: {len(exp_page_one)} players")


if __name__ == "__main__":
    asyncio.run(main())
