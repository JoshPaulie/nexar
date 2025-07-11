"""Specialized list class for working with match participants."""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, SupportsIndex, cast, overload

if TYPE_CHECKING:
    from .participant import Participant

from nexar.enums import MatchParticipantPosition


class ParticipantList(list["Participant"]):
    """
    A specialized list for match participants with ergonomic filtering methods.

    Extends the built-in list while providing convenient methods for common
    participant queries and filters.
    """

    def by_puuid(self, puuid: str) -> "Participant | None":
        """
        Find a participant by their PUUID.

        Args:
            puuid: The player's universally unique identifier

        Returns:
            The participant with the matching PUUID, or None if not found

        """
        return next((p for p in self if p.puuid == puuid), None)

    def by_champion(self, champion_name: str) -> "ParticipantList":
        """
        Filter participants by champion name.

        Args:
            champion_name: The champion name (case-insensitive)

        Returns:
            A new ParticipantList containing participants playing the specified champion

        """
        return ParticipantList(p for p in self if p.champion_name.lower() == champion_name.lower())

    def by_position(self, position: MatchParticipantPosition) -> "ParticipantList":
        """
        Filter participants by their team position.

        Args:
            position: The position to filter by

        Returns:
            A new ParticipantList containing participants in the specified position

        """
        return ParticipantList(p for p in self if p.team_position == position)

    def by_team(self, team_id: int) -> "ParticipantList":
        """
        Filter participants by team ID.

        Args:
            team_id: The team ID (100 for blue, 200 for red)

        Returns:
            A new ParticipantList containing participants on the specified team

        """
        return ParticipantList(p for p in self if p.team_id == team_id)

    def blue_team(self) -> "ParticipantList":
        """
        Get all participants on the blue team.

        Returns:
            A new ParticipantList containing blue team participants

        """
        return self.by_team(100)

    def red_team(self) -> "ParticipantList":
        """
        Get all participants on the red team.

        Returns:
            A new ParticipantList containing red team participants

        """
        return self.by_team(200)

    def winners(self) -> "ParticipantList":
        """
        Get all participants who won the match.

        Returns:
            A new ParticipantList containing winning participants

        """
        return ParticipantList(p for p in self if p.win)

    def losers(self) -> "ParticipantList":
        """
        Get all participants who lost the match.

        Returns:
            A new ParticipantList containing losing participants

        """
        return ParticipantList(p for p in self if not p.win)

    def team_of(self, puuid: str) -> "ParticipantList":
        """
        Get the team of the participant with the given PUUID.

        Args:
            puuid: The player's universally unique identifier

        Returns:
            A ParticipantList containing all participants on the same team as the specified PUUID.

        Raises:
            ValueError: If no participant with the given PUUID is found.

        """
        participant = self.by_puuid(puuid)
        if participant is None:
            msg = f"No participant found with PUUID: {puuid}"
            raise ValueError(msg)
        return self.by_team(participant.team_id)

    def filter(self, predicate: Callable[["Participant"], bool]) -> "ParticipantList":
        """
        Filter participants using a custom predicate function.

        Args:
            predicate: A function that takes a Participant and returns True/False

        Returns:
            A new ParticipantList containing participants that match the predicate

        """
        return ParticipantList(p for p in self if predicate(p))

    def sort_by(
        self,
        key: Callable[["Participant"], Any],
        *,
        reverse: bool = False,
    ) -> "ParticipantList":
        """
        Sort participants by a custom key function.

        Args:
            key: A function that takes a Participant and returns a sortable value
            reverse: Whether to sort in descending order

        Returns:
            A new ParticipantList with participants sorted by the key

        """
        return ParticipantList(sorted(self, key=key, reverse=reverse))

    def highest_kda(self, count: int = 1) -> "ParticipantList":
        """
        Get participants with the highest KDA ratios.

        Args:
            count: Number of top participants to return

        Returns:
            A new ParticipantList with the highest KDA participants

        """

        def kda_ratio(participant: "Participant") -> float:
            if participant.deaths == 0:
                return float(participant.kills + participant.assists)
            return (participant.kills + participant.assists) / participant.deaths

        return ParticipantList(self.sort_by(kda_ratio, reverse=True)[:count])

    def most_kills(self, count: int = 1) -> "ParticipantList":
        """
        Get participants with the most kills.

        Args:
            count: Number of top participants to return

        Returns:
            A new ParticipantList with the most kills

        """
        return ParticipantList(self.sort_by(lambda p: p.kills, reverse=True)[:count])

    def most_damage(self, count: int = 1) -> "ParticipantList":
        """
        Get participants who dealt the most damage to champions.

        Args:
            count: Number of top participants to return

        Returns:
            A new ParticipantList with the highest damage dealers

        """
        return ParticipantList(self.sort_by(lambda p: p.total_damage_dealt_to_champions, reverse=True)[:count])

    @overload
    def __getitem__(self, key: SupportsIndex) -> "Participant": ...

    @overload
    def __getitem__(self, key: slice) -> "ParticipantList": ...

    def __getitem__(self, key: SupportsIndex | slice) -> "Participant | ParticipantList":
        result = super().__getitem__(key)
        if isinstance(key, slice):
            msg = "Slicing a ParticipantList did not return a list as expected."
            if not isinstance(result, list):
                raise TypeError(msg)
            return ParticipantList(result)
        # Defensive: ensure only a Participant is returned for int
        if not isinstance(result, self._participant_type()):
            msg = "Indexing a ParticipantList did not return a Participant as expected."
            raise TypeError(msg)
        return cast("Participant", result)

    @staticmethod
    def _participant_type() -> type:
        from .participant import Participant

        return Participant
