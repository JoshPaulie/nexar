import os
import sys

from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5
from nexar.utils import sort_players_by_solo_queue_rank

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

# Example player names and tags (replace with real ones as needed)
players_info = [
    ("bexli", "bex"),
    ("roninalex", "na1"),
    ("MltSimpleton", "na1"),
]

# Create list of Player objects
players = [client.get_player(name, tag) for name, tag in players_info]

# Fetch solo queue ranks for all players (forces API call)
for player in players:
    _ = player.solo_rank_value  # Ensures rank is loaded

# Sort list of players by solo queue rank (highest first)
sorted_players = sort_players_by_solo_queue_rank(players)

print("Players sorted by solo queue rank (highest to lowest):")
for player in sorted_players:
    rank = player.rank
    if rank:
        print(f"{player.game_name}: {rank.tier.name.title()} {rank.rank.value}")
    else:
        print(f"{player.game_name}: Unranked")
