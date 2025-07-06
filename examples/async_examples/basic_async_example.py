"""Async example for the Nexar SDK."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5


async def main() -> None:
    """Demonstrate async functionality."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create async client
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as client:
        # Get basic player info
        account = await client.get_riot_account("bexli", "bex")
        print(f"Account: {account.game_name}#{account.tag_line} (PUUID: {account.puuid})")

        summoner = await client.get_summoner_by_puuid(account.puuid)
        print(f"Summoner: Level {summoner.summoner_level} (PUUID: {summoner.puuid})")

        # Get recent match IDs
        match_ids = await client.get_match_ids_by_puuid(account.puuid, count=5)
        print(f"Recent matches: {match_ids[:3]}")

        # Demonstrate concurrent API calls
        print("\nFetching match details concurrently...")

        async def fetch_match_info(match_id: str) -> str:
            match = await client.get_match(match_id)
            duration_minutes = match.info.game_duration // 60
            return f"Match {match_id}: {duration_minutes}m duration"

        # Fetch multiple matches concurrently
        match_tasks = [fetch_match_info(match_id) for match_id in match_ids[:3]]
        match_results = await asyncio.gather(*match_tasks)

        for result in match_results:
            print(f"  {result}")

        # Use high-level player object
        print("\nUsing AsyncPlayer object...")
        player = client.get_player("bexli", "bex")

        performance = await player.get_recent_performance(count=5)
        print(f"Recent performance: {performance['wins']}/{performance['total_games']} wins")
        print(f"Win rate: {performance['win_rate']:.1f}%")
        print(f"Average KDA: {performance['avg_kda']:.2f}")

        # Get league entries
        league_entries = await client.get_league_entries_by_puuid(account.puuid)
        for entry in league_entries:
            print(f"Rank: {entry.tier} {entry.rank} ({entry.league_points} LP)")


if __name__ == "__main__":
    asyncio.run(main())
