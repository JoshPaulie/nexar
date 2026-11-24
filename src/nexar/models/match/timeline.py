"""Match timeline models (match-v5 timeline)."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from .match import MatchMetadata


@dataclass(frozen=True)
class TimelinePosition:
    """Map position in Riot's coordinate grid."""

    x: int
    """X coordinate."""

    y: int
    """Y coordinate."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TimelinePosition":
        """Create TimelinePosition from API response."""
        return cls(x=data.get("x", 0), y=data.get("y", 0))


@dataclass(frozen=True)
class TimelineVictimDamage:
    """A single damage source inside a champion kill's victim breakdowns."""

    basic: bool
    """Whether the source is a basic attack."""

    magic_damage: int
    """Magic damage dealt by this source."""

    name: str
    """Champion (or structure) name of the source; empty for unnamed sources."""

    participant_id: int
    """Participant ID of the source; 0 for neutral structures (towers)."""

    physical_damage: int
    """Physical damage dealt by this source."""

    spell_name: str
    """Internal spell identifier (e.g. ``lockeq``)."""

    spell_slot: int
    """Spell slot index; -1 for passive-style unnamed sources."""

    true_damage: int
    """True damage dealt by this source."""

    type: str
    """Source category, e.g. ``OTHER`` or ``TOWER``."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TimelineVictimDamage":
        """Create TimelineVictimDamage from API response."""
        return cls(
            basic=data.get("basic", False),
            magic_damage=data.get("magicDamage", 0),
            name=data.get("name", ""),
            participant_id=data.get("participantId", 0),
            physical_damage=data.get("physicalDamage", 0),
            spell_name=data.get("spellName", ""),
            spell_slot=data.get("spellSlot", 0),
            true_damage=data.get("trueDamage", 0),
            type=data.get("type", ""),
        )


@dataclass(frozen=True)
class TimelineChampionStats:
    """Combat stats of one participant at a frame snapshot."""

    ability_haste: int
    """Ability haste."""

    ability_power: int
    """Ability power."""

    armor: int
    """Armor."""

    armor_pen: int
    """Lethality (flat armor penetration)."""

    armor_pen_percent: int
    """Armor penetration percent."""

    attack_damage: int
    """Attack damage."""

    attack_speed: int
    """Attack speed in Riot's raw frame encoding; the reference declares no
    unit for it (values like 128-216 do not map to attacks per second)."""

    bonus_armor_pen_percent: int
    """Bonus armor penetration percent."""

    bonus_magic_pen_percent: int
    """Bonus magic penetration percent."""

    cc_reduction: int
    """Tenacity (crowd-control reduction)."""

    cooldown_reduction: int
    """Cooldown reduction."""

    health: int
    """Current health."""

    health_max: int
    """Maximum health."""

    health_regen: int
    """Health regeneration per 5 seconds."""

    lifesteal: int
    """Lifesteal percent."""

    magic_pen: int
    """Flat magic penetration."""

    magic_pen_percent: int
    """Magic penetration percent."""

    magic_resist: int
    """Magic resist."""

    movement_speed: int
    """Movement speed."""

    omnivamp: int
    """Omnivamp percent."""

    physical_vamp: int
    """Physical vamp percent."""

    power: int
    """Current resource (mana, energy, ...)."""

    power_max: int
    """Maximum resource."""

    power_regen: int
    """Resource regeneration per 5 seconds."""

    spell_vamp: int
    """Spell vamp percent."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TimelineChampionStats":
        """Create TimelineChampionStats from API response."""
        return cls(
            ability_haste=data.get("abilityHaste", 0),
            ability_power=data.get("abilityPower", 0),
            armor=data.get("armor", 0),
            armor_pen=data.get("armorPen", 0),
            armor_pen_percent=data.get("armorPenPercent", 0),
            attack_damage=data.get("attackDamage", 0),
            attack_speed=data.get("attackSpeed", 0),
            bonus_armor_pen_percent=data.get("bonusArmorPenPercent", 0),
            bonus_magic_pen_percent=data.get("bonusMagicPenPercent", 0),
            cc_reduction=data.get("ccReduction", 0),
            cooldown_reduction=data.get("cooldownReduction", 0),
            health=data.get("health", 0),
            health_max=data.get("healthMax", 0),
            health_regen=data.get("healthRegen", 0),
            lifesteal=data.get("lifesteal", 0),
            magic_pen=data.get("magicPen", 0),
            magic_pen_percent=data.get("magicPenPercent", 0),
            magic_resist=data.get("magicResist", 0),
            movement_speed=data.get("movementSpeed", 0),
            omnivamp=data.get("omnivamp", 0),
            physical_vamp=data.get("physicalVamp", 0),
            power=data.get("power", 0),
            power_max=data.get("powerMax", 0),
            power_regen=data.get("powerRegen", 0),
            spell_vamp=data.get("spellVamp", 0),
        )


@dataclass(frozen=True)
class TimelineDamageStats:
    """Damage totals of one participant at a frame snapshot."""

    magic_damage_done: int
    """Total magic damage dealt."""

    magic_damage_done_to_champions: int
    """Magic damage dealt to champions."""

    magic_damage_taken: int
    """Magic damage taken."""

    physical_damage_done: int
    """Total physical damage dealt."""

    physical_damage_done_to_champions: int
    """Physical damage dealt to champions."""

    physical_damage_taken: int
    """Physical damage taken."""

    total_damage_done: int
    """Total damage dealt."""

    total_damage_done_to_champions: int
    """Total damage dealt to champions."""

    total_damage_taken: int
    """Total damage taken."""

    true_damage_done: int
    """Total true damage dealt."""

    true_damage_done_to_champions: int
    """True damage dealt to champions."""

    true_damage_taken: int
    """True damage taken."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TimelineDamageStats":
        """Create TimelineDamageStats from API response."""
        return cls(
            magic_damage_done=data.get("magicDamageDone", 0),
            magic_damage_done_to_champions=data.get("magicDamageDoneToChampions", 0),
            magic_damage_taken=data.get("magicDamageTaken", 0),
            physical_damage_done=data.get("physicalDamageDone", 0),
            physical_damage_done_to_champions=data.get("physicalDamageDoneToChampions", 0),
            physical_damage_taken=data.get("physicalDamageTaken", 0),
            total_damage_done=data.get("totalDamageDone", 0),
            total_damage_done_to_champions=data.get("totalDamageDoneToChampions", 0),
            total_damage_taken=data.get("totalDamageTaken", 0),
            true_damage_done=data.get("trueDamageDone", 0),
            true_damage_done_to_champions=data.get("trueDamageDoneToChampions", 0),
            true_damage_taken=data.get("trueDamageTaken", 0),
        )


@dataclass(frozen=True)
class TimelineParticipantFrame:
    """One participant's per-minute snapshot inside a frame."""

    participant_id: int
    """Participant ID (1-10); identity field, always present."""

    level: int
    """Champion level at this frame."""

    current_gold: int
    """Unspent gold at this frame."""

    total_gold: int
    """Total gold earned by this frame."""

    gold_per_second: int
    """Passive gold generation rate at this frame."""

    jungle_minions_killed: int
    """Jungle monsters killed by this frame."""

    minions_killed: int
    """Lane minions killed by this frame."""

    xp: int
    """Experience by this frame."""

    time_enemy_spent_controlled: int
    """Crowd-control time inflicted by this frame, in milliseconds (the wire
    carries raw ms, 70337 near the end of a 26-minute match; the reference
    lists no unit, and this is not seconds like ``timeCCingOthers``)."""

    position: TimelinePosition | None
    """Map position at this frame, or None when Riot omits it."""

    champion_stats: TimelineChampionStats | None
    """Combat stats at this frame, or None when Riot omits the block."""

    damage_stats: TimelineDamageStats | None
    """Damage totals at this frame, or None when Riot omits the block."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TimelineParticipantFrame":
        """Create TimelineParticipantFrame from API response."""
        return cls(
            # Identity field: a participant frame without an ID is not one.
            participant_id=data["participantId"],
            level=data.get("level", 0),
            current_gold=data.get("currentGold", 0),
            total_gold=data.get("totalGold", 0),
            gold_per_second=data.get("goldPerSecond", 0),
            jungle_minions_killed=data.get("jungleMinionsKilled", 0),
            minions_killed=data.get("minionsKilled", 0),
            xp=data.get("xp", 0),
            time_enemy_spent_controlled=data.get("timeEnemySpentControlled", 0),
            position=TimelinePosition.from_api_response(p_data) if (p_data := data.get("position")) else None,
            champion_stats=TimelineChampionStats.from_api_response(c_data)
            if (c_data := data.get("championStats"))
            else None,
            damage_stats=TimelineDamageStats.from_api_response(d_data) if (d_data := data.get("damageStats")) else None,
        )


@dataclass(frozen=True)
class TimelineEvent:
    """A single timeline event.

    The wire only guarantees ``timestamp`` and ``type``; every other field is
    carried per event type, and Riot omits empty values on top of that, so all
    of them parse with defaults. The event types observed on the live op:
    ``CHAMPION_KILL``, ``CHAMPION_SPECIAL_KILL``, ``ELITE_MONSTER_KILL``,
    ``BUILDING_KILL``, ``TURRET_PLATE_DESTROYED``, ``WARD_PLACED``,
    ``WARD_KILL``, ``ITEM_PURCHASED``, ``ITEM_SOLD``, ``ITEM_DESTROYED``,
    ``ITEM_UNDO``, ``SKILL_LEVEL_UP``, ``LEVEL_UP``, ``DRAGON_SOUL_GIVEN``,
    ``OBJECTIVE_BOUNTY_PRESTART``, ``PAUSE_END``, ``GAME_END`` (legacy
    gamemodes add ``ASCENDED_EVENT``, ``CAPTURE_POINT``,
    ``PORO_KING_SUMMON``). Riot introduces event types without notice, so
    ``type`` stays a string rather than an enum and unknown types parse
    instead of raising.
    """

    timestamp: int
    """Milliseconds since the match started (Riot's own encoding)."""

    type: str
    """Event type discriminator, e.g. ``CHAMPION_KILL``."""

    real_timestamp: datetime | None
    """Wall-clock time of the event, when Riot includes it (most types omit
    it; ``GAME_END`` and ``PAUSE_END`` carry it)."""

    position: TimelinePosition | None
    """Map coordinates, for the event types that carry them."""

    assisting_participant_ids: tuple[int, ...]
    """Participant IDs that assisted, for kill and building events."""

    killer_id: int
    """Killer participant ID (kills, ward kills, plate destructions)."""

    victim_id: int
    """Victim participant ID (champion kills)."""

    bounty: int
    """Kill bounty gold (champion, elite monster, and building kills)."""

    shutdown_bounty: int
    """Shutdown bounty gold (champion kills)."""

    kill_streak_length: int
    """Victim's kill streak before a champion kill ended it."""

    multi_kill_length: int
    """Multi-kill size for special kill announcements."""

    kill_type: str
    """Special-kill flavor, e.g. ``KILL_FIRST_BLOOD`` or ``KILL_MULTI5``."""

    victim_damage_dealt: tuple[TimelineVictimDamage, ...]
    """Per-source damage the victim dealt before dying."""

    victim_damage_received: tuple[TimelineVictimDamage, ...]
    """Per-source damage the victim received before dying."""

    victim_teamfight_damage_dealt: tuple[TimelineVictimDamage, ...]
    """Per-source teamfight-filtered damage the victim dealt."""

    victim_teamfight_damage_received: tuple[TimelineVictimDamage, ...]
    """Per-source teamfight-filtered damage the victim received."""

    participant_id: int
    """Actor participant ID (item and level-up events)."""

    creator_id: int
    """Ward creator participant ID (ward placements)."""

    level: int
    """Level reached (``LEVEL_UP``)."""

    skill_slot: int
    """Ability slot leveled up (``SKILL_LEVEL_UP``)."""

    level_up_type: str
    """``NORMAL`` or ``EVOLVE`` (``SKILL_LEVEL_UP``)."""

    item_id: int
    """Item involved (item events)."""

    after_id: int
    """Item restored by the undo (``ITEM_UNDO``)."""

    before_id: int
    """Item removed by the undo (``ITEM_UNDO``)."""

    gold_gain: int
    """Gold refunded by the undo (``ITEM_UNDO``)."""

    ward_type: str
    """Ward type involved (ward events)."""

    monster_type: str
    """Monster killed, e.g. ``DRAGON`` or ``BARON_NASHOR`` (elite kills)."""

    monster_sub_type: str
    """Monster subtype, e.g. the dragon element ``HEXTECH_DRAGON`` (elite kills)."""

    killer_team_id: int
    """Team of the killer (elite monster kills)."""

    building_type: str
    """``TOWER_BUILDING`` or ``INHIBITOR_BUILDING`` (building kills)."""

    tower_type: str
    """Which tower, e.g. ``OUTER_TURRET`` (building kills)."""

    lane_type: str
    """Lane involved, e.g. ``BOT_LANE`` (building kills, plate destructions)."""

    team_id: int
    """Team involved (building kills, souls, plate destructions)."""

    winning_team: int
    """Winning team ID (``GAME_END``)."""

    game_id: int
    """Game ID (``GAME_END``)."""

    name: str
    """Soul name, e.g. ``Ocean`` (``DRAGON_SOUL_GIVEN``)."""

    actual_start_time: int
    """Planned bounty activation time (``OBJECTIVE_BOUNTY_PRESTART``)."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TimelineEvent":
        """Create TimelineEvent from API response.

        ``timestamp`` and ``type`` are the only guaranteed keys (Riot's
        EventsTimeLineDto lists exactly those); everything else parses with
        defaults, and the champion-kill victim breakdowns parse element-wise.
        """
        return cls(
            # Guaranteed keys: direct reads, as with every identity field.
            timestamp=data["timestamp"],
            type=data["type"],
            real_timestamp=datetime.fromtimestamp(data["realTimestamp"] / 1000, tz=UTC)
            if data.get("realTimestamp")
            else None,
            position=TimelinePosition.from_api_response(p_data) if (p_data := data.get("position")) else None,
            assisting_participant_ids=tuple(data.get("assistingParticipantIds", ())),
            killer_id=data.get("killerId", 0),
            victim_id=data.get("victimId", 0),
            bounty=data.get("bounty", 0),
            shutdown_bounty=data.get("shutdownBounty", 0),
            kill_streak_length=data.get("killStreakLength", 0),
            multi_kill_length=data.get("multiKillLength", 0),
            kill_type=data.get("killType", ""),
            victim_damage_dealt=tuple(
                TimelineVictimDamage.from_api_response(entry) for entry in data.get("victimDamageDealt", ())
            ),
            victim_damage_received=tuple(
                TimelineVictimDamage.from_api_response(entry) for entry in data.get("victimDamageReceived", ())
            ),
            victim_teamfight_damage_dealt=tuple(
                TimelineVictimDamage.from_api_response(entry) for entry in data.get("victimTeamfightDamageDealt", ())
            ),
            victim_teamfight_damage_received=tuple(
                TimelineVictimDamage.from_api_response(entry) for entry in data.get("victimTeamfightDamageReceived", ())
            ),
            participant_id=data.get("participantId", 0),
            creator_id=data.get("creatorId", 0),
            level=data.get("level", 0),
            skill_slot=data.get("skillSlot", 0),
            level_up_type=data.get("levelUpType", ""),
            item_id=data.get("itemId", 0),
            after_id=data.get("afterId", 0),
            before_id=data.get("beforeId", 0),
            gold_gain=data.get("goldGain", 0),
            ward_type=data.get("wardType", ""),
            monster_type=data.get("monsterType", ""),
            monster_sub_type=data.get("monsterSubType", ""),
            killer_team_id=data.get("killerTeamId", 0),
            building_type=data.get("buildingType", ""),
            tower_type=data.get("towerType", ""),
            lane_type=data.get("laneType", ""),
            team_id=data.get("teamId", 0),
            winning_team=data.get("winningTeam", 0),
            game_id=data.get("gameId", 0),
            name=data.get("name", ""),
            actual_start_time=data.get("actualStartTime", 0),
        )


@dataclass(frozen=True)
class TimelineFrame:
    """One minute of the match: participant snapshots plus the events in between."""

    timestamp: int
    """Milliseconds since the match started; identity field, always present."""

    participant_frames: dict[int, TimelineParticipantFrame]
    """Per-participant snapshots keyed by participant ID (1-10)."""

    events: list[TimelineEvent]
    """Events that happened since the previous frame, chronological."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TimelineFrame":
        """Create TimelineFrame from API response."""
        return cls(
            # Identity field: a frame without a timestamp is not one.
            timestamp=data["timestamp"],
            participant_frames={
                int(key): TimelineParticipantFrame.from_api_response(frame)
                for key, frame in data.get("participantFrames", {}).items()
            },
            events=[TimelineEvent.from_api_response(event) for event in data.get("events", [])],
        )


@dataclass(frozen=True)
class TimelineParticipant:
    """A timeline info participant: the participant ID to PUUID mapping row."""

    participant_id: int
    """Participant ID (1-10); identity field, always present."""

    puuid: str
    """Player's universally unique identifier; identity field, always present."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TimelineParticipant":
        """Create TimelineParticipant from API response."""
        return cls(
            participant_id=data["participantId"],
            puuid=data["puuid"],
        )


@dataclass(frozen=True)
class TimelineInfo:
    """Timeline match info: frame cadence and the frame series."""

    frame_interval: int
    """Frame interval in milliseconds (60000 on live matches)."""

    game_id: int
    """Game ID; identity field, always present."""

    end_of_game_result: str | None
    """e.g. ``GameComplete``, or None when Riot omits it."""

    participants: list[TimelineParticipant]
    """Participant ID to PUUID mapping for this match."""

    frames: list[TimelineFrame]
    """Per-minute frames, chronological (the last carries ``GAME_END``)."""

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "TimelineInfo":
        """Create TimelineInfo from API response."""
        return cls(
            frame_interval=data.get("frameInterval", 0),
            # Identity field: matches MatchInfo.game_id's direct read.
            game_id=data["gameId"],
            end_of_game_result=data.get("endOfGameResult"),
            # Collections harden like every non-identity field: Riot omits empty
            # values, so an absent array parses empty instead of raising.
            participants=[
                TimelineParticipant.from_api_response(participant) for participant in data.get("participants", [])
            ],
            frames=[TimelineFrame.from_api_response(frame) for frame in data.get("frames", [])],
        )


@dataclass(frozen=True)
class Timeline:
    """A complete match timeline."""

    metadata: MatchMetadata
    """Match metadata (shared DTO shape with ``Match``)."""

    info: TimelineInfo
    """Timeline info including participants and frames."""

    @property
    def frames(self) -> list[TimelineFrame]:
        """All frames, chronological."""
        return self.info.frames

    @property
    def events(self) -> list[TimelineEvent]:
        """All events across frames, flattened and chronological."""
        return [event for frame in self.info.frames for event in frame.events]

    def frames_for(self, puuid: str) -> list[TimelineParticipantFrame]:
        """
        Get one participant's per-minute snapshots, resolved by PUUID.

        Args:
            puuid: The player's universally unique identifier.

        Returns:
            The participant's frame from every frame that carries it, in
            chronological order. A PUUID that did not play in this match
            returns an empty list (matching ``ParticipantList.by_puuid``,
            which returns None on a miss instead of raising).

        """
        participant_id = next(
            (participant.participant_id for participant in self.info.participants if participant.puuid == puuid),
            None,
        )
        if participant_id is None:
            return []
        return [
            frame.participant_frames[participant_id]
            for frame in self.info.frames
            if participant_id in frame.participant_frames
        ]

    @classmethod
    def from_api_response(cls, data: dict[str, Any]) -> "Timeline":
        """Create Timeline from API response."""
        return cls(
            metadata=MatchMetadata.from_api_response(data["metadata"]),
            info=TimelineInfo.from_api_response(data["info"]),
        )
