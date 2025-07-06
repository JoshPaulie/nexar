"""Test basic async functionality after the sync-to-async conversion."""

import asyncio
import os
import sys

from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5


async def main() -> None:
    """Test basic async functionality."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create client
    client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
    )

    try:
        print("Testing async client functionality...")

        # Test get_riot_account
        print("Testing get_riot_account...")
        riot_account = await client.get_riot_account("bexli", "bex")
        print(f"✓ RiotAccount: {riot_account.game_name}#{riot_account.tag_line} (PUUID: {riot_account.puuid[:8]}...)")

        # Test get_summoner_by_puuid
        print("Testing get_summoner_by_puuid...")
        summoner = await client.get_summoner_by_puuid(riot_account.puuid)
        print(f"✓ Summoner: Level {summoner.summoner_level}")

        # Test Player creation
        print("Testing Player creation...")
        player = client.get_player("bexli", "bex")
        print(f"✓ Player created: {player.game_name}#{player.tag_line}")

        # Test async Player methods
        print("Testing async Player methods...")
        riot_account_via_player = await player.get_riot_account()
        print(f"✓ Player.get_riot_account(): {riot_account_via_player.game_name}#{riot_account_via_player.tag_line}")

        summoner_via_player = await player.get_summoner()
        print(f"✓ Player.get_summoner(): Level {summoner_via_player.summoner_level}")

        # Test get_champion_stats
        print("Testing Player.get_champion_stats...")
        champion_stats = await player.get_champion_stats(count=5)
        print(f"✓ Champion stats retrieved: {len(champion_stats)} champions")
        if champion_stats:
            top_champ = champion_stats[0]
            win_rate_percent = top_champ.win_rate
            print(
                f"  Top champion: {top_champ.champion_name} "
                f"({top_champ.games_played} games, {win_rate_percent:.1f}% WR)"
            )

        print("\n✅ All async functionality tests passed!")

    except (ValueError, ConnectionError, KeyError) as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
