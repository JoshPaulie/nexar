import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import RegionV4, RegionV5

from datetime import datetime, UTC

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

        # --8<-- [start:get-match]
        last_match = await player.get_last_match()
        assert last_match

        start_time = last_match.info.game_start_timestamp
        days_ago = (datetime.now(tz=UTC) - start_time).days
        print(f"{player.game_name}'s last game was {days_ago} day(s) ago")
        # --8<-- [end:get-match]

        print()

        # --8<-- [start:participants]
        participants = last_match.participants
        winning_team = participants.winners()

        winner_names = ", ".join([p.game_name or "Unknown" for p in winning_team])
        print(f"Winners! {winner_names}\n")

        for p in participants:
            name = p.game_name
            champ_name = p.champion_name
            kda = p.kda(as_str=True)
            print(f"{name} ({champ_name}) went {kda}")

        # --8<-- [end:participants]

        # --8<-- [start:get-participant]
        # Get participant by PUUID (easiest is from Player.puuid)
        participant = participants.by_puuid(player.puuid)

        # Get participants by position
        from nexar.enums import MatchParticipantPosition as Position

        bot_participants = participants.by_position(Position.BOTTOM)

        # Get participants by champion (Not recommended, prone to typos)
        jinx_players = participants.by_champion("Jinx")
        # --8<-- [end:get-participant]

        # --8<-- [start:get-team]
        # Get blue team
        blue_team = participants.blue_team()

        # Get red team
        red_team = participants.red_team()

        # Get team of particular player
        team_of_player = participants.team_of(player.puuid)
        # --8<-- [end:get-team]

        # Reset participant
        participant = participants.by_puuid(player.puuid)
        assert participant is not None

        # --8<-- [start:participant]
        # Typical stats
        magic_damage = participant.magic_damage_dealt_to_champions
        cs = participant.creep_score
        drags = participant.dragon_kills

        # The really fun stuff
        assert participant.challenges
        buffs_stolen = participant.challenges.buffs_stolen
        gold_per_min = participant.challenges.gold_per_minute
        # --8<-- [end:participant]


if __name__ == "__main__":
    asyncio.run(main())
