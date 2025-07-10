"""
Generate mock responses for testing.

Run this script to capture real API responses that can be used in tests.

# This script was auto generate and incomplete. Saving for future
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path so we can import nexar
sys.path.insert(0, str(Path(__file__).parent / "src"))

from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5


async def generate_mock_responses() -> None:
    """Generate mock responses for common API calls."""
    # Enable debug responses
    os.environ["NEXAR_DEBUG_RESPONSES"] = "1"

    # Get API key
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        print("Please set RIOT_API_KEY environment variable")
        sys.exit(1)

    # Create client with no caching
    client = NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=NO_CACHE_CONFIG,
    )

    mock_responses = {}

    try:
        print("Generating mock responses...")

        # Get riot account
        print("- Getting riot account...")
        riot_account = await client.get_riot_account("bexli", "bex")
        mock_responses["riot_account"] = {
            "puuid": riot_account.puuid,
            "game_name": riot_account.game_name,
            "tag_line": riot_account.tag_line,
        }

        # Get summoner by PUUID
        print("- Getting summoner...")
        summoner = await client.get_summoner_by_puuid(riot_account.puuid, region=RegionV4.NA1)
        mock_responses["summoner"] = {
            "id": summoner.id,
            "puuid": summoner.puuid,
            "profile_icon_id": summoner.profile_icon_id,
            "revision_date": int(summoner.revision_date.timestamp()),
            "summoner_level": summoner.summoner_level,
        }

        # Get match IDs
        print("- Getting match IDs...")
        match_ids = await client.get_match_ids_by_puuid(riot_account.puuid, count=5)
        mock_responses["match_ids"] = match_ids[:3]  # Only keep first 3

        # Get a single match
        if match_ids:
            print("- Getting match details...")
            match = await client.get_match(match_ids[0])
            # Store minimal match data
            mock_responses["match"] = {
                "match_id": match.metadata.match_id,
                "game_duration": match.info.game_duration,
                "game_start_timestamp": int(match.info.game_start_timestamp.timestamp()),
                "participants": [
                    {
                        "puuid": p.puuid,
                        "summoner_name": p.summoner_name,
                        "champion_name": p.champion_name,
                        "kills": p.kills,
                        "deaths": p.deaths,
                        "assists": p.assists,
                        "win": p.win,
                    }
                    for p in match.participants[:2]  # Only first 2 participants
                ],
            }

        # Get league entries
        print("- Getting league entries...")
        league_entries = await client.get_league_entries_by_puuid(riot_account.puuid, region=RegionV4.NA1)
        if league_entries:
            mock_responses["league_entries"] = [
                {
                    "queue_type": entry.queue_type.value,
                    "tier": entry.tier.value,
                    "rank": entry.division.value,
                    "league_points": entry.league_points,
                    "wins": entry.wins,
                    "losses": entry.losses,
                }
                for entry in league_entries[:1]  # Only first entry
            ]

    finally:
        await client.close()

    # Save to file
    output_file = Path("tests/mock_responses.json")
    output_file.write_text(json.dumps(mock_responses, indent=2))

    print(f"Mock responses saved to {output_file}")


if __name__ == "__main__":
    asyncio.run(generate_mock_responses())
