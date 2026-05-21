import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region
from nexar.models.match.team import TeamInfo, TeamsInfo

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        player = await client.get_player(riot_id="bexli#bex", region=Region.NA1)
        last_match = await player.get_last_match()
        assert last_match

        # Build TeamsInfo from match participants
        blue = TeamInfo(
            team_id=100,
            win=last_match.info.teams[0].win,
            bans=last_match.info.teams[0].bans or [],
            objectives=last_match.info.teams[0].objectives,
            participants=list(last_match.participants.blue_team()),
        )
        red = TeamInfo(
            team_id=200,
            win=last_match.info.teams[1].win,
            bans=last_match.info.teams[1].bans or [],
            objectives=last_match.info.teams[1].objectives,
            participants=list(last_match.participants.red_team()),
        )
        teams = TeamsInfo(blue=blue, red=red)

        for team in teams:
            side = "Blue" if team.team_id == 100 else "Red"
            result = "Won!" if team.win else "Lost"
            print(f"--- {side} Side ({result}) ---")
            print(f"  Total Kills:  {team.total_kills}")
            print(f"  Total Deaths: {team.total_deaths}")
            print(f"  Total Assists:{team.total_assists}")
            print(f"  Total Damage: {team.total_damage:,}")
            print(f"  Total Gold:   {team.total_gold_earned:,}")
            print(f"  Vision Score: {team.total_vision_score}")
            print(f"  Players:")
            for p in team.participants:
                print(f"    {p.champion_name:<12} {p.kda(as_str=True)}")
            print()


if __name__ == "__main__":
    asyncio.run(main())
