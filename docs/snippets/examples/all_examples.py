import asyncio
import os
import sys
import datetime as dt

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region, Queue
from nexar.models import Player
from nexar.utils import sort_players_by_rank

# Get API key from environment
api_key = os.getenv("RIOT_API_KEY")
if api_key is None:
    sys.exit("Please set RIOT_API_KEY environment variable")

client = NexarClient(
    riot_api_key=api_key,
    default_region=Region.NA1,
    cache_config=SMART_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        # --8<-- [start:batch-players-demo]
        # List of riot IDs to fetch
        riot_ids = [
            "bexli#bex",
            "mltsimpleton#na1",
        ]

        print(f"Fetching {len(riot_ids)} players...")

        # Fetch all players in parallel
        players = await client.get_players(riot_ids)

        print(f"Successfully retrieved {len(players)} players!\n")
        # --8<-- [end:batch-players-demo]

        # --8<-- [start:batch-players-regions]
        riot_ids_korean: list[str] = []  # Imagine this is populated with Korean players

        players_korean = await client.get_players(
            riot_ids_korean,
            region=Region.KR,
        )
        # --8<-- [end:batch-players-regions]

        # --8<-- [start:champ-performance-demo]
        # Get player
        player = await client.get_player("bexli", "bex")

        # Get recent matches
        matches = await player.get_matches()

        champ_performance = matches.get_champion_stats()
        for champ in champ_performance:
            print(champ.champion_name)
            print(f"{champ.wins} wins / {champ.losses} losses ({champ.win_rate:.2g}%)")
            kda = f"{champ.avg_kills:.2g}/{champ.avg_deaths:.2g}/{champ.avg_assists:.2g}"
            print(f"Average KDA: {kda} ({champ.avg_kda:.2g})\n")
        # --8<-- [end:champ-performance-demo]

        # --8<-- [start:match-history-demo]
        # Get player
        player = await client.get_player("bexli", "bex")

        # Get last 20 matches
        matches = await player.get_matches()

        # Get last 5 solo queue matches
        matches = await player.get_matches(count=5, queue=Queue.SOLO_QUEUE)

        # Get last week's matches
        past_week = dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=7)
        past_week_matches = await player.get_matches(start_time=past_week)

        # Get last match
        last_match = await player.get_last_match()
        # --8<-- [end:match-history-demo]

        # --8<-- [start:player-performance-demo]
        # Get player
        player = await client.get_player("bexli", "bex")

        # Get recent matches
        matches = await player.get_matches(count=20)

        # Get recent performance stats
        performance = matches.get_performance_stats()

        print(f"Performance over {performance.total_games} recent games:")
        print(f"Win Rate: {performance.win_rate:.1f}% ({performance.wins}W/{performance.losses}L)")

        kda_str = f"{performance.avg_kills:.1f}/{performance.avg_deaths:.1f}/{performance.avg_assists:.1f}"
        print(f"Average KDA: {kda_str} ({performance.avg_kda:.2f})")
        print(f"Average CS: {performance.avg_cs:.1f}")
        print(f"Average Game Duration: {performance.avg_game_duration_minutes:.1f} minutes")
        # --8<-- [end:player-performance-demo]

        # --8<-- [start:sort-players-by-rank-demo]
        # Get players
        riot_ids = [
            "bexli#bex",
            "mltsimpleton#na1",
            "roninalex#na1",
            "poydok#na1",
            "boxrog#na1",
            "vynle#na1",
        ]

        print(f"Fetching {len(riot_ids)} players...\n")

        # Fetch all players in parallel
        players = await client.get_players(riot_ids)

        # Players sorted by rank
        sorted_players = await sort_players_by_rank(players)

        # Print them!
        for player in sorted_players:
            solo_rank = await player.get_solo_rank()
            rank_text = (
                f"{solo_rank.tier} {solo_rank.division:<3} ({solo_rank.league_points} LP)"
                if solo_rank  # Handle unranked
                else "Unranked!"
            )
            print(f"{player.game_name:<12} :: {rank_text}")
        # --8<-- [end:sort-players-by-rank-demo]


if __name__ == "__main__":
    asyncio.run(main())