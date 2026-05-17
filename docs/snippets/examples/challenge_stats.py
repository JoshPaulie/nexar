import asyncio
import os

from nexar.cache import DEFAULT_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region

client = NexarClient(
    riot_api_key=os.getenv("RIOT_API_KEY", ""),
    cache_config=DEFAULT_CACHE_CONFIG,
)


async def main() -> None:
    async with client:
        player = await client.get_player(riot_id="bexli#bex", region=Region.NA1)
        last_match = await player.get_last_match()
        assert last_match

        participant = last_match.participants.by_puuid(player.puuid)
        assert participant

        challenges = participant.challenges
        if not challenges:
            print("No challenge data available for this match.")
            return

        print(f"Challenges for {participant.game_name} on {participant.champion_name}:")
        print(f"  KDA:                {challenges.kda:.2f}")
        print(f"  Kill Participation: {challenges.kill_participation:.2%}")
        print(f"  Damage/min:         {challenges.damage_per_minute:.0f}")
        print(f"  Gold/min:           {challenges.gold_per_minute:.0f}")
        print(f"  Vision/min:         {challenges.vision_score_per_minute:.2f}")

        # Niche but interesting stats
        print(f"  Team Damage %:      {challenges.team_damage_percentage:.2%}" if challenges.team_damage_percentage else "")
        print(f"  Skillshots Dodged:  {challenges.skillshots_dodged}")
        print(f"  Skillshots Hit:     {challenges.skillshots_hit}")
        print(f"  Epic Monster Steals:{challenges.epic_monster_steals}")
        print(f"  Control Wards:      {challenges.control_wards_placed}")
        print(f"  Multikills:         {challenges.multikills}")
        print(f"  Solo Kills:         {challenges.solo_kills}")
        print(f"  Takedowns:          {challenges.takedowns}")
        print(f"  Turret Plates:      {challenges.turret_plates_taken}")
        print(f"  Killing Sprees:     {challenges.killing_sprees}")
        print(f"  Buffs Stolen:       {challenges.buffs_stolen}")


if __name__ == "__main__":
    asyncio.run(main())
