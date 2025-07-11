"""Utility functions for working with Nexar models."""

from collections.abc import Sequence

from nexar.enums import QueueId
from nexar.models.player import Player


async def sort_players_by_rank(
    players: Sequence[Player],
    *,
    descending: bool = True,
    ranked_queue_type: QueueId = QueueId.RANKED_SOLO_5x5,
) -> list[Player]:
    """
    Return a list of Player objects sorted by their ranked queue rank.

    This function will automatically fetch league entries for each player if not already loaded.

    Args:
        players: Sequence of Player objects
        descending: If True (default), highest rank first. If False, lowest first.
        ranked_queue_type: QueueID.RANKED_SOLO_5x5 or RANKED_FLEX_SR

    Returns:
        List of Player objects sorted by rank (unranked players last).

    Examples:
        from nexar.utils import sort_players_by_rank
        # Sort by flex queue rank (lowest first)
        sorted_players = await sort_players_by_rank(players, descending=False, queue_type=QueueId.RANKED_FLEX_SR)

    """
    from nexar.models.league import LeagueEntry

    async def get_league_entry(player: Player) -> LeagueEntry | None:
        """Get the league entry for the specified queue type."""
        if ranked_queue_type == QueueId.RANKED_SOLO_5x5:
            return await player.get_solo_rank()
        if ranked_queue_type == QueueId.RANKED_FLEX_SR:
            return await player.get_flex_rank()

        msg = f"Invalid queue_type: {ranked_queue_type}. Must be QueueId.RANKED_SOLO_5x5 or QueueId.RANKED_FLEX_SR."
        raise ValueError(msg)

    # Create list of (player, league_entry) tuples for sorting
    players_with_ranks = []
    for player in players:
        league_entry = await get_league_entry(player)
        players_with_ranks.append((player, league_entry))

    # Separate ranked and unranked players
    ranked_players = [(player, league_entry) for player, league_entry in players_with_ranks if league_entry is not None]
    unranked_players = [player for player, league_entry in players_with_ranks if league_entry is None]

    # Sort ranked players by their league entry (LeagueEntry objects are directly comparable)
    ranked_players.sort(key=lambda x: x[1], reverse=descending)

    # Combine: ranked players first, then unranked players
    return [player for player, _ in ranked_players] + unranked_players
