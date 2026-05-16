"""Utility functions for working with Nexar models."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from nexar.enums import Queue

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from nexar.models import Participant, ParticipantList
    from nexar.models.league import LeagueEntry
    from nexar.models.player import Player


async def sort_players_by_rank(
    players: Sequence[Player],
    *,
    descending: bool = True,
    ranked_queue_type: Queue = Queue.RANKED_SOLO_5x5,
) -> list[Player]:
    """
    Return a list of Player objects sorted by their ranked queue rank.

    This function will automatically fetch league entries for each player if not already loaded.

    Args:
        players: Sequence of Player objects
        descending: If True (default), highest rank first. If False, lowest first.
        ranked_queue_type: Queue.RANKED_SOLO_5x5 or RANKED_FLEX_SR

    Returns:
        List of Player objects sorted by rank (unranked players last).

    Example:
        ```
        from nexar.utils import sort_players_by_rank
        # Sort by flex queue rank (lowest first)
        sorted_players = await sort_players_by_rank(players, descending=False, queue_type=Queue.RANKED_FLEX_SR)
        ```

    """
    if ranked_queue_type == Queue.RANKED_SOLO_5x5:

        async def getter(p: Player) -> LeagueEntry | None:
            return await p.get_solo_rank()
    elif ranked_queue_type == Queue.RANKED_FLEX_SR:

        async def getter(p: Player) -> LeagueEntry | None:
            return await p.get_flex_rank()
    else:
        msg = f"Invalid queue_type: {ranked_queue_type}. Must be Queue.RANKED_SOLO_5x5 or Queue.RANKED_FLEX_SR."
        raise ValueError(msg)

    league_entries = await asyncio.gather(*(getter(p) for p in players))

    players_with_ranks = list(zip(players, league_entries, strict=False))

    # Separate ranked and unranked players
    ranked = [(p, e) for p, e in players_with_ranks if e is not None]
    unranked = [p for p, e in players_with_ranks if e is None]

    ranked.sort(key=lambda x: x[1], reverse=descending)

    return [p for p, _ in ranked] + unranked


def team_total_percentage(
    participants: ParticipantList,
    target_participant: Participant,
    stat_selector: Callable[[Participant], int | float],
) -> float:
    """
    Calculate the percentage of a specific stat for a participant relative to their team's total for that stat.

    Args:
        participants: List of all participants in the match.
        target_participant: The participant for whom to calculate the percentage.
        stat_selector: Lambda expression that takes a Participant and returns the specific stat to calculate

    Returns:
        The percentage of the stat for the target participant relative to their team's total for that stat.

    Example:
        ```
        from nexar.utils import team_total_percentage
        # Calculate the percentage of total team damage dealt by a participant
        total_damage = team_total_percentage(
            participants,
            target_participant,
            lambda p: p.total_damage_dealt_to_champions,
        )
        ```

    """
    if participants.by_puuid(target_participant.puuid) is None:
        msg = f"Participant with PUUID '{target_participant.puuid}' not found in the provided ParticipantList."
        raise ValueError(msg)

    total_stat_by_team = sum([stat_selector(p) for p in participants.by_team(target_participant.team_id)])
    if total_stat_by_team == 0:
        return 0.0
    return stat_selector(target_participant) / total_stat_by_team * 100
