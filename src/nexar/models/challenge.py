"""LoL challenge system models (lol-challenges-v1).

Distinct from :mod:`nexar.models.match.challenges`, which holds the per-match
challenge stats inside a match payload — those are ``Challenges``; everything
here is the account-wide challenge system (``ChallengeConfig`` and friends).
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class LocalizedChallengeNames:
    """One locale's name, description, and short description for a challenge.

    The locale map carries 28 locales on the live wire (2026-11-21 NA1); the
    long-form ``description`` is usually empty and the client shows the short
    one — both parse regardless.
    """

    name: str
    """Display name of the challenge in this locale."""

    description: str
    """Long-form description; empty on the wire for most challenges."""

    short_description: str
    """Short-form description, the one clients display."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "LocalizedChallengeNames":
        """Create LocalizedChallengeNames from API response."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            short_description=data.get("shortDescription", ""),
        )


@dataclass(frozen=True)
class ChallengeConfig:
    """One challenge's configuration, from the config family of ops.

    The live wire sends ``id``, ``localizedNames``, ``state``, ``leaderboard``,
    and ``thresholds`` on every entry (measured 2026-11-21 NA1, 405
    challenges), plus ``endTimestamp`` on exactly one — challenge 600012, a
    launch-window challenge the catalog still serves. The reference DTO
    table's ``tracking`` and ``startTimestamp`` never appear on the wire.
    """

    id: int
    """Challenge identifier."""

    localized_names: dict[str, LocalizedChallengeNames]
    """Per-locale display strings, keyed like 'en_US'."""

    state: str
    """One of Riot's documented states: DISABLED, HIDDEN, ENABLED, ARCHIVED."""

    leaderboard: bool
    """Whether this challenge has leaderboards at all."""

    thresholds: dict[str, float]
    """Tier name to the value needed to reach it, e.g. ``{"IRON": 1.0}``.

    Only the tiers a challenge can reach appear (some cap below CHALLENGER).
    """

    end_timestamp: datetime | None
    """When a time-limited challenge ends, or None on open-ended challenges —
    the catalog carries this on exactly one entry (measured 2026-11-21)."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ChallengeConfig":
        """Create ChallengeConfig from API response.

        Riot omits empty values, so everything except ``id`` parses with
        defaults.
        """
        localized_raw = data.get("localizedNames") or {}
        end_ms = data.get("endTimestamp")
        return cls(
            id=data["id"],
            localized_names={
                locale: LocalizedChallengeNames.from_api_response(names) for locale, names in localized_raw.items()
            },
            state=data.get("state") or "",
            leaderboard=data.get("leaderboard", False),
            thresholds=dict(data.get("thresholds") or {}),
            end_timestamp=datetime.fromtimestamp(end_ms / 1000, tz=UTC) if end_ms else None,
        )


@dataclass(frozen=True)
class ChallengeLeaderboardEntry:
    """One player's row on a challenge leaderboard."""

    puuid: str
    """Player's universally unique identifier."""

    value: float
    """The player's challenge value (their standing basis)."""

    position: int
    """The player's position in the challenge's ladder.

    Positions are global across the challenge's tiers — the MASTER board for
    the CRYSTAL challenge starts at 58, with positions 1-57 belonging to the
    tiers above (measured 2026-11-21 NA1). Zero means not placed, when Riot
    omits the field entirely.
    """

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ChallengeLeaderboardEntry":
        """Create ChallengeLeaderboardEntry from API response."""
        return cls(
            puuid=data["puuid"],
            value=data.get("value", 0.0),
            position=data.get("position", 0),
        )


@dataclass(frozen=True)
class ChallengePoints:
    """Challenge points for a total or one category.

    The wire spells the percentile key ``percentile`` (measured 2026-11-21);
    the reference DTO table's ``precentile`` is a documentation typo.
    """

    level: str
    """Tier name reached with these points (e.g. 'DIAMOND')."""

    current: int
    """Points earned so far."""

    max: int
    """Points needed for the next tier."""

    percentile: float
    """Fraction of players below this points level, 0.0 to 1.0."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ChallengePoints":
        """Create ChallengePoints from API response."""
        return cls(
            level=data.get("level") or "NONE",
            current=data.get("current", 0),
            max=data.get("max", 0),
            percentile=data.get("percentile", 0.0),
        )


@dataclass(frozen=True)
class ChallengePreferences:
    """The player's client-side challenge customization."""

    banner_accent: str
    """Selected banner accent identifier."""

    title: str
    """Selected challenge title identifier (a challengeId as a string)."""

    challenge_ids: tuple[int, ...]
    """Challenge IDs the player has pinned/selected."""

    crest_border: str
    """Selected crest border identifier."""

    prestige_crest_border_level: int
    """Level of the prestige crest border the player has unlocked."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ChallengePreferences":
        """Create ChallengePreferences from API response."""
        return cls(
            banner_accent=data.get("bannerAccent") or "",
            title=data.get("title") or "",
            challenge_ids=tuple(data.get("challengeIds") or ()),
            crest_border=data.get("crestBorder") or "",
            prestige_crest_border_level=data.get("prestigeCrestBorderLevel", 0),
        )


@dataclass(frozen=True)
class ChallengeProgress:
    """One challenge's progress for a player, from player-data.

    The wire sends three key shapes (measured 2026-11-21 NA1): fully placed
    rows carry ``position`` and ``playersInLevel``, progressed rows carry
    ``achievedTime``, and untouched challenges carry neither — ``level`` is
    'NONE' with a percentile of 1.0.
    """

    challenge_id: int
    """Challenge identifier."""

    percentile: float
    """Fraction of players below this player's value, 0.0 to 1.0."""

    level: str
    """Tier name reached on this challenge (e.g. 'DIAMOND', or 'NONE')."""

    value: float
    """The player's current challenge value."""

    achieved_time: datetime | None
    """When the current tier was reached, or None when the tier has not been
    reached at all."""

    players_in_level: int
    """How many players share this tier; 0 when the tier has no board."""

    position: int
    """The player's global position on this challenge; 0 when unplaced."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "ChallengeProgress":
        """Create ChallengeProgress from API response.

        Riot omits empty values, so everything except ``challenge_id``
        parses with defaults; ``achievedTime`` is epoch milliseconds.
        """
        achieved_ms = data.get("achievedTime")
        return cls(
            challenge_id=data["challengeId"],
            percentile=data.get("percentile", 0.0),
            level=data.get("level") or "NONE",
            value=data.get("value", 0.0),
            achieved_time=(datetime.fromtimestamp(achieved_ms / 1000, tz=UTC) if achieved_ms is not None else None),
            players_in_level=data.get("playersInLevel", 0),
            position=data.get("position", 0),
        )


@dataclass(frozen=True)
class PlayerChallengeData:
    """A player's standing in the account-wide challenge system.

    From the player-data op: every challenge with progress, the point totals
    per category, and the player's client-side challenge customization.
    """

    challenges: tuple[ChallengeProgress, ...]
    """Per-challenge progress rows (343 on the recording player, 2026-11-21)."""

    preferences: ChallengePreferences | None
    """The player's challenge customization, or None when Riot omits it."""

    total_points: ChallengePoints | None
    """Points across every category, or None when Riot omits it."""

    category_points: dict[str, ChallengePoints]
    """Points per challenge category (IMAGINATION, TEAMWORK, EXPERTISE,
    VETERANCY, COLLECTION on the live wire)."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "PlayerChallengeData":
        """Create PlayerChallengeData from API response.

        Riot omits empty values, so containers parse empty and the two
        singletons parse to None rather than raising.
        """
        preferences = data.get("preferences")
        total_points = data.get("totalPoints")
        category_raw = data.get("categoryPoints") or {}
        return cls(
            challenges=tuple(ChallengeProgress.from_api_response(entry) for entry in data.get("challenges") or ()),
            preferences=ChallengePreferences.from_api_response(preferences) if preferences else None,
            total_points=ChallengePoints.from_api_response(total_points) if total_points else None,
            category_points={
                category: ChallengePoints.from_api_response(points) for category, points in category_raw.items()
            },
        )
