"""Example demonstrating direct API usage for getting match IDs with various filters."""

import asyncio
import os
import sys
from datetime import datetime, timedelta

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import MatchType, QueueId, RegionV4, RegionV5


async def main() -> None:
    """Demonstrate direct API usage for getting match IDs with various filters."""
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
        print("=== Match IDs API Example ===")

        # Get PUUID using Player API for convenience
    player = await client.get_player("bexli", "bex")
    puuid = player.puuid
    print(f"Analyzing matches for: {player}\n")

    # Example 1: Basic usage - get the last 20 match IDs
    print("1. Basic usage - last 20 match IDs:")
    match_ids = await client.get_match_ids_by_puuid(puuid)
    print(f"   Found {len(match_ids)} match IDs")
    print(f"   Most recent: {match_ids[0] if match_ids else 'None'}")

    # Example 2: Filter by queue type
    print("\n2. Ranked Solo Queue matches only:")
    ranked_match_ids = await client.get_match_ids_by_puuid(
        puuid,
        queue=QueueId.RANKED_SOLO_5x5,
        count=10,
    )
    print(f"   Found {len(ranked_match_ids)} ranked match IDs")

    # Example 3: Filter by time range (last 7 days)
    print("\n3. Matches from last 7 days:")
    end_time = datetime.now().astimezone()
    start_time = end_time - timedelta(days=7)

    recent_match_ids = await client.get_match_ids_by_puuid(
        puuid,
        start_time=start_time,
        end_time=end_time,
        count=50,
    )
    print(f"   Found {len(recent_match_ids)} matches in last 7 days")

    # Example 4: Filter by match type
    print("\n4. Ranked matches only (any ranked queue):")
    ranked_any_match_ids = await client.get_match_ids_by_puuid(
        puuid,
        match_type=MatchType.RANKED,
        count=15,
    )
    print(f"   Found {len(ranked_any_match_ids)} ranked matches")

    # Example 5: Pagination
    print("\n5. Pagination example:")
    page_1 = await client.get_match_ids_by_puuid(puuid, start=0, count=5)
    page_2 = await client.get_match_ids_by_puuid(puuid, start=5, count=5)
    page_3 = await client.get_match_ids_by_puuid(puuid, start=10, count=5)

    print(f"   Page 1 (0-4): {len(page_1)} matches")
    print(f"   Page 2 (5-9): {len(page_2)} matches")
    print(f"   Page 3 (10-14): {len(page_3)} matches")

    # Example 6: Combine multiple filters
    print("\n6. Complex filtering - ranked matches from last 30 days:")
    thirty_days_ago = datetime.now().astimezone() - timedelta(days=30)

    complex_match_ids = await client.get_match_ids_by_puuid(
        puuid,
        start_time=thirty_days_ago,
        queue=QueueId.RANKED_SOLO_5x5,
        count=25,
    )
    print(f"   Found {len(complex_match_ids)} ranked solo queue matches from last 30 days")

    # Example 7: Get match details for analysis
    if match_ids:
        print("\n7. Getting match details for most recent match:")
        match_id = match_ids[0]
        match = await client.get_match(match_id)

        print(f"   Match ID: {match_id}")
        print(
            f"   Game Duration: {match.info.game_duration // 60}m {match.info.game_duration % 60}s",
        )
        print(f"   Queue: {match.info.queue_id}")
        print(f"   Participants: {len(match.info.participants)}")

        # Find our player's performance
        for participant in match.info.participants:
            if participant.puuid == puuid:
                result = "WIN" if participant.win else "LOSS"
                kda = f"{participant.kills}/{participant.deaths}/{participant.assists}"
                print(
                    f"   Player Result: {result} with {participant.champion_name} ({kda})",
                )
                break

        print("\n=== Match IDs API Example Complete ===")
        print("This demonstrates the low-level match IDs API.")
        print("For most use cases, prefer the high-level Player API:")
        print("  await player.get_recent_matches(count=20, queue=QueueId.RANKED_SOLO_5x5)")


if __name__ == "__main__":
    asyncio.run(main())
