"""Example demonstrating direct API usage for league entries."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.models.player import Player


async def main() -> None:
    """Demonstrate direct API usage for league entries."""
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
        print("=== League Entries API Example ===")

        # Get PUUID using the account lookup
        account = await client.get_riot_account("bexli", "bex")
        puuid = account.puuid
        print(f"Found account: {account.game_name}#{account.tag_line}")
        print(f"PUUID: {puuid}\n")

        # Get league entries using direct API call
        league_entries = await client.get_league_entries_by_puuid(puuid)

    if not league_entries:
        print("No ranked entries found for this player.")
    else:
        print(f"Found {len(league_entries)} league entries:\n")

        for i, entry in enumerate(league_entries, 1):
            print(f"{i}. {entry.queue_type.value}")
            print(f"   Rank: {entry.tier.value} {entry.rank.value}")
            print(f"   LP: {entry.league_points}")
            print(f"   Wins/Losses: {entry.wins}/{entry.losses}")
            print(f"   Win Rate: {entry.win_rate:.1f}%")

            if entry.mini_series:
                print(f"   In Promos: {entry.mini_series.progress}")
                print(f"   Promo Target: {entry.mini_series.target}")
                print(f"   Promo Wins: {entry.mini_series.wins}")
                print(f"   Promo Losses: {entry.mini_series.losses}")

            if entry.hot_streak:
                print("   🔥 HOT STREAK!")

            if entry.veteran:
                print("   🎖️ VETERAN")

            if entry.inactive:
                print("   💤 INACTIVE")

            if entry.fresh_blood:
                print("   🆕 FRESH BLOOD")

            print()

    # Compare with Player API usage
    print("=== Comparison: Using Player API ===")

    player = Player(client=client, game_name="bexli", tag_line="bex")

    print("Using Player API for the same data:")
    player_rank = await player.get_rank()
    player_flex_rank = await player.get_flex_rank()
    print(f"Solo Queue Rank: {player_rank.tier.value if player_rank else 'Unranked'}")
    print(f"Flex Queue Rank: {player_flex_rank.tier.value if player_flex_rank else 'Unranked'}")

    print("\n=== API Usage Notes ===")
    print("Direct API:")
    print("- Use await client.get_league_entries_by_puuid(puuid)")
    print("- Returns list of all league entries")
    print("- Requires manual PUUID lookup")
    print("- Full control over data processing")
    print()
    print("Player API:")
    print("- Use await player.get_rank() or await player.get_flex_rank()")
    print("- Automatically filters to specific queue types")
    print("- Handles PUUID lookup automatically")
    print("- Simpler for common use cases")
    print()
    print(
        "Recommendation: Use Player API unless you need all queue types or custom processing",
    )


if __name__ == "__main__":
    asyncio.run(main())
