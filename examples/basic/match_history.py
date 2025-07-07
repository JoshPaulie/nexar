"""Basic example showing how to get recent match history for a player."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import QueueId, RegionV4, RegionV5


async def main() -> None:
    """Demonstrate retrieving recent match history for a player."""
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
        # Create player object
        player = client.get_player("bexli", "bex")
        riot_account = await player.get_riot_account()
        print(f"Getting recent matches for {player}")

        # Get recent matches (last 5 games)
        print("\n=== Recent Matches (All Queues) ===")
        recent_matches = await player.get_matches(count=5)

        for i, match in enumerate(recent_matches, 1):
            # Find this player's participant data
            player_participant = None
            for participant in match.info.participants:
                if participant.puuid == riot_account.puuid:
                    player_participant = participant
                    break

            if player_participant:
                result = "WIN" if player_participant.win else "LOSS"
                kda = f"{player_participant.kills}/{player_participant.deaths}/{player_participant.assists}"
                champion = player_participant.champion_name
                duration_minutes = match.info.game_duration // 60

                print(f"{i}. {result} - {champion} ({kda}) - {duration_minutes}m")

        # Get ranked solo queue matches only
        print("\n=== Recent Ranked Solo Queue Matches ===")
        ranked_matches = await player.get_matches(count=3, queue=QueueId.RANKED_SOLO_5x5)

        for i, match in enumerate(ranked_matches, 1):
            # Find this player's participant data
            player_participant = None
            for participant in match.info.participants:
                if participant.puuid == riot_account.puuid:
                    player_participant = participant
                    break

            if player_participant:
                result = "WIN" if player_participant.win else "LOSS"
                kda = f"{player_participant.kills}/{player_participant.deaths}/{player_participant.assists}"
                champion = player_participant.champion_name
                cs = player_participant.total_minions_killed + player_participant.neutral_minions_killed

                print(f"{i}. {result} - {champion} ({kda}) - {cs} CS")


if __name__ == "__main__":
    asyncio.run(main())
