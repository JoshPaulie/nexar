"""Tests for the match timeline client method and models."""

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
import pytest_asyncio

from nexar.cache import NO_CACHE_CONFIG
from nexar.client import NexarClient
from nexar.enums import Queue, Region
from nexar.exceptions import NotFoundError
from nexar.models.match.timeline import (
    Timeline,
    TimelineChampionStats,
    TimelineDamageStats,
    TimelineParticipant,
    TimelineParticipantFrame,
    TimelinePosition,
    TimelineVictimDamage,
)
from tests.helpers import register_exact_url, timeline_response_payload

if TYPE_CHECKING:
    from aioresponses import aioresponses

BASE_URL = "https://americas.api.riotgames.com/lol/match/v5/matches"
MATCH_ID = "NA1_5671503499"
PUUID_1 = "zEiEotqOyouhFjJ6B21ZzKFzd8qwcr2V4fCjsPFtKH6lGI7uL6UsZrLI66FQUwree_7EXzlSzg79RQ"
PUUID_2 = "QfBAP8d_7D12_1qA-M9pL4LjOzLX3Xh-P41yjn4fI9s9_X8tWJ7OnY630UzoVQK-fjjsLF5e_Xju8w"


@pytest_asyncio.fixture
async def fresh_client() -> AsyncGenerator[NexarClient]:
    """Client with no conftest catch-alls, so exact-URL registrations are the only matches."""
    client = NexarClient(riot_api_key="test-api-key", default_region=Region.NA1, cache_config=NO_CACHE_CONFIG)
    yield client
    await client.close()


def expected_warwick_r() -> TimelineVictimDamage:
    """The first victim damage source of the recorded kill, field for field."""
    return TimelineVictimDamage(
        basic=False,
        magic_damage=178,
        name="Warwick",
        participant_id=1,
        physical_damage=0,
        spell_name="warwickr",
        spell_slot=3,
        true_damage=0,
        type="OTHER",
    )


class TestMatchTimelineClient:
    """Client method against exact-URL registrations (routing and path pinning)."""

    async def test_get_match_timeline_parses_recorded_payload(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """The exact URL pins the americas v5 route and the /timeline path."""
        register_exact_url(
            mock_aioresponse,
            f"{BASE_URL}/{MATCH_ID}/timeline",
            timeline_response_payload(),
        )

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        assert timeline.metadata.match_id == MATCH_ID
        assert timeline.metadata.participants == [PUUID_1, PUUID_2]
        assert timeline.info.game_id == 5671503499
        assert timeline.info.frame_interval == 60000
        assert timeline.info.end_of_game_result == "GameComplete"
        assert timeline.info.participants == [
            TimelineParticipant(participant_id=1, puuid=PUUID_1),
            TimelineParticipant(participant_id=2, puuid=PUUID_2),
        ]
        assert [frame.timestamp for frame in timeline.frames] == [60017, 1589893]

    async def test_get_match_timeline_no_timeline_raises_not_found(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """A match without timeline data maps to Riot's 404 → NotFoundError."""
        register_exact_url(
            mock_aioresponse,
            f"{BASE_URL}/NA1_1234567890/timeline",
            {"status": {"message": "Data not found"}},
            status=404,
        )

        with pytest.raises(NotFoundError):
            await fresh_client.get_match_timeline("NA1_1234567890")


class TestTimelineModelApi:
    """The model API surface: frame lookup and the flattened event stream."""

    async def test_frames_for_resolves_puuid_across_frames(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        mine = timeline.frames_for(PUUID_1)
        assert [frame.participant_id for frame in mine] == [1, 1]
        assert [frame.total_gold for frame in mine] == [500, 10275]

    async def test_frames_for_unknown_puuid_returns_empty(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        assert timeline.frames_for("not-in-this-match") == []

    async def test_events_flatten_across_frames_in_order(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        assert [event.type for event in timeline.events] == [
            "PAUSE_END",
            "ITEM_PURCHASED",
            "SKILL_LEVEL_UP",
            "WARD_PLACED",
            "LEVEL_UP",
            "ITEM_SOLD",
            "CHAMPION_KILL",
            "CHAMPION_SPECIAL_KILL",
            "ELITE_MONSTER_KILL",
            "ITEM_UNDO",
            "CHAMPION_KILL",
            "DRAGON_SOUL_GIVEN",
            "BUILDING_KILL",
            "OBJECTIVE_BOUNTY_PRESTART",
            "GAME_END",
        ]
        assert timeline.frames[0].events == timeline.events[:4]
        assert timeline.frames[1].events == timeline.events[4:]


class TestTimelineEventParsing:
    """Event parsing against recorded values, one salient type at a time."""

    async def test_champion_kill_parses_every_recorded_field(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        kill = next(event for event in timeline.events if event.type == "CHAMPION_KILL" and event.timestamp == 768159)
        assert kill.timestamp == 768159
        assert kill.real_timestamp is None, "this kill predates Riot adding realTimestamp to kills"
        assert kill.killer_id == 1
        assert kill.victim_id == 9
        assert kill.bounty == 320
        assert kill.shutdown_bounty == 219
        assert kill.kill_streak_length == 0
        assert kill.position == TimelinePosition(x=12608, y=2218)
        assert kill.assisting_participant_ids == ()
        assert kill.victim_damage_received == (
            expected_warwick_r(),
            TimelineVictimDamage(
                basic=False,
                magic_damage=61,
                name="Warwick",
                participant_id=1,
                physical_damage=0,
                spell_name="warwickp",
                spell_slot=63,
                true_damage=0,
                type="OTHER",
            ),
            TimelineVictimDamage(
                basic=False,
                magic_damage=0,
                name="Warwick",
                participant_id=1,
                physical_damage=19,
                spell_name="",
                spell_slot=0,
                true_damage=0,
                type="OTHER",
            ),
        )
        # The recording carries the teamfight twin of the received breakdown,
        # identical in this kill; the helper keeps both, as on the wire.
        assert kill.victim_teamfight_damage_received == kill.victim_damage_received
        assert kill.victim_teamfight_damage_dealt == ()

    async def test_four_breakdown_kill_parses_dealt_fields(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """The recording's four-breakdown kill pins the two dealt parser lines, a nonzero killStreakLength, and a real assists list."""
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        kill = next(event for event in timeline.events if event.type == "CHAMPION_KILL" and event.timestamp == 350431)
        assert kill.kill_streak_length == 1
        assert kill.assisting_participant_ids == (1,)
        assert kill.bounty == 300
        assert kill.shutdown_bounty == 43
        assert kill.killer_id == 2
        assert kill.victim_id == 7
        assert kill.position == TimelinePosition(x=3247, y=12830)
        assert len(kill.victim_damage_dealt) == 5
        assert kill.victim_damage_dealt[0] == TimelineVictimDamage(
            basic=False,
            magic_damage=124,
            name="Amumu",
            participant_id=1,
            physical_damage=0,
            spell_name="tantrum",
            spell_slot=2,
            true_damage=0,
            type="OTHER",
        )
        assert kill.victim_teamfight_damage_dealt == kill.victim_damage_dealt
        assert len(kill.victim_damage_received) == 13
        assert kill.victim_teamfight_damage_received == kill.victim_damage_received

    async def test_elite_monster_kill_parses_subtype(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        elite = next(event for event in timeline.events if event.type == "ELITE_MONSTER_KILL")
        assert elite.monster_type == "DRAGON"
        assert elite.monster_sub_type == "HEXTECH_DRAGON"
        assert elite.killer_id == 7
        assert elite.killer_team_id == 200
        assert elite.position == TimelinePosition(x=9837, y=4397)

    async def test_item_undo_parses_gold_gain(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        undo = next(event for event in timeline.events if event.type == "ITEM_UNDO")
        assert undo.participant_id == 2
        assert undo.before_id == 2022
        assert undo.after_id == 0
        assert undo.gold_gain == 250

    async def test_building_kill_parses_tower_fields(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        building = next(event for event in timeline.events if event.type == "BUILDING_KILL")
        assert building.building_type == "TOWER_BUILDING"
        assert building.tower_type == "OUTER_TURRET"
        assert building.lane_type == "BOT_LANE"
        assert building.team_id == 100
        assert building.killer_id == 9

    async def test_game_end_parses_real_timestamp(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        game_end = next(event for event in timeline.events if event.type == "GAME_END")
        assert game_end.winning_team == 200
        assert game_end.game_id == 5671503499
        assert game_end.real_timestamp == datetime.fromtimestamp(1793555560000 / 1000, tz=UTC)

    async def test_pause_end_parses_real_timestamp(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        pause_end = next(event for event in timeline.events if event.type == "PAUSE_END")
        assert pause_end.real_timestamp == datetime.fromtimestamp(1793553970038 / 1000, tz=UTC)

    async def test_skill_level_up_and_ward_and_purchase_events(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        skill = next(event for event in timeline.events if event.type == "SKILL_LEVEL_UP")
        assert skill.participant_id == 8
        assert skill.skill_slot == 1
        assert skill.level_up_type == "NORMAL"

        ward = next(event for event in timeline.events if event.type == "WARD_PLACED")
        assert ward.creator_id == 5
        assert ward.ward_type == "UNDEFINED"

        purchase = next(event for event in timeline.events if event.type == "ITEM_PURCHASED")
        assert purchase.item_id == 3865
        assert purchase.participant_id == 0

    async def test_assisting_participant_ids_parse(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """Assists arrive under assistingParticipantIds (not the community-documented assistingIds)."""
        payload = timeline_response_payload()
        payload["info"]["frames"][1]["events"].append(
            {
                "assistingParticipantIds": [2, 4, 6],
                "killerId": 3,
                "timestamp": 800000,
                "type": "CHAMPION_KILL",
                "victimId": 7,
            },
        )
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", payload)

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        assisted = next(event for event in timeline.events if event.timestamp == 800000)
        assert assisted.assisting_participant_ids == (2, 4, 6)

    async def test_victim_teamfight_breakdowns_parse(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        payload = timeline_response_payload()
        kill = next(
            event
            for event in payload["info"]["frames"][1]["events"]
            if event["type"] == "CHAMPION_KILL" and event["timestamp"] == 768159
        )
        kill["victimTeamfightDamageReceived"] = [
            {
                "basic": True,
                "magicDamage": 0,
                "name": "",
                "participantId": 0,
                "physicalDamage": 237,
                "spellName": "turretbasicattack2",
                "spellSlot": 47,
                "trueDamage": 0,
                "type": "TOWER",
            },
        ]
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", payload)

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        parsed_kill = next(
            event for event in timeline.events if event.type == "CHAMPION_KILL" and event.timestamp == 768159
        )
        assert parsed_kill.victim_teamfight_damage_received == (
            TimelineVictimDamage(
                basic=True,
                magic_damage=0,
                name="",
                participant_id=0,
                physical_damage=237,
                spell_name="turretbasicattack2",
                spell_slot=47,
                true_damage=0,
                type="TOWER",
            ),
        )
        assert parsed_kill.victim_teamfight_damage_dealt == ()


class TestTimelineOmissions:
    """Riot omits empty values: minimal payloads parse with defaults, not KeyErrors."""

    def test_minimal_event_defaults_every_omitted_field(self) -> None:
        from nexar.models.match.timeline import TimelineEvent

        event = TimelineEvent.from_api_response({"timestamp": 78029, "type": "LEVEL_UP"})

        assert event.timestamp == 78029
        assert event.type == "LEVEL_UP"
        assert event.real_timestamp is None
        assert event.position is None
        assert event.assisting_participant_ids == ()
        assert event.killer_id == 0
        assert event.victim_id == 0
        assert event.bounty == 0
        assert event.shutdown_bounty == 0
        assert event.victim_damage_received == ()
        assert event.participant_id == 0
        assert event.item_id == 0
        assert event.ward_type == ""
        assert event.monster_type == ""
        assert event.building_type == ""
        assert event.winning_team == 0
        assert event.name == ""

    def test_participant_frame_without_stat_blocks(self) -> None:
        from nexar.models.match.timeline import TimelineParticipantFrame

        frame = TimelineParticipantFrame.from_api_response({"participantId": 3})

        assert frame.participant_id == 3
        assert frame.level == 0
        assert frame.total_gold == 0
        assert frame.position is None
        assert frame.champion_stats is None
        assert frame.damage_stats is None

    def test_frame_without_events_and_participant_frames(self) -> None:
        from nexar.models.match.timeline import TimelineFrame

        frame = TimelineFrame.from_api_response({"timestamp": 60000})

        assert frame.timestamp == 60000
        assert frame.participant_frames == {}
        assert frame.events == []

    def test_info_without_end_of_game_result_and_frame_interval(self) -> None:
        from nexar.models.match.timeline import TimelineInfo

        info = TimelineInfo.from_api_response({"gameId": 1, "participants": [], "frames": []})

        assert info.game_id == 1
        assert info.frame_interval == 0
        assert info.end_of_game_result is None

    def test_info_without_participants_and_frames_keys(self) -> None:
        """Riot omits empty values: absent arrays parse empty, not KeyError."""
        from nexar.models.match.timeline import TimelineInfo

        info = TimelineInfo.from_api_response({"gameId": 1})

        assert info.participants == []
        assert info.frames == []

    def test_champion_and_damage_stats_default_omitted_values(self) -> None:
        champion_stats = TimelineChampionStats.from_api_response({})
        assert champion_stats.health == 0
        assert champion_stats.power == 0

        damage_stats = TimelineDamageStats.from_api_response({})
        assert damage_stats.total_damage_taken == 0
        assert damage_stats.magic_damage_done == 0

    def test_participant_frame_stats_equality_against_recorded_values(self) -> None:
        """The first frame's participant 1 stats, field for field."""
        payload = timeline_response_payload()
        recorded = payload["info"]["frames"][0]["participantFrames"]["1"]

        frame = TimelineParticipantFrame.from_api_response(recorded)

        assert frame.champion_stats == TimelineChampionStats(
            ability_haste=0,
            ability_power=0,
            armor=33,
            armor_pen=0,
            armor_pen_percent=0,
            attack_damage=78,
            attack_speed=128,
            bonus_armor_pen_percent=0,
            bonus_magic_pen_percent=0,
            cc_reduction=0,
            cooldown_reduction=0,
            health=539,
            health_max=630,
            health_regen=11,
            lifesteal=0,
            magic_pen=0,
            magic_pen_percent=0,
            magic_resist=32,
            movement_speed=335,
            omnivamp=1,
            physical_vamp=0,
            power=280,
            power_max=280,
            power_regen=14,
            spell_vamp=0,
        )
        assert frame.damage_stats == TimelineDamageStats(
            magic_damage_done=0,
            magic_damage_done_to_champions=0,
            magic_damage_taken=97,
            physical_damage_done=0,
            physical_damage_done_to_champions=0,
            physical_damage_taken=0,
            total_damage_done=0,
            total_damage_done_to_champions=0,
            total_damage_taken=97,
            true_damage_done=0,
            true_damage_done_to_champions=0,
            true_damage_taken=0,
        )
        assert frame.position == TimelinePosition(x=1964, y=12192)


class TestTimelineRecordedSnapshots:
    """Every snapshot field parsed against the recording, value for value."""

    async def test_last_frame_snapshot_field_for_field(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """A second value point for every parser line: no parser constant can satisfy both frames."""
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        last = timeline.frames_for(PUUID_1)[-1]
        assert last == TimelineParticipantFrame(
            participant_id=1,
            level=16,
            current_gold=640,
            total_gold=10275,
            gold_per_second=0,
            jungle_minions_killed=0,
            minions_killed=198,
            xp=15879,
            time_enemy_spent_controlled=70337,
            position=TimelinePosition(x=5734, y=5834),
            champion_stats=TimelineChampionStats(
                ability_haste=0,
                ability_power=0,
                armor=96,
                armor_pen=0,
                armor_pen_percent=0,
                attack_damage=189,
                attack_speed=216,
                bonus_armor_pen_percent=0,
                bonus_magic_pen_percent=0,
                cc_reduction=30,
                cooldown_reduction=0,
                health=0,
                health_max=2613,
                health_regen=74,
                lifesteal=12,
                magic_pen=0,
                magic_pen_percent=0,
                magic_resist=131,
                movement_speed=395,
                omnivamp=1,
                physical_vamp=0,
                power=659,
                power_max=786,
                power_regen=32,
                spell_vamp=0,
            ),
            damage_stats=TimelineDamageStats(
                magic_damage_done=32367,
                magic_damage_done_to_champions=8192,
                magic_damage_taken=21232,
                physical_damage_done=90009,
                physical_damage_done_to_champions=9476,
                physical_damage_taken=11616,
                total_damage_done=131794,
                total_damage_done_to_champions=17669,
                total_damage_taken=35025,
                true_damage_done=9417,
                true_damage_done_to_champions=0,
                true_damage_taken=2175,
            ),
        )

    async def test_jungler_frame_carries_recorded_gold_per_second(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        """The jungler row (pid 5) is the recorded nonzero gold_per_second value point."""
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        pid_5_frame = timeline.frames[0].participant_frames[5]
        assert pid_5_frame.participant_id == 5
        assert pid_5_frame.gold_per_second == 30
        assert pid_5_frame.position == TimelinePosition(x=10942, y=1552)


class TestTimelineRemainingEventTypes:
    """Value assertions for every event type the earlier tests did not touch."""

    async def test_special_kill_level_up_soul_and_bounty_events(
        self,
        fresh_client: NexarClient,
        mock_aioresponse: "aioresponses",
    ) -> None:
        register_exact_url(mock_aioresponse, f"{BASE_URL}/{MATCH_ID}/timeline", timeline_response_payload())

        timeline = await fresh_client.get_match_timeline(MATCH_ID)

        special = next(event for event in timeline.events if event.type == "CHAMPION_SPECIAL_KILL")
        assert special.kill_type == "KILL_MULTI"
        assert special.multi_kill_length == 2
        assert special.killer_id == 3
        assert special.position == TimelinePosition(x=11393, y=1747)

        level_up = next(event for event in timeline.events if event.type == "LEVEL_UP")
        assert level_up.level == 2
        assert level_up.participant_id == 7

        sold = next(event for event in timeline.events if event.type == "ITEM_SOLD")
        assert sold.item_id == 2003
        assert sold.participant_id == 10
        assert sold.timestamp == 230035

        soul = next(event for event in timeline.events if event.type == "DRAGON_SOUL_GIVEN")
        assert soul.name == "Ocean"
        assert soul.team_id == 0

        bounty = next(event for event in timeline.events if event.type == "OBJECTIVE_BOUNTY_PRESTART")
        assert bounty.actual_start_time == 1505000
        assert bounty.team_id == 100


class TestMatchTimelineSharedFixture:
    """The conftest timeline catch-all serves the recorded mock payload."""

    async def test_client_fixture_serves_timeline(self, client: NexarClient) -> None:
        timeline = await client.get_match_timeline(MATCH_ID)

        assert timeline.metadata.match_id == MATCH_ID
        assert len(timeline.frames) == 2
        assert timeline.events, "recorded fixture carries events"

        # The recorded kill's teamfight breakdown parses from the shared fixture.
        kill = next(event for event in timeline.events if event.type == "CHAMPION_KILL")
        assert kill.victim_teamfight_damage_received
        assert kill.victim_teamfight_damage_received == kill.victim_damage_received

        # The three event types only this fixture carries, asserted against
        # their recorded values (kills the last unasserted parser paths).
        plate = next(event for event in timeline.events if event.type == "TURRET_PLATE_DESTROYED")
        assert plate.lane_type == "MID_LANE"
        assert plate.team_id == 100
        assert plate.killer_id == 0
        assert plate.position == TimelinePosition(x=5846, y=6396)

        ward_kill = next(event for event in timeline.events if event.type == "WARD_KILL")
        assert ward_kill.killer_id == 9
        assert ward_kill.ward_type == "SIGHT_WARD"

        destroyed = next(event for event in timeline.events if event.type == "ITEM_DESTROYED")
        assert destroyed.item_id == 1052
        assert destroyed.participant_id == 5

        # Participants 1 and 2 carry frames in both recorded frames.
        assert len(timeline.frames_for(PUUID_1)) == 2
        assert len(timeline.frames_for(PUUID_2)) == 2


class TestMatchTimelineLive:
    """Live canaries (real Riot API calls; skipped keyless)."""

    @pytest.mark.slow
    async def test_live_match_timeline_roundtrip(self, real_client: NexarClient) -> None:
        """Live canary: account, ranked match ids, one full timeline (3 fresh calls)."""
        player = await real_client.get_player(game_name="bexli", tag_line="bex")

        match_ids = await real_client.get_match_ids_by_puuid(
            player.puuid,
            queue=Queue.RANKED_SOLO_5x5,
            count=1,
        )
        assert match_ids, "account has ranked matches"

        timeline = await real_client.get_match_timeline(match_ids[0])
        assert timeline.metadata.match_id == match_ids[0]
        assert timeline.info.frame_interval == 60000
        assert timeline.info.end_of_game_result == "GameComplete"
        assert len(timeline.info.participants) == len(timeline.metadata.participants)

        assert len(timeline.frames) > 1, "a ranked match has multiple frames"
        assert timeline.events, "the event stream is non-empty"

        # The puuid frame lookup spans the whole match.
        mine = timeline.frames_for(player.puuid)
        assert mine
        assert len(mine) == len(timeline.frames)

        game_end = next(event for event in timeline.events if event.type == "GAME_END")
        assert game_end.winning_team in (100, 200)
        assert game_end.real_timestamp is not None
