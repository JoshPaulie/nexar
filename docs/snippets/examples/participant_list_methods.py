import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import MatchParticipantPosition, Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        player = await client.get_player(game_name="bexli", tag_line="bex", region=Region.NA1)
        last_match = await player.get_last_match()
        assert last_match

        participants = last_match.participants

        # highest_kda: top 3 by KDA
        print("Top 3 KDA:")
        for p in participants.highest_kda(3):
            print(f"  {p.champion_name:<12} {p.kda(as_str=True)}")

        # most_kills: top 3 by kills
        print("\nMost Kills:")
        for p in participants.most_kills(3):
            print(f"  {p.champion_name:<12} {p.kills} kills")

        # most_damage: top 3 by damage to champions
        print("\nMost Damage:")
        for p in participants.most_damage(3):
            print(f"  {p.champion_name:<12} {p.total_damage_dealt_to_champions:,}")

        # Filter by position
        junglers = participants.by_position(MatchParticipantPosition.JUNGLE)
        print(f"\nJunglers: {[p.champion_name for p in junglers]}")

        # Winners / losers
        print(f"Winners: {len(participants.winners())} players")
        print(f"Losers:  {len(participants.losers())} players")


if __name__ == "__main__":
    asyncio.run(main())
