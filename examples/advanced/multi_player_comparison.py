"""Advanced example comparing multiple players' performance using the Player API."""

import asyncio
import os
import sys

from nexar.cache import SMART_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import QueueId, RegionV4, RegionV5
from nexar.models.player import Player


async def compare_players(players: list[Player], analysis_games: int = 20):
    """Compare performance metrics across multiple players."""
    print(f"\n=== Comparing {len(players)} Players (Last {analysis_games} Games) ===")

    player_data = []

    for player in players:
        try:
            # Get basic info
            summoner = await player.get_summoner()
            summoner_level = summoner.summoner_level
            rank_info = "Unranked"
            player_rank = await player.get_rank()
            if player_rank:
                rank_info = f"{player_rank.tier.value} {player_rank.rank.value} ({player_rank.league_points} LP)"

            # Get performance summary
            performance = await player.get_performance_summary(
                count=analysis_games,
                queue=QueueId.RANKED_SOLO_5x5,
            )

            # Get top champion
            top_champions = await player.get_top_champions(
                top_n=1,
                count=analysis_games,
                queue=QueueId.RANKED_SOLO_5x5,
            )
            top_champion = top_champions[0].champion_name if top_champions else "None"

            # Check win streak
            on_streak = await player.is_on_win_streak(min_games=3)

            player_data.append(
                {
                    "player": player,
                    "summoner_level": summoner_level,
                    "rank": rank_info,
                    "performance": performance,
                    "top_champion": top_champion,
                    "on_streak": on_streak,
                },
            )

        except ValueError as e:
            print(f"Error analyzing {player}: {e}")
            continue

    if not player_data:
        print("No player data available for comparison")
        return None

    # Print comparison table
    print(
        f"\n{'Player':<20} {'Level':<6} {'Rank':<20} {'WR%':<6} {'Avg KDA':<8} {'Top Champ':<15} {'Streak':<6}",
    )
    print("-" * 95)

    for data in player_data:
        player_name = f"{data['player'].game_name}#{data['player'].tag_line}"
        level = data["summoner_level"]
        rank = data["rank"][:19]  # Truncate long rank strings
        perf = data["performance"]
        win_rate = f"{perf['win_rate']:.1f}%" if perf["total_games"] > 0 else "N/A"
        avg_kda = f"{perf['avg_kda']:.2f}" if perf["total_games"] > 0 else "N/A"
        top_champ = data["top_champion"][:14]  # Truncate long champion names
        streak = "YES" if data["on_streak"] else "NO"

        print(
            f"{player_name:<20} {level:<6} {rank:<20} {win_rate:<6} {avg_kda:<8} {top_champ:<15} {streak:<6}",
        )

    # Detailed performance comparison
    print("\n=== Detailed Performance Metrics ===")

    # Sort by win rate for rankings
    sorted_by_wr = sorted(
        [d for d in player_data if d["performance"]["total_games"] > 0],
        key=lambda x: x["performance"]["win_rate"],
        reverse=True,
    )

    if sorted_by_wr:
        print(
            f"\n🏆 Highest Win Rate: {sorted_by_wr[0]['player'].game_name}#{sorted_by_wr[0]['player'].tag_line}",
        )
        print(
            f"   {sorted_by_wr[0]['performance']['win_rate']:.1f}% ({sorted_by_wr[0]['performance']['wins']}W/{sorted_by_wr[0]['performance']['losses']}L)",
        )

    # Sort by KDA
    sorted_by_kda = sorted(
        [d for d in player_data if d["performance"]["total_games"] > 0],
        key=lambda x: x["performance"]["avg_kda"],
        reverse=True,
    )

    if sorted_by_kda:
        print(
            f"\n🎯 Best KDA: {sorted_by_kda[0]['player'].game_name}#{sorted_by_kda[0]['player'].tag_line}",
        )
        perf = sorted_by_kda[0]["performance"]
        print(
            f"   {perf['avg_kills']:.1f}/{perf['avg_deaths']:.1f}/{perf['avg_assists']:.1f} ({perf['avg_kda']:.2f} KDA)",
        )

    # Players on win streaks
    streak_players = [d for d in player_data if d["on_streak"]]
    if streak_players:
        print("\n🔥 Players on Win Streaks:")
        for data in streak_players:
            print(f"   {data['player'].game_name}#{data['player'].tag_line}")

    return player_data


async def analyze_champion_overlap(players: list[Player], analysis_games: int = 30):
    """Analyze what champions multiple players have in common."""
    print(f"\n=== Champion Pool Analysis (Last {analysis_games} Games) ===")

    all_champions = {}
    player_champions = {}

    for player in players:
        try:
            player_name = f"{player.game_name}#{player.tag_line}"
            champions = await player.get_champion_stats(
                count=analysis_games,
                queue=QueueId.RANKED_SOLO_5x5,
            )

            player_champions[player_name] = champions

            for champ in champions:
                if champ.games_played >= 2:  # Only count champions with 2+ games
                    if champ.champion_name not in all_champions:
                        all_champions[champ.champion_name] = []
                    all_champions[champ.champion_name].append(
                        {
                            "player": player_name,
                            "games": champ.games_played,
                            "win_rate": champ.win_rate,
                        },
                    )
        except ValueError as e:
            print(f"Error getting champions for {player}: {e}")
            continue

    # Find commonly played champions
    common_champions = {
        champ: players_data
        for champ, players_data in all_champions.items()
        if len(players_data) >= 2  # Played by at least 2 players
    }

    if common_champions:
        print("\nCommonly Played Champions:")
        for champion, players_data in sorted(common_champions.items()):
            print(f"\n{champion}:")
            for player_data in sorted(
                players_data,
                key=lambda x: x["win_rate"],
                reverse=True,
            ):
                print(
                    f"  {player_data['player']}: {player_data['games']} games, {player_data['win_rate']:.1f}% WR",
                )

    # Find unique champions (played by only one player)
    unique_champions = {
        champ: players_data[0]
        for champ, players_data in all_champions.items()
        if len(players_data) == 1 and players_data[0]["games"] >= 3
    }

    if unique_champions:
        print("\nUnique Champions (3+ games):")
        for champion, player_data in sorted(unique_champions.items()):
            print(
                f"  {champion}: {player_data['player']} ({player_data['games']} games, {player_data['win_rate']:.1f}% WR)",
            )


async def main() -> None:
    """Multi-Player Analysis Demo."""
    # Get API key from environment
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        sys.exit("Please set RIOT_API_KEY environment variable")

    # Create async client
    async with NexarClient(
        riot_api_key=api_key,
        default_v4_region=RegionV4.NA1,
        default_v5_region=RegionV5.AMERICAS,
        cache_config=SMART_CACHE_CONFIG,
    ) as client:
        print("=== Multi-Player Analysis Demo ===")

        # Create player objects for comparison
        # You can add more players by adding their game names and tag lines
        players_to_compare = [
            await client.get_player("bexli", "bex"),
            await client.get_player("roninalex", "na1"),
            # Add more players here for comparison
            # await client.get_player("other_player", "tag"),
        ]

        if len(players_to_compare) == 1:
            print("Note: Only one player configured. To see comparison features,")
            print("add more players to the players_to_compare list in the code.")
            print(f"\nAnalyzing single player: {players_to_compare[0]}")

        # Compare players
        await compare_players(players_to_compare, analysis_games=20)

        # Analyze champion pools if multiple players
        if len(players_to_compare) > 1:
            await analyze_champion_overlap(players_to_compare, analysis_games=30)

        print("\n=== Multi-Player Analysis Complete ===")
        print("This example demonstrates:")
        print("- Comparing performance metrics across players")
        print("- Ranking players by different statistics")
        print("- Identifying champion pool overlaps and unique picks")
        print("- Finding players on win streaks")
        print("- Add more players to players_to_compare list for better comparison")


if __name__ == "__main__":
    asyncio.run(main())
