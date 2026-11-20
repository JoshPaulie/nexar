"""Tests for gameDuration normalization across the 11.20 unit change.

Riot's match-v5 ``gameDuration`` field is milliseconds before patch 11.20 and
seconds from 11.20 onwards. ``MatchInfo`` normalizes both to seconds at parse
time so downstream consumers (average duration, per-minute rates) never have to
know which era a match came from.
"""

from typing import Any

import pytest

from nexar.models.match.match import MatchInfo


def info_payload(**overrides: object) -> dict[str, Any]:
    """Build a minimal match-v5 ``info`` payload, overridable per test."""
    payload: dict[str, Any] = {
        "gameCreation": 1600000000000,
        "gameDuration": 1800,
        "gameId": 4500000001,
        "gameMode": "CLASSIC",
        "gameStartTimestamp": 1600000000000,
        "gameType": "MATCHED_GAME",
        "gameVersion": "14.23.654.12",
        "mapId": 11,
        "participants": [],
        "platformId": "NA1",
        "queueId": 420,
        "teams": [],
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize(
    ("game_version", "raw_duration", "expected"),
    [
        ("11.19.1.1", 1_800_000, 1800),
        ("11.9.1.1", 1_500_000, 1500),
        ("10.10", 1_200_000, 1200),
        ("11.20.1.1", 1800, 1800),
        ("15.1.615.9282", 2200, 2200),
        ("unknown", 1800, 1800),
        ("", 1800, 1800),
    ],
    ids=[
        "pre-11-20-milliseconds",
        "pre-11-20-sub-minor-numeric",
        "pre-11-20-two-part-version",
        "11-20-boundary-seconds",
        "modern-seconds",
        "unparseable-version",
        "empty-version",
    ],
)
def test_game_duration_normalized_to_seconds(game_version: str, raw_duration: int, expected: int) -> None:
    """MatchInfo.game_duration is always expressed in seconds, per the version era."""
    info = MatchInfo.from_api_response(
        info_payload(gameVersion=game_version, gameDuration=raw_duration),
    )
    assert info.game_duration == expected


def test_missing_game_version_still_raises_key_error() -> None:
    """The ``gameVersion`` field stays required; its absence is not silently defaulted."""
    payload = info_payload()
    del payload["gameVersion"]
    with pytest.raises(KeyError):
        MatchInfo.from_api_response(payload)
