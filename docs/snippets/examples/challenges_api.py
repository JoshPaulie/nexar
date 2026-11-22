import asyncio
import os

from nexar.client import NexarClient
from nexar.enums import ChallengeLevel, Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
)


async def main() -> None:
    async with client:
        # The whole catalog in one call (405 challenges on NA at recording).
        configs = await client.get_all_challenge_configs(Region.NA1)
        print(f"{len(configs)} challenges, {sum(c.leaderboard for c in configs)} with leaderboards")

        # Localized display strings, one entry per locale.
        crystal = next(c for c in configs if c.id == 0)
        print(f"\nChallenge #{crystal.id}: {crystal.localized_names['en_US'].name}")
        print(f"  state={crystal.state}, MASTER threshold={crystal.thresholds.get('MASTER')}")

        # Percentile map for one challenge: level name -> share of players at or above it.
        percentiles = await client.get_challenge_percentiles(crystal.id, Region.NA1)
        print(f"\nCRYSTAL MASTER percentile: {percentiles.get('MASTER')}")

        # Leaderboards serve the apex levels only (MASTER/GRANDMASTER/CHALLENGER).
        board = await client.get_challenge_leaderboard(crystal.id, ChallengeLevel.MASTER, Region.NA1, limit=3)
        print(f"\nTop {len(board)} CRYSTAL MASTER players:")
        for row in board:
            print(f"  #{row.position}: {row.value:g}")

        # The one player-centric op, also available as Player.get_challenge_data().
        player = await client.get_player(game_name="bexli", tag_line="bex", region=Region.NA1)
        data = await player.get_challenge_data()
        print(f"\n{player} has {len(data.challenges)} progressed challenges")
        if data.total_points is not None:
            print(f"Total points: {data.total_points.current}/{data.total_points.max} ({data.total_points.level})")


if __name__ == "__main__":
    asyncio.run(main())
