import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region
from nexar.utils import team_total_percentage

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        # Create a player object to look up
        player = await client.get_player(game_name="bexli", tag_line="bex", region=Region.NA1)

        # Get the player's last match
        last_game = await player.get_last_match()
        assert last_game

        # Get the participant object for the player in that match
        participant = last_game.participants.by_puuid(player.puuid)
        assert participant

        # Print the game mode
        game_mode = last_game.info.queue_id.name.replace("_", " ").title()
        print(f"~~ {game_mode} ~~")

        # Team kills
        blue_team_kills = sum(p.kills for p in last_game.participants.by_team(100))
        red_team_kills = sum(p.kills for p in last_game.participants.by_team(200))
        print(f"(Blue) {blue_team_kills} vs. {red_team_kills} (Red)")

        # Print player stats from the match
        match_duration = last_game.info.game_duration // 60
        cs = participant.creep_score
        cs_per_minute = cs / match_duration
        result = "won!" if participant.win else "lost."
        print(f"\n{participant.game_name} played {participant.champion_name} (and {result})")
        print(f"KDA: {participant.kda_str} ({participant.challenges.kda:.2f})")
        print(f"CS: {cs} ({cs_per_minute:.1f} per minute)")

        # Get the player's team in that match
        last_team = last_game.participants.by_team(participant.team_id)

        # Print teammates and their stats
        print("\nTeam:")
        for teammate in [p for p in last_team if p != participant]:
            print(f"- {teammate.game_name} played {teammate.champion_name} ({teammate.kda_str})")

        # Use the team_total_percentage utility function to calculate the percentage of the team's
        # total damage dealt to champions that was contributed by the player
        team_total_damage = team_total_percentage(
            last_game.participants,
            participant,
            lambda p: p.total_damage_dealt_to_champions,
        )

        print(f"\nTotal damage dealt to champions: {participant.total_damage_dealt_to_champions:,}")
        print(f"..that's {team_total_damage:.2f}% of the team's total damage dealt to champions!")

        # Use same util function to find kill participation percentage
        team_kills = team_total_percentage(
            last_game.participants,
            participant,
            lambda p: p.kills + p.assists,
        )

        print(f"\nKill participation: {participant.kills + participant.assists} kills & assists")
        print(f"..that's {team_kills:.2f}% of the team's total kills!")


if __name__ == "__main__":
    asyncio.run(main())
