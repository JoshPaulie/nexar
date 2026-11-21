"""LoL platform service status models (lol-status-v4)."""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger("nexar")


def _parse_timestamp(value: object) -> datetime | None:
    """Parse an ISO-8601 status timestamp; null, absent, or unparsable values become None.

    The status op sends explicit nulls (``"updated_at": null``) and ISO strings
    with a UTC offset — unlike most Riot ops, which omit empty values instead.
    An unparsable string degrades to None with a warning rather than aborting
    the parse; timestamps are display data, not identity.
    """
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        logger.warning("Unparsable status timestamp %r. Storing None.", value)
        return None


@dataclass(frozen=True)
class StatusContent:
    """A localized status string — used for incident/maintenance titles and update translations."""

    locale: str
    """Locale tag for this string (e.g. 'en_US')."""

    content: str
    """The localized text."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "StatusContent":
        """Create StatusContent from an API response."""
        return cls(
            locale=data.get("locale") or "",
            content=data.get("content") or "",
        )


@dataclass(frozen=True)
class StatusUpdate:
    """A single update posted under a maintenance or incident."""

    id: int
    """Update identifier."""

    publish: bool
    """Whether the update is published."""

    author: str
    """Who posted the update (e.g. 'Riot Games')."""

    publish_locations: tuple[str, ...]
    """Surfaces the update appears on (e.g. 'game', 'riotclient', 'riotstatus')."""

    translations: tuple[StatusContent, ...]
    """Localized update texts, one per locale."""

    created_at: datetime | None
    """When the update was posted, or None when Riot sends null/omits it."""

    updated_at: datetime | None
    """When the update was last edited, or None when Riot sends null/omits it."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "StatusUpdate":
        """Create StatusUpdate from an API response.

        This op sends explicit nulls, so every field is guarded against a null
        value — ``.get(key, default)`` alone would pass the null straight
        through into a non-optional field.
        """
        return cls(
            id=data.get("id") or 0,
            publish=data.get("publish") or False,
            author=data.get("author") or "",
            publish_locations=tuple(data.get("publish_locations") or ()),
            translations=tuple(StatusContent.from_api_response(t) for t in (data.get("translations") or ())),
            created_at=_parse_timestamp(data.get("created_at")),
            updated_at=_parse_timestamp(data.get("updated_at")),
        )


@dataclass(frozen=True)
class StatusEntry:
    """A maintenance or incident on a platform.

    The same shape serves both collections on the platform-data payload:
    maintenances carry ``maintenance_status`` ('scheduled', 'in_progress',
    'complete'), incidents carry ``incident_severity`` ('info', 'warning',
    'critical'); each omits the other's field, so both parse with defaults.
    """

    id: int
    """Entry identifier."""

    maintenance_status: str
    """Maintenance phase; empty on incidents."""

    incident_severity: str
    """Incident severity; empty on maintenances."""

    titles: tuple[StatusContent, ...]
    """Localized titles for this entry."""

    updates: tuple[StatusUpdate, ...]
    """Updates posted under this entry, in the order Riot returns them (only
    single-update incidents have been observed on the wire)."""

    platforms: tuple[str, ...]
    """Platforms affected (e.g. 'windows', 'macos', 'android', 'ios')."""

    created_at: datetime | None
    """When the entry was created, or None when Riot sends null/omits it."""

    archive_at: datetime | None
    """When the entry was archived, or None while it is active."""

    updated_at: datetime | None
    """When the entry was last updated, or None when Riot sends null/omits it."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "StatusEntry":
        """Create StatusEntry from an API response (nulls and absences parse the same)."""
        return cls(
            id=data.get("id") or 0,
            maintenance_status=data.get("maintenance_status") or "",
            incident_severity=data.get("incident_severity") or "",
            titles=tuple(StatusContent.from_api_response(t) for t in (data.get("titles") or ())),
            updates=tuple(StatusUpdate.from_api_response(u) for u in (data.get("updates") or ())),
            platforms=tuple(data.get("platforms") or ()),
            created_at=_parse_timestamp(data.get("created_at")),
            archive_at=_parse_timestamp(data.get("archive_at")),
            updated_at=_parse_timestamp(data.get("updated_at")),
        )


@dataclass(frozen=True)
class PlatformStatus:
    """Service status for one platform (lol-status-v4 platform-data).

    ``maintenances`` and ``incidents`` are usually empty — the value of this op
    is checking before a debug session that the platform itself is healthy.
    """

    id: str
    """Platform identifier (e.g. 'NA1')."""

    name: str
    """Human-readable platform name (e.g. 'North America')."""

    locales: tuple[str, ...]
    """Locale tags the platform's status messages come in."""

    maintenances: tuple[StatusEntry, ...]
    """Scheduled and in-progress maintenances."""

    incidents: tuple[StatusEntry, ...]
    """Active incidents."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "PlatformStatus":
        """Create PlatformStatus from an API response (nulls and absences parse the same)."""
        return cls(
            id=data.get("id") or "",
            name=data.get("name") or "",
            locales=tuple(data.get("locales") or ()),
            maintenances=tuple(StatusEntry.from_api_response(m) for m in (data.get("maintenances") or ())),
            incidents=tuple(StatusEntry.from_api_response(i) for i in (data.get("incidents") or ())),
        )
