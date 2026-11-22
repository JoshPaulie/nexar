"""Identity-aware Riot routes for executing docs snippets offline.

``tests/test_snippets.py`` runs every snippet's ``main()`` against these
routes. The load-bearing piece is the roster: the account route hands out a
puuid, and the match and timeline payloads are generated from the same
identities, so a snippet that looks its player up inside a match always finds
a participant. A match payload carrying unrelated puuids would let those
snippets pass on empty stats with no exception -- a false green the gate
cannot afford.

Nothing here talks to the wire, and the roster grows on demand: an identity a
snippet asks for that is not in the base table is synthesized deterministically
and joins the participant list, so new snippet ids never silently miss their
match row.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote

from aioresponses import CallbackResult

from .mastery import champion_mastery_payload

if TYPE_CHECKING:
    from aioresponses import aioresponses

BASE_URL = r"https://[^/]+\.api\.riotgames\.com"
DUMMY_KEY = "RGAPI-SNIPPET-TEST"
"""Key the gate exports: the snippets' runtime key guards must not trip."""

FAILURE_MARKER = "Snippet execution skipped or failed"
"""What the key-guarded snippets print when they swallow an exception.

The gate treats it as a failure: under mocks a snippet has no reason to skip,
and a swallowed traceback is exactly the silent green the gate exists to stop.
"""

# Game name, tag line, champion name, champion id -- ten identities, five per side.
_ROSTER: tuple[tuple[str, str, str, int], ...] = (
    ("bexli", "bex", "Jinx", 222),
    ("mltsimpleton", "na1", "Lux", 99),
    ("roninalex", "na1", "Garen", 86),
    ("poydok", "na1", "Ahri", 103),
    ("boxrog", "na1", "Thresh", 412),
    ("vynle", "na1", "LeeSin", 64),
    ("doublelift", "na1", "Caitlyn", 51),
    ("thebausffs", "cool", "Sion", 14),
    ("agurin", "euw", "KhaZix", 121),
    ("playername", "na1", "Orianna", 61),
)

# The two ids the batch example documents as not-found. Everything else
# synthesizes, so a new snippet id cannot quietly 404 the whole gate.
_MISSING_ACCOUNTS = frozenset({("nonexistent", "user"), ("alsobad", "user")})

_RECORDED_PUUID = "0wKS4sQQTcA6mAmu_oW5rVhyxmWAXV9hZrraXnDdh8GvelgGWYM5tM7fcHw0kalBVgCl6MxOZe0bLA"
"""bexli's puuid from ``mock_responses.json``: one persona matches the recording."""

_POSITIONS = ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY")
_LANES = {"TOP": "TOP", "JUNGLE": "JUNGLE", "MIDDLE": "MIDDLE", "BOTTOM": "BOTTOM", "UTILITY": "BOTTOM"}
_SPARE_CHAMPIONS: tuple[tuple[str, int], ...] = (
    ("Akali", 84),
    ("Vayne", 67),
    ("Nautilus", 111),
    ("JarvanIV", 59),
    ("Syndra", 134),
    ("Shen", 98),
)

_MATCH_IDS = ["NA1_5320484860", "NA1_5320477703", "NA1_5320466273"]
_GAME_START_MS = 1751820328000
_GAME_DURATION_S = 1800


def _result(payload: object, *, status: int = 200) -> CallbackResult:
    """A callback result whose payload may be a JSON list.

    ``CallbackResult`` annotates ``payload`` as a dict, but aioresponses
    ``json.dumps`` whatever it gets and Riot serves list payloads too, so the
    body is built here instead of leaning on the stub's narrower type.
    """
    return CallbackResult(status=status, body=json.dumps(payload))


def _digest(text: str) -> bytes:
    return hashlib.sha256(text.encode()).digest()


def _puuid(game_name: str, tag_line: str) -> str:
    """A stable 43-character puuid-shaped id for a synthesized identity."""
    if (game_name.casefold(), tag_line.casefold()) == ("bexli", "bex"):
        return _RECORDED_PUUID
    return base64.urlsafe_b64encode(_digest(f"{game_name.casefold()}#{tag_line.casefold()}")).decode().rstrip("=")


@dataclass(frozen=True)
class Identity:
    """One roster persona, shared by the account, match, and timeline payloads."""

    game_name: str
    tag_line: str
    puuid: str
    champion_name: str
    champion_id: int
    participant_id: int
    team_id: int
    position: str


def _identity(
    game_name: str,
    tag_line: str,
    champion_name: str,
    champion_id: int,
    participant_id: int,
) -> Identity:
    position = _POSITIONS[(participant_id - 1) % len(_POSITIONS)]
    return Identity(
        game_name=game_name,
        tag_line=tag_line,
        puuid=_puuid(game_name, tag_line),
        champion_name=champion_name,
        champion_id=champion_id,
        participant_id=participant_id,
        # Odd participant ids are blue side; red side wins, as on a real payload.
        team_id=100 if participant_id % 2 else 200,
        position=position,
    )


def _spare_identity(game_name: str, tag_line: str, participant_id: int) -> Identity:
    champion_name, champion_id = _SPARE_CHAMPIONS[
        int.from_bytes(_digest(game_name + tag_line)[:2]) % len(_SPARE_CHAMPIONS)
    ]
    return _identity(game_name, tag_line, champion_name, champion_id, participant_id)


def _participant_payload(identity: Identity) -> dict[str, Any]:
    """A complete participant block: stats, perks, and challenges the snippets read."""
    boost = identity.participant_id
    return {
        "puuid": identity.puuid,
        "riotIdGameName": identity.game_name,
        "riotIdTagline": identity.tag_line,
        "summonerName": f"{identity.game_name}#{identity.tag_line}",
        "championId": identity.champion_id,
        "championName": identity.champion_name,
        "teamId": identity.team_id,
        "participantId": identity.participant_id,
        "win": identity.team_id == 200,
        "individualPosition": identity.position,
        "teamPosition": identity.position,
        "lane": _LANES[identity.position],
        "role": "SOLO" if identity.position in {"TOP", "MIDDLE"} else identity.position,
        "champLevel": 18,
        "kills": 3 + boost,
        "deaths": 2 + boost % 3,
        "assists": 5 + boost * 2,
        "goldEarned": 12000 + boost * 250,
        "goldSpent": 11000 + boost * 200,
        "visionScore": 15 + boost * 3,
        "item0": 3031,
        "item1": 3006,
        "item2": 6672,
        "item3": 3072,
        "item4": 3036,
        "item5": 3046,
        "item6": 3340,
        "totalMinionsKilled": 150 + boost * 4,
        "neutralMinionsKilled": 12 + boost,
        "totalDamageDealtToChampions": 18000 + boost * 900,
        "magicDamageDealtToChampions": 9000 + boost * 400,
        "physicalDamageDealtToChampions": 8000 + boost * 300,
        "trueDamageDealtToChampions": 1000 + boost * 100,
        "dragonKills": boost % 3,
        "baronKills": boost % 2,
        "turretKills": 1 + boost % 4,
        "perks": {
            "statPerks": {"defense": 5001, "flex": 5008, "offense": 5005},
            "styles": [
                {
                    "description": "primaryStyle",
                    "style": 8000,
                    "selections": [
                        {"perk": 8005, "var1": 0, "var2": 0, "var3": 0},
                        {"perk": 9101, "var1": 0, "var2": 0, "var3": 0},
                        {"perk": 9104, "var1": 0, "var2": 0, "var3": 0},
                        {"perk": 8014, "var1": 0, "var2": 0, "var3": 0},
                    ],
                },
                {
                    "description": "subStyle",
                    "style": 8300,
                    "selections": [
                        {"perk": 8304, "var1": 0, "var2": 0, "var3": 0},
                        {"perk": 8347, "var1": 0, "var2": 0, "var3": 0},
                    ],
                },
            ],
        },
        "challenges": {
            "kda": (3 + boost + 5 + boost * 2) / (2 + boost % 3),
            "killParticipation": 0.55 + boost / 100,
            "damagePerMinute": 600.0 + boost * 10,
            "goldPerMinute": 420.0 + boost * 5,
            "visionScorePerMinute": 1.1 + boost / 100,
            "teamDamagePercentage": 0.18 + boost / 100,
            "skillshotsDodged": 20 + boost,
            "skillshotsHit": 45 + boost * 2,
            "epicMonsterSteals": boost % 2,
            "controlWardsPlaced": boost % 4,
            "multikills": boost % 3,
            "soloKills": boost % 4,
            "takedowns": 8 + boost,
            "turretPlatesTaken": boost % 5,
            "killingSprees": boost % 3,
            "buffsStolen": boost % 2,
        },
    }


def _team_payload(team_id: int) -> dict[str, Any]:
    won = team_id == 200
    objective = {"first": won, "kills": 2 if won else 1}
    return {
        "teamId": team_id,
        "win": won,
        "bans": [
            {"championId": 875, "pickTurn": 1},
            {"championId": 24, "pickTurn": 2},
            {"championId": 157, "pickTurn": 3},
        ],
        "objectives": {
            "baron": objective,
            "champion": {"first": won, "kills": 30 if won else 22},
            "dragon": {"first": won, "kills": 3 if won else 2},
            "inhibitor": {"first": won, "kills": 2 if won else 1},
            "riftHerald": objective,
            "tower": {"first": won, "kills": 8 if won else 4},
            "horde": {"first": won, "kills": 3},
        },
    }


def match_payload(match_id: str, identities: list[Identity]) -> dict[str, Any]:
    """A match payload where every roster identity plays as a participant."""
    game_id = int(re.sub(r"\D", "", match_id) or "0")
    return {
        "metadata": {
            "dataVersion": "2",
            "matchId": match_id,
            "participants": [identity.puuid for identity in identities],
        },
        "info": {
            "gameCreation": _GAME_START_MS,
            "gameDuration": _GAME_DURATION_S,
            "gameEndTimestamp": _GAME_START_MS + _GAME_DURATION_S * 1000,
            "gameId": game_id,
            "gameMode": "CLASSIC",
            "gameName": f"teambuilder-match-{match_id}",
            "gameStartTimestamp": _GAME_START_MS,
            "gameType": "MATCHED_GAME",
            "gameVersion": "15.1.615.9282",
            "mapId": 11,
            "participants": [_participant_payload(identity) for identity in identities],
            "platformId": "NA1",
            "queueId": 420,
            "teams": [_team_payload(100), _team_payload(200)],
            "tournamentCode": "",
        },
    }


def _timeline_frame(minute: int, identities: list[Identity]) -> dict[str, Any]:
    return {
        "timestamp": minute * 60000,
        "participantFrames": {
            str(identity.participant_id): {
                "participantId": identity.participant_id,
                "level": 6 + minute * 4,
                "currentGold": 400 + minute * 60,
                "totalGold": 2500 * minute + identity.participant_id * 120,
                "xp": 900 * minute,
                "minionsKilled": 8 * minute,
                "jungleMinionsKilled": minute,
            }
            for identity in identities
        },
        "events": [
            {
                "timestamp": minute * 60000,
                "type": "CHAMPION_KILL",
                "killerId": identities[0].participant_id,
                "victimId": identities[1].participant_id,
                "bounty": 300,
                "position": {"x": 5000, "y": 5000},
            },
            {"timestamp": minute * 60000 + 1000, "type": "WARD_PLACED", "creatorId": identities[0].participant_id},
        ],
    }


def timeline_payload(match_id: str, identities: list[Identity]) -> dict[str, Any]:
    """A timeline carrying per-minute gold for every roster identity."""
    frames = [_timeline_frame(minute, identities) for minute in (1, 2, 3)]
    frames[-1]["events"].append(
        {
            "timestamp": 4 * 60000,
            "type": "GAME_END",
            "winningTeam": 200,
            "gameId": int(re.sub(r"\D", "", match_id) or "0"),
            "realTimestamp": _GAME_START_MS + _GAME_DURATION_S * 1000,
        },
    )
    return {
        "metadata": {
            "dataVersion": "2",
            "matchId": match_id,
            "participants": [identity.puuid for identity in identities],
        },
        "info": {
            "frameInterval": 60000,
            "gameId": int(re.sub(r"\D", "", match_id) or "0"),
            "participants": [
                {"participantId": identity.participant_id, "puuid": identity.puuid} for identity in identities
            ],
            "frames": frames,
        },
    }


def summoner_payload(identity: Identity) -> dict[str, Any]:
    return {
        "id": f"summoner-{identity.puuid[:16]}",
        "puuid": identity.puuid,
        "profileIconId": 5435,
        "revisionDate": _GAME_START_MS,
        "summonerLevel": 300 + identity.participant_id,
    }


def league_entry_payload(identity: Identity) -> dict[str, Any]:
    return {
        "queueType": "RANKED_SOLO_5x5",
        "tier": "GOLD",
        "rank": ("I", "II", "III", "IV")[identity.participant_id % 4],
        "puuid": identity.puuid,
        "leaguePoints": 40 + identity.participant_id * 7,
        "wins": 50 + identity.participant_id,
        "losses": 40 + identity.participant_id * 2,
        "hotStreak": False,
        "veteran": False,
        "freshBlood": False,
        "inactive": False,
    }


def apex_league_payload(identities: list[Identity]) -> dict[str, Any]:
    """Challenger ladder: whole and pre-sorted by LP, as the live op serves it."""
    entries = [
        {
            "puuid": identity.puuid,
            "leaguePoints": 1200 - index * 50,
            "wins": 200 + index,
            "losses": 120 + index,
            "hotStreak": index == 0,
            "veteran": False,
            "freshBlood": False,
            "inactive": False,
        }
        for index, identity in enumerate(identities)
    ]
    return {"tier": "CHALLENGER", "queue": "RANKED_SOLO_5x5", "entries": entries}


def challenge_config_payload() -> list[dict[str, Any]]:
    return [
        {
            "id": 0,
            "localizedNames": {
                "en_US": {"name": "CRYSTAL", "description": "", "shortDescription": "Earn crystal points."},
            },
            "state": "ENABLED",
            "leaderboard": True,
            "thresholds": {"IRON": 1.0, "MASTER": 800.0, "GRANDMASTER": 1200.0, "CHALLENGER": 1600.0},
        },
        {
            "id": 1,
            "localizedNames": {"en_US": {"name": "CRYSTAL CUT", "description": "", "shortDescription": "Deal damage."}},
            "state": "ENABLED",
            "leaderboard": False,
            "thresholds": {"IRON": 10.0, "MASTER": 25000.0},
        },
    ]


def challenge_percentiles_payload() -> dict[str, float]:
    return {"IRON": 0.6, "BRONZE": 0.3, "GOLD": 0.08, "MASTER": 0.0031, "CHALLENGER": 0.0001}


def challenge_leaderboard_payload(identities: list[Identity]) -> list[dict[str, Any]]:
    return [
        {"puuid": identity.puuid, "value": 15000.0 - index * 900, "position": 58 + index}
        for index, identity in enumerate(identities[:3])
    ]


def challenge_player_data_payload() -> dict[str, Any]:
    return {
        "challenges": [
            {"challengeId": 0, "percentile": 0.022, "level": "DIAMOND", "value": 15165.0},
            {"challengeId": 302101, "percentile": 0.003, "level": "GRANDMASTER", "value": 295.0},
        ],
        "preferences": {"bannerAccent": "1", "title": "40220104", "challengeIds": [402409, 203404]},
        "totalPoints": {"current": 42500, "level": "DIAMOND", "max": 60000, "percentile": 0.08},
        "categoryPoints": {
            "EXPERTISE": {"current": 12000, "level": "PLATINUM", "max": 20000, "percentile": 0.1},
        },
    }


def champion_rotations_payload() -> dict[str, Any]:
    return {"sr": [1, 2, 3, 4, 5, 6, 7, 8], "newplayer": [9, 10]}


def platform_status_payload() -> dict[str, Any]:
    return {
        "id": "NA1",
        "name": "North America",
        "locales": ["en_US"],
        "maintenances": [],
        "incidents": [
            {
                "id": 1,
                "incident_severity": "info",
                "titles": [{"locale": "en_US", "content": "Ranked queues are degraded"}],
                "updates": [
                    {
                        "id": 1,
                        "publish": True,
                        "author": "Riot Games",
                        "publish_locations": ["game"],
                        "translations": [{"locale": "en_US", "content": "We are investigating."}],
                        "created_at": "2026-11-21T12:00:00+00:00",
                        "updated_at": None,
                    },
                ],
                "platforms": ["windows"],
                "created_at": "2026-11-21T12:00:00+00:00",
                "updated_at": None,
            },
        ],
    }


class SnippetSandbox:
    """Mock Riot routes plus the identity roster they share."""

    def __init__(self) -> None:
        self.identities: dict[tuple[str, str], Identity] = {}
        self.requests: list[str] = []
        for index, (game_name, tag_line, champion_name, champion_id) in enumerate(_ROSTER, start=1):
            identity = _identity(game_name, tag_line, champion_name, champion_id, index)
            self.identities[(game_name.casefold(), tag_line.casefold())] = identity

    # -- roster -----------------------------------------------------------------

    def identity_for(self, game_name: str, tag_line: str) -> Identity | None:
        """Resolve a Riot id to its roster persona, or None when the fixture says it is missing."""
        key = (unquote(game_name).casefold(), unquote(tag_line).casefold())
        if key in _MISSING_ACCOUNTS:
            return None
        identity = self.identities.get(key)
        if identity is None:
            identity = _spare_identity(key[0], key[1], len(self.identities) + 1)
            self.identities[key] = identity
        return identity

    def identity_by_puuid(self, puuid: str) -> Identity | None:
        return next((identity for identity in self.identities.values() if identity.puuid == puuid), None)

    @property
    def roster(self) -> list[Identity]:
        return sorted(self.identities.values(), key=lambda identity: identity.participant_id)

    # -- registration -----------------------------------------------------------

    def register(self, mock: aioresponses) -> None:
        """Register every route the snippets reach, most specific patterns first."""
        routes: tuple[tuple[str, Any], ...] = (
            (rf"{BASE_URL}/riot/account/v1/accounts/by-riot-id/[^/?]+/[^/?]+", self._account_by_riot_id),
            (rf"{BASE_URL}/riot/account/v1/accounts/by-puuid/[^/?]+", self._account_by_puuid),
            (rf"{BASE_URL}/lol/summoner/v4/summoners/by-puuid/[^/?]+", self._summoner),
            (rf"{BASE_URL}/lol/match/v5/matches/by-puuid/[^/?]+/ids", self._match_ids),
            (rf"{BASE_URL}/lol/match/v5/matches/(?!by-puuid)[^/?]+/timeline", self._timeline),
            (rf"{BASE_URL}/lol/match/v5/matches/(?!by-puuid)[^/?]+", self._match),
            (rf"{BASE_URL}/lol/league/v4/entries/by-puuid/[^/?]+", self._league_entries),
            (rf"{BASE_URL}/lol/league/v4/challengerleagues/by-queue/[^/?]+", self._challenger_league),
            (rf"{BASE_URL}/lol/league/v4/entries/[^/?]+/[^/?]+/[^/?]+", self._division_page),
            (rf"{BASE_URL}/lol/league-exp/v4/entries/[^/?]+/[^/?]+/[^/?]+", self._division_page),
            (
                rf"{BASE_URL}/lol/champion-mastery/v4/champion-masteries/by-puuid/[^/?]+/by-champion/[^/?]+",
                self._mastery_by_champion,
            ),
            (rf"{BASE_URL}/lol/champion-mastery/v4/champion-masteries/by-puuid/[^/?]+/top", self._top_masteries),
            (rf"{BASE_URL}/lol/champion-mastery/v4/champion-masteries/by-puuid/[^/?]+", self._masteries),
            (rf"{BASE_URL}/lol/champion-mastery/v4/scores/by-puuid/[^/?]+", self._mastery_score),
            (rf"{BASE_URL}/lol/challenges/v1/challenges/config", self._challenge_configs),
            (rf"{BASE_URL}/lol/challenges/v1/challenges/[^/?]+/percentiles", self._challenge_percentiles),
            (
                rf"{BASE_URL}/lol/challenges/v1/challenges/[^/?]+/leaderboards/by-level/[^/?]+",
                self._challenge_leaderboard,
            ),
            (rf"{BASE_URL}/lol/challenges/v1/player-data/[^/?]+", self._challenge_player_data),
            (rf"{BASE_URL}/lol/platform/v3/champion-rotations", self._rotations),
            (rf"{BASE_URL}/lol/status/v4/platform-data", self._platform_status),
        )
        for pattern, callback in routes:
            mock.get(re.compile(pattern), callback=callback, repeat=True)

    # -- route callbacks --------------------------------------------------------

    @staticmethod
    def _missing() -> CallbackResult:
        return _result(
            {"status": {"status_code": 404, "message": "Data not found - summoner not found"}},
            status=404,
        )

    def _account_by_riot_id(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        found = re.search(r"/accounts/by-riot-id/([^/?]+)/([^/?]+)", str(url))
        if found is None:
            return self._missing()
        identity = self.identity_for(found[1], found[2])
        if identity is None:
            return self._missing()
        return CallbackResult(
            payload={"puuid": identity.puuid, "gameName": identity.game_name, "tagLine": identity.tag_line},
        )

    def _account_by_puuid(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        found = re.search(r"/accounts/by-puuid/([^/?]+)", str(url))
        identity = self.identity_by_puuid(found[1]) if found else None
        if identity is None:
            return self._missing()
        return CallbackResult(
            payload={"puuid": identity.puuid, "gameName": identity.game_name, "tagLine": identity.tag_line},
        )

    def _summoner(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        found = re.search(r"/summoners/by-puuid/([^/?]+)", str(url))
        identity = self.identity_by_puuid(found[1]) if found else None
        if identity is None:
            return self._missing()
        return _result(payload=summoner_payload(identity))

    def _match_ids(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=list(_MATCH_IDS))

    def _match(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        found = re.search(r"/matches/(?!by-puuid)([^/?]+)", str(url))
        match_id = unquote(found[1]) if found else _MATCH_IDS[0]
        return _result(payload=match_payload(match_id, self.roster))

    def _timeline(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        found = re.search(r"/matches/(?!by-puuid)([^/?]+)/timeline", str(url))
        match_id = unquote(found[1]) if found else _MATCH_IDS[0]
        return _result(payload=timeline_payload(match_id, self.roster))

    def _league_entries(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        found = re.search(r"/entries/by-puuid/([^/?]+)", str(url))
        identity = self.identity_by_puuid(found[1]) if found else None
        if identity is None:
            return self._missing()
        return _result(payload=[league_entry_payload(identity)])

    def _challenger_league(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=apex_league_payload(self.roster))

    def _division_page(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=[league_entry_payload(identity) for identity in self.roster[:5]])

    def _masteries(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        found = re.search(r"/by-puuid/([^/?]+)", str(url))
        identity = self.identity_by_puuid(found[1]) if found else None
        if identity is None:
            return self._missing()
        return _result(
            payload=[
                champion_mastery_payload(puuid=identity.puuid, championId=identity.champion_id, championPoints=127530),
                champion_mastery_payload(puuid=identity.puuid, championId=103, championPoints=64100),
            ],
        )

    def _top_masteries(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        found = re.search(r"/by-puuid/([^/?]+)", str(url))
        identity = self.identity_by_puuid(found[1]) if found else None
        if identity is None:
            return self._missing()
        return _result(payload=[champion_mastery_payload(puuid=identity.puuid, championId=identity.champion_id)])

    def _mastery_by_champion(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        found = re.search(r"/by-puuid/([^/?]+)/by-champion/([^/?]+)", str(url))
        identity = self.identity_by_puuid(found[1]) if found else None
        if identity is None or found is None:
            return self._missing()
        return CallbackResult(
            payload=champion_mastery_payload(
                puuid=identity.puuid,
                championId=int(found[2]),
                chestGranted=True,
            ),
        )

    def _mastery_score(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=157331)

    def _challenge_configs(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=challenge_config_payload())

    def _challenge_percentiles(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=challenge_percentiles_payload())

    def _challenge_leaderboard(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=challenge_leaderboard_payload(self.roster))

    def _challenge_player_data(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=challenge_player_data_payload())

    def _rotations(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=champion_rotations_payload())

    def _platform_status(self, url: object, **_: object) -> CallbackResult:
        self.requests.append(str(url))
        return _result(payload=platform_status_payload())
