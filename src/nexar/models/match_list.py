"""Specialized list class for working with a player's matches."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, SupportsIndex, cast, overload

from nexar.models.stats import ChampionStats, PerformanceStats

if TYPE_CHECKING:
    from nexar.models.match.match import Match
    from nexar.models.match.participant import Participant


class MatchList(list["Match"]):
    """
    A specialized list for a player's matches with methods for calculating stats.

    Extends the built-in list while providing convenient methods for common
    queries and filters.
    """

    def __init__(self, matches: list["Match"], puuid: str) -> None:
        super().__init__(matches)
        self.puuid = puuid

    def get_champion_stats(
        self,
    ) -> list[ChampionStats]:
        """
        Get champion statistics for the player.

        Returns:
            List of ChampionStats objects sorted by games played (descending)

        """
        # Aggregate stats by champion
        champion_data: dict[int, dict[str, Any]] = {}

        for match in self:
            # Find the participant for this player
            participant = match.participants.by_puuid(self.puuid)

            if not participant:
                continue

            champion_id = participant.champion_id
            champion_name = participant.champion_name

            if champion_id not in champion_data:
                champion_data[champion_id] = {
                    "champion_name": champion_name,
                    "games_played": 0,
                    "wins": 0,
                    "losses": 0,
                    "total_kills": 0,
                    "total_deaths": 0,
                    "total_assists": 0,
                }

            stats = champion_data[champion_id]
            stats["games_played"] += 1
            stats["total_kills"] += participant.kills
            stats["total_deaths"] += participant.deaths
            stats["total_assists"] += participant.assists

            if participant.win:
                stats["wins"] += 1
            else:
                stats["losses"] += 1

        # Convert to ChampionStats objects
        champion_stats = []
        for champion_id, data in champion_data.items():
            champion_stat = ChampionStats(
                champion_id=champion_id,
                champion_name=data["champion_name"],
                games_played=data["games_played"],
                wins=data["wins"],
                losses=data["losses"],
                total_kills=data["total_kills"],
                total_deaths=data["total_deaths"],
                total_assists=data["total_assists"],
            )
            champion_stats.append(champion_stat)

        # Sort by games played (descending)
        champion_stats.sort(key=lambda x: x.games_played, reverse=True)
        return champion_stats

    def get_performance_stats(self) -> PerformanceStats:
        """
        Get recent performance summary for the player.

        Returns:
            PerformanceStats with comprehensive performance metrics

        """
        if not self:
            return PerformanceStats(
                total_games=0,
                wins=0,
                losses=0,
                win_rate=0.0,
                avg_kills=0.0,
                avg_deaths=0.0,
                avg_assists=0.0,
                avg_kda=0.0,
                avg_cs=0.0,
                avg_game_duration_minutes=0.0,
            )

        total_games = len(self)
        wins = 0
        total_kills = 0
        total_deaths = 0
        total_assists = 0
        total_cs = 0
        total_duration = 0

        for match in self:
            # Find the participant for this player
            participant = match.participants.by_puuid(self.puuid)

            if not participant:
                continue

            if participant.win:
                wins += 1

            total_kills += participant.kills
            total_deaths += participant.deaths
            total_assists += participant.assists
            total_cs += participant.total_minions_killed + participant.neutral_minions_killed
            total_duration += match.info.game_duration

        losses = total_games - wins
        win_rate = (wins / total_games) * 100.0 if total_games > 0 else 0.0
        avg_kills = total_kills / total_games if total_games > 0 else 0.0
        avg_deaths = total_deaths / total_games if total_games > 0 else 0.0
        avg_assists = total_assists / total_games if total_games > 0 else 0.0
        avg_kda = (total_kills + total_assists) / total_deaths if total_deaths > 0 else 0.0
        avg_cs = total_cs / total_games if total_games > 0 else 0.0
        avg_game_duration_minutes = (total_duration / 60) / total_games if total_games > 0 else 0.0

        return PerformanceStats(
            total_games=total_games,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            avg_kills=avg_kills,
            avg_deaths=avg_deaths,
            avg_assists=avg_assists,
            avg_kda=avg_kda,
            avg_cs=avg_cs,
            avg_game_duration_minutes=avg_game_duration_minutes,
        )

    def get_average_stat(
        self,
        stat_retriever: Callable[["Participant"], int | float],
    ) -> float:
        """
        Calculate the average of a specific statistic for the player across all matches.

        Args:
            stat_retriever: A lambda function that takes a Participant object
                            and returns the statistic to average.

        Returns:
            The average value of the statistic, or 0.0 if no matches are found.

        Example:
            # Get average gold per minute
            avg_gold_per_min = matches.get_average_stat(
                lambda p: p.challenges.gold_per_minute
            )

        """
        total_stat = 0.0
        games_counted = 0

        for match in self:
            participant = match.participants.by_puuid(self.puuid)
            if participant:
                total_stat += stat_retriever(participant)
                games_counted += 1

        if games_counted == 0:
            return 0.0

        return total_stat / games_counted

    def filter(self, predicate: Callable[["Match"], bool]) -> "MatchList":
        """
        Filter matches using a custom predicate function.

        Args:
            predicate: A function that takes a Match and returns True/False

        Returns:
            A new MatchList containing matches that match the predicate

        """
        return MatchList([p for p in self if predicate(p)], self.puuid)

    def sort_by(
        self,
        key: Callable[["Match"], Any],
        *,
        reverse: bool = False,
    ) -> "MatchList":
        """
        Sort matches by a custom key function.

        Args:
            key: A function that takes a Match and returns a sortable value
            reverse: Whether to sort in descending order

        Returns:
            A new MatchList with matches sorted by the key

        """
        return MatchList(sorted(self, key=key, reverse=reverse), self.puuid)

    @overload
    def __getitem__(self, key: SupportsIndex) -> "Match": ...

    @overload
    def __getitem__(self, key: slice) -> "MatchList": ...

    def __getitem__(self, key: SupportsIndex | slice) -> "Match | MatchList":
        result = super().__getitem__(key)
        if isinstance(key, slice):
            msg = "Slicing a MatchList did not return a list as expected."
            if not isinstance(result, list):
                raise TypeError(msg)
            return MatchList(result, self.puuid)
        # Defensive: ensure only a Match is returned for int
        if not isinstance(result, self._match_type()):
            msg = "Indexing a MatchList did not return a Match as expected."
            raise TypeError(msg)
        return cast("Match", result)

    @staticmethod
    def _match_type() -> type:
        from nexar.models.match.match import Match

        return Match
