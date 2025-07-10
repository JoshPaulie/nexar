import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

from datetime import datetime

riot_api = os.getenv("RIOT_API_KEY")
if riot_api is None:
    sys.exit("Couldn't find RIOT_API_KEY.")

client = NexarClient(
    riot_api_key=riot_api,
    default_v4_region=RegionV4.NA1,
    default_v5_region=RegionV5.AMERICAS,
    cache_config=SMART_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        player = await client.get_player("bexli", "bex")
        last_match = await player.get_last_match()
        if not last_match:
            print("This player doesn't have a recent match.")
            sys.exit()

        # --8<-- [start:get-match]
        last_match = await player.get_last_match()

        start_time = last_match.info.game_start_timestamp
        days_ago = (datetime.now() - start_time).days
        print(f"{player.game_name}'s last game was {days_ago} day(s) ago")
        # --8<-- [end:get-match]

        print()

        # --8<-- [start:participants]
        participants = last_match.participants
        winning_team = participants.winners()

        winner_names = ", ".join([p.riot_id_game_name for p in winning_team])
        print(f"Winners! {winner_names}\n")

        for participant in participants:
            name = participant.riot_id_game_name
            champ_name = participant.champion_name
            kda = participant.kda(as_str=True)
            print(f"{name} ({champ_name}) went {kda}")

        # --8<-- [end:participants]

        # --8<-- [start:get-participant]
        # By PUUID (easiest is from Player.puuid)
        participant = participants.by_puuid(player.puuid)

        # By position
        from nexar.enums import MatchParticipantPosition as Position

        participant = participants.by_position(Position.BOTTOM)

        # By champion (Not recommended, prone to typos)
        participant = participants.by_champion("Jinx")
        # --8<-- [end:get-participant]

        # Reset participant
        participant = participants.by_puuid(player.puuid)

        # --8<-- [start:participant]
        # Typical stats
        magic_damage = participant.magic_damage_dealt_to_champions
        cs = participant.creep_score
        drags = participant.dragon_kills

        # The really fun stuff
        buffs_stolen = participant.challenges.buffs_stolen
        gold_per_min = participant.challenges.gold_per_minute
        # --8<-- [end:participant]


if __name__ == "__main__":
    asyncio.run(main())
