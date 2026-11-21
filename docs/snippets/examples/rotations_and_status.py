import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        # Both pools in one call; not player-centric, so no puuid is involved.
        rotations = await client.get_champion_rotations(Region.NA1)
        print(f"{len(rotations.sr)} champions free on Summoner's Rift this rotation")
        print(f"{len(rotations.newplayer)} extra champions for players under level 11")

        # Near-realtime service status for the platform.
        status = await client.get_platform_status(Region.NA1)
        print(f"\n{status.name}: {len(status.maintenances)} maintenances, {len(status.incidents)} incidents")
        for incident in status.incidents:
            severity = incident.incident_severity or "info"
            title = incident.titles[0].content if incident.titles else "Untitled incident"
            latest = incident.updates[-1] if incident.updates else None
            when = latest.created_at if latest and latest.created_at else "unknown time"
            print(f"  [{severity}] {title} (first posted {when})")


if __name__ == "__main__":
    asyncio.run(main())
