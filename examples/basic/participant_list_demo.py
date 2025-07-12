"""Example demonstrating the ParticipantList functionality."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import MatchParticipantPosition, RegionV4, RegionV5

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if api_key is not None:
    sys.exit("Please set RIOT_API_KEY environment variable")


async def main() -> None:
    """Demonstrate ParticipantList filtering capabilities."""
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as client:
        # Get a player and their recent match
        player = await client.get_player("bexli", "bex")
        recent_matches = await player.get_matches(count=1)

        if not recent_matches:
            print("No recent matches found")
            return

        match = recent_matches[0]
        participants = match.participants

        print(f"Match ID: {match.metadata.match_id}")
        print(f"Total participants: {len(participants)}")
        print()

        # Find the player we're looking for
        target_participant = participants.by_puuid(player.puuid)
        if target_participant:
            print(f"Found {player.riot_account.game_name} playing {target_participant.champion_name}")
            print(f"KDA: {target_participant.kda(as_str=True)}")
            print(f"Team: {target_participant.team_color}")
            print()  # Team analysis using ParticipantList methods
        print("=== Team Analysis ===")
        blue_team = participants.blue_team()
        red_team = participants.red_team()

        print(f"Blue team ({len(blue_team)} players):")
        for p in blue_team:
            print(f"  {p.game_name} - {p.champion_name} ({p.kda(as_str=True)})")

        print(f"\nRed team ({len(red_team)} players):")
        for p in red_team:
            print(f"  {p.game_name} - {p.champion_name} ({p.kda(as_str=True)})")

        # Compare team performance
        blue_total_kills = sum(p.kills for p in blue_team)
        red_total_kills = sum(p.kills for p in red_team)
        print(f"\nTeam kills: Blue {blue_total_kills}, Red {red_total_kills}")

        winning_team = participants.winners()
        print(f"Winning team: {'Blue' if winning_team[0].team_id == 100 else 'Red'}")
        print()

        # Find players by position
        junglers = participants.by_position(MatchParticipantPosition.JUNGLE)
        print(f"Junglers ({len(junglers)}):")
        for p in junglers:
            print(f"  {p.game_name} - {p.champion_name}")
        print()

        # Get top performers
        top_killers = participants.most_kills(count=3)
        print("Top 3 killers:")
        for i, p in enumerate(top_killers, 1):
            print(f"  {i}. {p.game_name} - {p.kills} kills ({p.champion_name})")
        print()

        highest_kda = participants.highest_kda(count=3)
        print("Top 3 KDA:")
        for i, p in enumerate(highest_kda, 1):
            kda_ratio = (p.kills + p.assists) / max(p.deaths, 1)
            print(f"  {i}. {p.game_name} - {kda_ratio:.2f} KDA ({p.champion_name})")
        print()

        # Filter with custom predicate
        high_damage_dealers = participants.filter(
            lambda p: p.total_damage_dealt_to_champions > 20000,
        )
        print(f"High damage dealers (>20k damage): {len(high_damage_dealers)}")
        for p in high_damage_dealers:
            print(f"  {p.game_name} - {p.total_damage_dealt_to_champions:,} damage")
        print()

        # Chain operations
        winning_supports = participants.winners().by_position(MatchParticipantPosition.UTILITY)
        if winning_supports:
            print("Winning support players:")
            for p in winning_supports:
                print(f"  {p.game_name} - {p.champion_name}")
        else:
            print("No winning support players found")


if __name__ == "__main__":
    asyncio.run(main())
