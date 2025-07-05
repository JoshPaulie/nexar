import os
from datetime import datetime

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

# Create client
client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY"),
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)

# Get player information
player = client.get_player("bexli", "bex")

print()
print(f"Summoner: {player.riot_account.game_name}")
print(f"Level: {player.summoner.summoner_level}")
if player.rank:
    rank_text = f"{player.rank.tier.value.title()} {player.rank.rank.value}"
    print(f"Solo Queue rank: {rank_text}\n")

# Get and display recent matches
recent_matches = player.get_recent_matches(count=5)
print(f"Recent Match History ({len(recent_matches)} matches):\n")

for match in recent_matches:
    # Find player's performance in this match
    for participant in match.info.participants:
        if participant.puuid == player.puuid:
            result = "Victory!" if participant.win else "Defeat."
            kda = participant.kda(as_str=True)
            kda_ratio = f"{participant.challenges.kda:.2f}"

            days_ago = (datetime.today() - match.info.game_start_timestamp).days
            days_ago_str = f"{days_ago} {'day' if days_ago == 1 else 'days'} ago"

            print(
                f"{days_ago_str:<10} "
                f"{result:<9} "
                f"{participant.champion_name:<8} "
                f"{participant.team_position.value.title():<6} "
                f"{kda} ({kda_ratio})",
            )
            break
