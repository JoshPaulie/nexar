"""Utility functions for working with Nexar models."""

from collections.abc import Sequence

from nexar.models.player import Player


def sort_players_by_solo_queue_rank(
    players: Sequence[Player], descending: bool = True
) -> list[Player]:
    """
    Return a list of Player objects sorted by solo queue rank.

    Args:
        players: Sequence of Player objects
        descending: If True (default), highest rank first. If False, lowest rank first.

    Returns:
        List of Player objects sorted by solo queue rank (unranked last).
    """
    return sorted(
        players,
        key=lambda p: p.solo_rank_value or -1,
        reverse=descending,
    )
