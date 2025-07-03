"""Example usage of the get_league_entries_by_puuid method."""

import os
import sys

from nexar import NexarClient, RegionV4, RegionV5

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if api_key is None:
    sys.exit("No RIOT_API_KEY environment variable found")

# Initialize the client
client = NexarClient(
    riot_api_key=api_key,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
)

# Get PUUID from a riot account (using test account as example)
account = client.get_riot_account("bexli", "bex")
puuid = account.puuid
print(f"Found account: {account.game_name}#{account.tag_line}\n")

# Get league entries for the player
league_entries = client.get_league_entries_by_puuid(puuid)

if not league_entries:
    print("No ranked entries found for this player.")
else:
    print(f"Found {len(league_entries)} ranked queue(s):\n")

    for entry in league_entries:
        print(f"Queue: {entry.queue_type.value}")
        print(f"Rank: {entry.tier.value} {entry.rank.value}")
        print(f"League Points: {entry.league_points} LP")
        print(f"Win/Loss: {entry.wins}W / {entry.losses}L")
        print(f"Win Rate: {entry.win_rate:.1f}%")

        # Display player status flags
        status_flags = []
        if entry.hot_streak:
            status_flags.append("🔥 Hot Streak")
        if entry.veteran:
            status_flags.append("🏆 Veteran")
        if entry.fresh_blood:
            status_flags.append("✨ Fresh Blood")
        if entry.inactive:
            status_flags.append("💤 Inactive")

        if status_flags:
            print(f"Status: {', '.join(status_flags)}")

        # Display mini series progress if in promos
        if entry.mini_series:
            print(
                f"Promotion Series: {entry.mini_series.progress} "
                f"({entry.mini_series.wins}W/{entry.mini_series.losses}L, "
                f"target: {entry.mini_series.target})"
            )

        print()  # Empty line between entries

"""
Example output:

Found account: bexli#bex (PUUID: 0wKS4PaI...)

Found 1 ranked queue(s):

Queue: RANKED_SOLO_5x5
Rank: SILVER IV
League Points: 63 LP
Win/Loss: 50W / 42L
Win Rate: 54.3%
Status: 🏆 Veteran

"""
