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
    # Ensure all players have league entries loaded
    for player in players:
        await player.get_league_entries()

    async def get_rank_value(player: Player) -> int:
        """Get rank value for sorting, with unranked players getting -1."""
        if ranked_queue_type == QueueId.RANKED_SOLO_5x5:
            rank_value = await player.get_solo_rank_value()
        elif ranked_queue_type == QueueId.RANKED_FLEX_SR:
            flex_rank = await player.get_flex_rank()
            rank_value = flex_rank.rank_value if flex_rank else None
        else:
            msg = f"Invalid queue_type: {ranked_queue_type}. Must be QueueId.RANKED_SOLO_5x5 or QueueId.RANKED_FLEX_SR."
            raise ValueError(msg)

        return rank_value if rank_value is not None else -1

    # Create list of (player, rank_value) tuples for sorting
    players_with_ranks = []
    for player in players:
        rank_value = await get_rank_value(player)
        players_with_ranks.append((player, rank_value))

    # Sort by rank value
    players_with_ranks.sort(key=lambda x: x[1], reverse=descending)

    # Return just the players
    return [player for player, _ in players_with_ranks]
