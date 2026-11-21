"""Tests for platform service status (lol-status-v4)."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Region
from nexar.models import PlatformStatus, StatusContent, StatusEntry, StatusUpdate
from tests.helpers import register_exact_url

if TYPE_CHECKING:
    from aioresponses import aioresponses


def status_payload() -> dict[str, object]:
    """Platform-data in the recorded live shape (2026-11-21 NA1).

    One incident verbatim from the wire — explicit null timestamps (this op
    sends nulls instead of omitting values), a localized update, and an empty
    maintenances array. The locales list is trimmed; everything else is exact.
    """
    return {
        "id": "NA1",
        "name": "North America",
        "locales": ["en_US", "de_DE", "ja_JP"],
        "maintenances": [],
        "incidents": [
            {
                "id": 13878,
                "created_at": "2026-11-20T22:20:13.684894+00:00",
                "updated_at": None,
                "archive_at": None,
                "titles": [{"locale": "en_US", "content": "Facebook login Issues"}],
                "updates": [
                    {
                        "id": 24815,
                        "created_at": "2026-11-20T22:20:13.684894+00:00",
                        "updated_at": "2026-11-20T22:20:13+00:00",
                        "publish": True,
                        "author": "Riot Games",
                        "translations": [
                            {
                                "locale": "en_US",
                                "content": "Some players may be facing issues with login via Facebook.",
                            }
                        ],
                        "publish_locations": ["game", "riotclient", "riotstatus"],
                    }
                ],
                "platforms": ["android", "ios", "macos", "windows"],
                "incident_severity": "critical",
            }
        ],
    }


@pytest_asyncio.fixture
async def fresh_client() -> AsyncGenerator[NexarClient]:
    """Client with no conftest catch-alls, so the exact-URL registration is the only match."""
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
    yield client
    await client.close()


class TestPlatformStatusClient:
    """The platform-data op against an exact-URL registration (routing and path pinning)."""

    async def test_get_platform_status_parses_recorded_payload(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(
            mock_aioresponse,
            "https://na1.api.riotgames.com/lol/status/v4/platform-data",
            status_payload(),
        )

        status = await fresh_client.get_platform_status()

        assert status == PlatformStatus(
            id="NA1",
            name="North America",
            locales=("en_US", "de_DE", "ja_JP"),
            maintenances=(),
            incidents=(
                StatusEntry(
                    id=13878,
                    maintenance_status="",
                    incident_severity="critical",
                    titles=(StatusContent(locale="en_US", content="Facebook login Issues"),),
                    updates=(
                        StatusUpdate(
                            id=24815,
                            publish=True,
                            author="Riot Games",
                            publish_locations=("game", "riotclient", "riotstatus"),
                            translations=(
                                StatusContent(
                                    locale="en_US",
                                    content="Some players may be facing issues with login via Facebook.",
                                ),
                            ),
                            created_at=datetime(2026, 11, 20, 22, 20, 13, 684894, tzinfo=UTC),
                            updated_at=datetime(2026, 11, 20, 22, 20, 13, tzinfo=UTC),
                        ),
                    ),
                    platforms=("android", "ios", "macos", "windows"),
                    created_at=datetime(2026, 11, 20, 22, 20, 13, 684894, tzinfo=UTC),
                    archive_at=None,
                    updated_at=None,
                ),
            ),
        )


class TestPlatformStatusModels:
    """PlatformStatus parsing, including the null-timestamp and degradation paths."""

    def test_maintenance_entry_parses_its_own_field(self) -> None:
        """A maintenance carries maintenance_status and omits incident_severity."""
        entry = StatusEntry.from_api_response(
            {
                "id": 1,
                "maintenance_status": "in_progress",
                "titles": [],
                "updates": [],
                "platforms": ["windows"],
            },
        )

        assert entry.maintenance_status == "in_progress"
        assert entry.incident_severity == ""
        assert entry.platforms == ("windows",)
        assert entry.created_at is None

    def test_unparsable_timestamp_degrades_to_none(self) -> None:
        """Timestamps are display data: a bad string warns and stores None instead of raising."""
        entry = StatusEntry.from_api_response({"id": 2, "created_at": "not-a-timestamp"})

        assert entry.created_at is None

    def test_explicit_nulls_parse_like_absences(self) -> None:
        """The status op demonstrably sends nulls — every null field must parse to its empty value.

        ``.get(key, default)`` alone passes a null straight through (and
        ``tuple(None)`` raises), so the status models guard with ``or``.
        """
        status = PlatformStatus.from_api_response(
            {
                "id": "NA1",
                "name": None,
                "locales": None,
                "maintenances": None,
                "incidents": [
                    {
                        "id": None,
                        "maintenance_status": None,
                        "incident_severity": None,
                        "titles": None,
                        "updates": None,
                        "platforms": None,
                        "created_at": None,
                        "archive_at": None,
                        "updated_at": None,
                    }
                ],
            },
        )

        assert status == PlatformStatus(
            id="NA1",
            name="",
            locales=(),
            maintenances=(),
            incidents=(
                StatusEntry(
                    id=0,
                    maintenance_status="",
                    incident_severity="",
                    titles=(),
                    updates=(),
                    platforms=(),
                    created_at=None,
                    archive_at=None,
                    updated_at=None,
                ),
            ),
        )

    def test_explicit_null_update_fields_parse_like_absences(self) -> None:
        update = StatusUpdate.from_api_response(
            {"id": None, "publish": None, "author": None, "publish_locations": None, "translations": None},
        )

        assert update == StatusUpdate(
            id=0,
            publish=False,
            author="",
            publish_locations=(),
            translations=(),
            created_at=None,
            updated_at=None,
        )

    def test_empty_payload_parses_empty(self) -> None:
        status = PlatformStatus.from_api_response({})

        assert status == PlatformStatus(id="", name="", locales=(), maintenances=(), incidents=())


class TestLiveStatusCanary:
    """Live canary: the platform-data op against the real API."""

    @pytest.mark.slow
    async def test_live_platform_status_reports_the_platform(self, real_client: NexarClient) -> None:
        status = await real_client.get_platform_status()

        assert status.id == "NA1"
        assert status.name == "North America"
        for entry in (*status.maintenances, *status.incidents):
            assert isinstance(entry.id, int)
            assert entry.platforms
