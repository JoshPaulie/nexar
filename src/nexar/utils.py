"""Utility functions for working with Nexar models."""

from collections.abc import Callable, Sequence
from typing import Any

from nexar.models.player import Player


def sort_players(
    players: Sequence[Player],
    key: Callable[[Player], Any] | str,
    descending: bool = True,
) -> list[Player]:
    """
    Return a list of Player objects sorted by a given property or function.

    Args:
        players: Sequence of Player objects
        key: Function (recommended, for autocomplete/type safety) or property name (str, discouraged)
        descending: If True (default), highest value first. If False, lowest first.

    Returns:
        List of Player objects sorted by the given key (None/False/empty last).

    Note:
        For best developer experience, pass a lambda or method reference for `key` (e.g., `key=lambda p: p.solo_rank_value`).
        Passing a string disables autocomplete and type checking.

    Examples:
        from nexar.utils import sort_players
        sorted_players = sort_players(players, key=lambda p: p.solo_rank_value)
        sorted_players = sort_players(players, key=lambda p: p.wins, descending=False)
        # Discouraged: string disables autocomplete
        sorted_players = sort_players(players, key="solo_rank_value")

    """

    def get_value(p: Player) -> Any:
        if isinstance(key, str):
            value = getattr(p, key, None)
        else:
            value = key(p)
        return value if value is not None else -1

    return sorted(
        players,
        key=get_value,
        reverse=descending,
    )


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
