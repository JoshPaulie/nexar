"""Utility functions for working with Nexar models."""

from __future__ import annotations

import asyncio
from dataclasses import fields, is_dataclass
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from nexar.enums import Queue

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from nexar.models import Participant, ParticipantList
    from nexar.models.league import LeagueEntry
    from nexar.models.player import Player


__all__ = [
    "cs_per_min",
    "sort_players_by_rank",
    "team_total_percentage",
    "to_dict",
]


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
        sorted_players = await sort_players_by_rank(players, descending=False, ranked_queue_type=Queue.RANKED_FLEX_SR)
        ```

    """
    if ranked_queue_type == Queue.RANKED_SOLO_5x5:

        async def getter(p: Player) -> LeagueEntry | None:
            return await p.get_solo_rank()
    elif ranked_queue_type == Queue.RANKED_FLEX_SR:

        async def getter(p: Player) -> LeagueEntry | None:
            return await p.get_flex_rank()
    else:
        msg = f"Invalid ranked_queue_type: {ranked_queue_type}. Must be Queue.RANKED_SOLO_5x5 or Queue.RANKED_FLEX_SR."
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


def cs_per_min(participant: Participant, duration_s: float) -> float:
    """
    Creep score per minute for one participant.

    Creep score counts lane minions plus neutral monsters,
    [`Participant.creep_score`][nexar.models.match.participant.Participant.creep_score].

    Args:
        participant: The participant to measure.
        duration_s: Match length in seconds, from
            [`MatchInfo.game_duration`][nexar.models.match.match.MatchInfo.game_duration].

    Returns:
        Creeps divided by the match length in minutes, or 0.0 when
        ``duration_s`` is not positive.

    Example:
        ```
        from nexar.utils import cs_per_min
        match = await client.get_match(match_id)
        participant = match.info.participants[0]
        print(f"{cs_per_min(participant, match.info.game_duration):.1f} CS/min")
        ```

    """
    if duration_s <= 0:
        return 0.0
    return participant.creep_score / (duration_s / 60)


def to_dict(model: object) -> dict[str, Any]:
    """
    Convert a model into JSON-safe primitives.

    Nested dataclasses become nested dicts, list subclasses become lists,
    enums become their wire values (``MatchParticipantPosition.UTILITY`` is
    ``"UTILITY"``, not the display label ``"Utility"``), and datetimes become
    ISO 8601 strings. The result passes ``json.dumps`` unchanged.

    Args:
        model: A dataclass instance from the model tree (Match, Participant,
            Timeline, LeagueEntry, ...).

    Returns:
        A dict of plain Python values: dict, list, str, int, float, bool, None.

    Raises:
        TypeError: If ``model`` is not a dataclass instance.

    Example:
        ```
        import json

        from nexar.utils import to_dict
        match = await client.get_match(match_id)
        print(json.dumps(to_dict(match))[:200])
        ```

    """
    if isinstance(model, type) or not is_dataclass(model):
        msg = f"to_dict() needs a dataclass instance, got {type(model).__name__}"
        raise TypeError(msg)
    return {field.name: _jsonable(getattr(model, field.name)) for field in fields(model)}


def _jsonable(value: object) -> object:
    """Recursively convert one model value into a JSON-safe primitive."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, date | datetime):
        return value.isoformat()
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _jsonable(getattr(value, field.name)) for field in fields(value)}
    return value
