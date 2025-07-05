"""Test script to verify enum conversions are working correctly."""

import os

from nexar.client import NexarClient
from nexar.enums import MapId, PlatformId, QueueId, RegionV4, RegionV5

client = NexarClient(
    os.getenv("RIOT_API_KEY"),
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
)

me = client.get_player("bexli", "bex")
last_game = me.get_recent_matches(1)[0]

print("=== Enum Conversion Test ===")
print(f"Map ID: {last_game.info.map_id} (type: {type(last_game.info.map_id)})")
print(
    f"Platform ID: {last_game.info.platform_id} (type: {type(last_game.info.platform_id)})"
)
print(f"Queue ID: {last_game.info.queue_id} (type: {type(last_game.info.queue_id)})")

print("\n=== Verifying enum types ===")
print(f"Map ID is MapId enum: {isinstance(last_game.info.map_id, MapId)}")
print(
    f"Platform ID is PlatformId enum: {isinstance(last_game.info.platform_id, PlatformId)}"
)
print(f"Queue ID is QueueId enum: {isinstance(last_game.info.queue_id, QueueId)}")

print("\n=== Verifying enum values ===")
print(f"Map ID value: {last_game.info.map_id.value}")
print(f"Platform ID value: {last_game.info.platform_id.value}")
print(f"Queue ID value: {last_game.info.queue_id.value}")
