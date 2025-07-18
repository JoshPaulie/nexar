import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region

riot_api = os.getenv("RIOT_API_KEY")
if riot_api is None:
    sys.exit("Couldn't find RIOT_API_KEY.")

client = NexarClient(
    riot_api_key=riot_api,
    default_region=Region.NA1,
    cache_config=SMART_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        # --8<-- [start:get-player]
        from nexar.models import Player

        # Get player with default region set in client
        player = await client.get_player("bexli", "bex")
        # or
        player = await Player.by_riot_id(client, "bexli#bex")
        # or
        player = await Player.create(client, "bexli", "bex")

        # Get a player from a different region
        eu_player = await client.get_player(
            "Thebausffs",
            "COOL",
            region=Region.EUW1,
        )
        # --8<-- [end:get-player]

        # --8<-- [start:get-players]
        players = await client.get_players(["bexli#bex", "mltsimpleton#na1"])

        # Iterate over players
        for player in players:
            # Get player summoner info
            player_summoner = await player.get_summoner()
            # Print player summoner level
            print(f"{player.game_name} is level {player_summoner.summoner_level}")
        # --8<-- [end:get-players]

        # Reset player to me from previous example
        player = await client.get_player("bexli", "bex")

        # --8<-- [start:get-ranks]
        # Solo queue
        solo_rank = await player.get_solo_rank()

        if solo_rank:
            solo_tier = solo_rank.tier  # RankTier.Bronze, RankTier.Iron, ...
            solo_division = solo_rank.tier  # RankDivision.IV, RankDivision.III, ...
            solo_league_points = solo_rank.league_points

        # Flex queue
        solo_rank = await player.get_flex_rank()

        # Of course, all of the same properties as Solo queue

        # --8<-- [end:get-ranks]

        # --8<-- [start:get-matches]
        from nexar.enums import Queue

        # Get player's last match
        last_match = await player.get_last_match()

        # Get player's recent draft pick matches
        last_10_draft_matches = await player.get_matches(
            count=10,
            queue=Queue.DRAFT_PICK,
        )
        # --8<-- [end:get-matches]

        # --8<-- [start:champ-metrics]
        # Get recent champion performance from matches
        recent_champion = last_10_draft_matches.get_champion_stats()
        if recent_champion:
            for stat in recent_champion:
                print(f"Average KDA with {stat.champion_name}: {stat.avg_kda:.2f}")
        # --8<-- [end:champ-metrics]


if __name__ == "__main__":
    asyncio.run(main())
