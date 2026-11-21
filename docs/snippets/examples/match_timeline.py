import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Queue, Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        player = await client.get_player(riot_id="bexli#bex", region=Region.NA1)

        match_ids = await player.get_match_ids(queue=Queue.RANKED_SOLO_5x5, count=1)
        if not match_ids:
            print("No ranked matches yet.")
            return

        timeline = await client.get_match_timeline(match_ids[0], region=Region.NA1)

        # Gold curve for one player: one snapshot per minute
        frames = timeline.frames_for(player.puuid)
        if not frames:
            print("No frames for this player in that match.")
            return
        print(f"{len(frames)} minute snapshots")
        print(f"final total gold: {frames[-1].total_gold:,}")

        # The flattened event stream
        kills = [event for event in timeline.events if event.type == "CHAMPION_KILL"]
        if kills:
            first = kills[0]
            print(f"first kill at {first.timestamp / 1000:.0f}s, bounty {first.bounty}")

        wards = sum(1 for event in timeline.events if event.type == "WARD_PLACED")
        print(f"wards placed in the match: {wards}")


if __name__ == "__main__":
    asyncio.run(main())
