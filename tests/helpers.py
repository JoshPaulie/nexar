"""Shared test helpers for the Nexar test suite.

Wire-payload and model-factory families live in ``payloads/``, split by
family; this module re-exports them so every test keeps importing from
``tests.helpers``.
"""

from aioresponses import aioresponses

from .payloads.mastery import champion_mastery_payload
from .payloads.match import (
    create_test_match,
    create_test_participant,
    match_response_payload,
)
from .payloads.timeline import timeline_response_payload

__all__ = [
    "champion_mastery_payload",
    "create_test_match",
    "create_test_participant",
    "match_response_payload",
    "register_exact_url",
    "timeline_response_payload",
]


def register_exact_url(
    mock: aioresponses,
    url: str,
    payload: object,
    *,
    repeat: bool = False,
    status: int = 200,
) -> None:
    """Register a payload for one exact URL — the registration style for parameter-sensitive tests.

    A literal URL makes aioresponses match the full query string, so a dropped or
    mangled request parameter fails the request instead of silently serving the
    canned payload to any matching URL.
    """
    mock.get(url, payload=payload, status=status, repeat=repeat)
