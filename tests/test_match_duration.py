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


class TestGameDurationNormalization:
    """MatchInfo.game_duration is always expressed in seconds."""

    def test_pre_11_20_milliseconds_are_converted_to_seconds(self) -> None:
        """A 30-minute pre-11.20 match stored in milliseconds parses to 1800 seconds."""
        info = MatchInfo.from_api_response(
            info_payload(gameVersion="11.19.1.1", gameDuration=1_800_000),
        )
        assert info.game_duration == 1800

    def test_pre_11_20_sub_minor_versions_are_not_string_compared(self) -> None:
        """11.9 predates 11.20 numerically even though '11.9' > '11.20' as a string."""
        info = MatchInfo.from_api_response(
            info_payload(gameVersion="11.9.1.1", gameDuration=1_500_000),
        )
        assert info.game_duration == 1500

    def test_pre_11_20_two_part_version_is_normalized(self) -> None:
        """Versions without the build segments (e.g. '10.10') still normalize."""
        info = MatchInfo.from_api_response(
            info_payload(gameVersion="10.10", gameDuration=1_200_000),
        )
        assert info.game_duration == 1200

    def test_11_20_boundary_is_already_seconds(self) -> None:
        """11.20 is the first patch reporting seconds, so the value is untouched."""
        info = MatchInfo.from_api_response(
            info_payload(gameVersion="11.20.1.1", gameDuration=1800),
        )
        assert info.game_duration == 1800

    def test_modern_seconds_are_left_unchanged(self) -> None:
        """Post-11.20 matches keep the raw seconds value."""
        info = MatchInfo.from_api_response(
            info_payload(gameVersion="15.1.615.9282", gameDuration=2200),
        )
        assert info.game_duration == 2200

    def test_unparseable_game_version_leaves_duration_untouched(self) -> None:
        """An unrecognized version is treated as unknown: raw value preserved."""
        info = MatchInfo.from_api_response(
            info_payload(gameVersion="unknown", gameDuration=1800),
        )
        assert info.game_duration == 1800

    def test_empty_game_version_leaves_duration_untouched(self) -> None:
        """An empty version string is treated as unknown: raw value preserved."""
        info = MatchInfo.from_api_response(
            info_payload(gameVersion="", gameDuration=1800),
        )
        assert info.game_duration == 1800

    def test_missing_game_version_still_raises_key_error(self) -> None:
        """The ``gameVersion`` field stays required; its absence is not silently defaulted."""
        payload = info_payload()
        del payload["gameVersion"]
        with pytest.raises(KeyError):
            MatchInfo.from_api_response(payload)
