# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Added

- README: the Objective now carries the SDK-vs-wrapper reasoning (region routing, epoch timestamps, omitted fields) instead of asserting it, the rate-limiting bullet names the sliding window that mirrors Riot's documented enforcement, and the pre-Riot-IDs nostalgia line is gone, with the one-call `get_player` demo kept; a new Docs section links the quick start, API surface, worked examples, reference, FAQ, and the hosted docs site. Every wrapped Riot op is listed with its client method and return type on its own page, `docs/reference/api-surface.md` (mkdocs nav under Reference), so the README carries links instead of tables.

- Ranked ladder, rotation, and status coverage — the next coverage step after the match timeline: `NexarClient.get_challenger_league`, `get_grandmaster_league`, and `get_master_league` return a typed `LeagueList` whose entries are puuid-keyed `LeagueItem`s (the live apex payloads carry no `leagueId`, no `name`, and no summoner-era fields — measured before modeling, the DTO tables still lag); `get_league_entries` and `get_league_exp_entries` page through the division ladders (205 players per page, measured from the live wire since the current reference op block no longer states a page size) and parse into the existing by-puuid `LeagueEntry`, whose recorded shape they share exactly; `get_champion_rotations` returns `ChampionRotations` with the wire's `sr`/`newplayer` keys preserved; and `get_platform_status` returns `PlatformStatus` with maintenances, incidents, and localized updates (this op sends explicit nulls, so timestamps parse to aware datetimes or `None`). Smart cache TTLs follow the data: ladders ride the 5-minute league class, rotations 1 day, status 1 minute — all pinned through the library's own `CacheActions` resolution. league-exp-v4 is wrapped by no other live Python SDK in the 2026-11-20 peer survey (pulsefire, RiotWatcher, Cassiopeia source clones); the de-listed `leagues/{leagueId}` op stays out, and none of this is player-centric, so no `Player` seam was added.

- LoL Challenges API coverage, all six current ops: `get_all_challenge_configs` (405 challenges on NA at recording; the wire sends `id`/`localizedNames`/`state`/`leaderboard`/`thresholds` on every entry and `endTimestamp` on exactly one — challenge 600012, surfaced by the review pass against the recorded payload — so `ChallengeConfig` carries a nullable `end_timestamp`; the DTO table's `tracking` and `startTimestamp` never appear), `get_challenge_config`, `get_all_challenge_percentiles` and `get_challenge_percentiles` (flat challengeId→level→percentile maps; the reference's triple-nested `Map[Long, Map[Integer, ...>>` does not exist on the wire), `get_challenge_leaderboard` (apex levels serve — MASTER/GRANDMASTER/CHALLENGER; the other ten legal `ChallengeLevel` values buy a 400 on the live wire, measured 2026-11-21, so an enum input for a non-apex level raises before the wire call while raw strings pass through; the optional `limit` truncates; positions are global across tiers and arrive ascending), and `get_player_challenge_data` plus the `Player.get_challenge_data()` seam. Models live in `nexar.models.challenge`, distinct from the match payload's `Challenges` stats model: `ChallengeConfig` (with `LocalizedChallengeNames` per locale), `ChallengeLeaderboardEntry`, `PlayerChallengeData` (`ChallengeProgress`, `ChallengePoints` — the wire spells the percentile key correctly; the DTO table's `precentile` is a doc typo — and `ChallengePreferences`), plus the `ChallengeLevel` enum. All six route per-platform (`na1.api.riotgames.com`) like summoner/mastery — the americas/europe/asia regional hosts answer 403 for this family (measured; Riot's spec consts agree), unlike account-v1. Smart TTLs follow the data: configs and percentiles 6 hours, leaderboards the 5-minute ladder class, player-data the 30-minute mastery class — pinned through `CacheActions` resolution with no-shadow proofs, and exact-URL offline tests plus a live canary (one account lookup, then the six ops and the limit variant on one region) cover it.

- Match timeline support: `NexarClient.get_match_timeline` parses the match-v5 timeline into typed `Timeline` models — per-minute `TimelineParticipantFrame` snapshots with champion and damage stats, and a `TimelineEvent` flat union covering every event type and field observed on the live op (Riot's reference documents only the three common event fields; per-type keys like `assistingParticipantIds` and the champion-kill victim damage breakdowns were verified against a real payload). `Timeline.frames_for(puuid)` returns one player's per-minute snapshots and `Timeline.events` flattens the stream; the URL rides the existing immutable match cache glob, and exact-URL offline tests plus a live canary (account, match ids, one timeline) cover it.

- Champion Mastery support, current puuid-only surface: `NexarClient.get_champion_masteries`, `get_champion_mastery`, `get_top_champion_masteries`, and `get_champion_mastery_score`, plus `Player.get_champion_masteries()`. Responses parse into typed `ChampionMastery` models (milestone fields included), with 30-minute smart cache TTLs and live canaries covering all four endpoints.

- `get_top_champion_masteries` accepts an optional `count` parameter (Riot's reference default is 3) — surfaced by the review pass, verified against the live reference, and pinned by an exact-URL test plus a live canary row.

- `Region.ME1` (Middle East & North Africa) joins the platform routing: verified live via a 200 from `me1.api.riotgames.com` and against Riot's spec consts, and routed through the `europe` cluster for both account and match lookups. The local mirror of Riot's routing table gains the row the upstream docs page has not published yet.

- Docs snippets are now gated like source: ruff (lint and format) runs on `docs/` in the local gates and CI, mypy covers `docs/snippets` via the `files` array in `pyproject.toml`, and a parametrized test imports every snippet module offline with a dummy key — a snippet referencing removed or misused API fails the suite instead of shipping in the docs.

- `__all__` is now declared in the six leaf modules (`client`, `cache`, `enums`, `exceptions`, `rate_limiter`, `utils`), so scoped imports autocomplete only the public API — implementation constants (`HTTP_*` status shortcuts, match-id defaults) are deliberately excluded, and the surface baseline was refreshed with `UPDATE_BASELINE=1` in the same commit.
- `tests/test_structure.py` guardrails: a pinned public-API surface baseline (`tests/api_baseline.json`, refresh via `UPDATE_BASELINE=1` in the same commit as a surface change), file and function size budgets, and seam tests forbidding underscore access across module boundaries.

### Changed

- `NexarClient` is assembled from per-topic mixins — `client_identity`, `client_league`, `client_platform`, `client_challenges`, `client_match`, and `client_plumbing` — over the shared declarations in `nexar.core`; `from nexar.client import NexarClient` and `CallStats` import exactly as before, with the client's internal `HTTP_*` status constants now living in `client_plumbing` and the match-id defaults in `client_match`, both pinned by the API baseline.

- The lint config ignores the rules ruff's own formatter docs list as conflicting (`COM812`, `COM819`, `D206`, `D300`, `Q000`–`Q004`, `W191`, and the preview-only `E111`/`E114`/`E117`), so `ruff format` runs warning-free and the linter no longer hands back diffs the formatter reverses. Nothing in the tree violated them; the change is future-proofing the layout gate.

- The type gate is `ty` (pinned `0.0.42`) instead of `mypy --strict`, and it runs over the whole tree — `src`, `tests`, `scripts`, and `docs/snippets` — with `--error-on-warning`, so a stale `ty: ignore` fails like any other diagnostic. ty resolves `aiohttp_client_cache`'s `CachedSession`, which mypy erased to `Any` (the library builds its mixin base in an `if`/`else`); the switch surfaced one real defect: a cached row with an empty body decodes to `None` on the cache-hit path and is now treated as a miss instead of a dict.

- The logging snippet is renamed `client-features/log_config.py`: a snippet named `logging.py` resolves `import logging` to itself under mypy's basename module naming, and is a `sys.modules` shadow hazard for anything that imports it unqualified (the four `--8<--` markers in `docs/client-features/logging.md` follow the rename).

- Internal: client call counters are now keyed from the `CallStats` field definitions instead of a hand-maintained dict, and the redundant in-method `Player` imports were removed.

- Internal: `NexarClient.get_player()` now forwards to `Player.create`, which owns the identification dispatch alone; `Player.by_riot_id()` forwards to it as well.

- Internal: the batch partition behind `get_players` and `Player.get_matches` is now one helper, `nexar.exceptions.gather_partitioned`, which routes captured `BaseException` results to the error side (the `get_players` variant previously checked the narrower `Exception`).

### Removed

- `HTTP_OK`, the one wire-status constant with no caller anywhere (importable from `nexar.client` in v2.0.0 but never referenced by the SDK, a test, or a doc) — the plumbing split surfaced it, and the API baseline records the removal in the same commit.

- `Region.PH2` and `Region.TH2` (with their `PlatformId` aliases) — Riot migrated the Philippines and Thailand platforms into SG2 on 2025-01-08, and both are absent from the reference's executable region list, so nexar tracks the current surface. The routing-table mirror drops both rows ahead of the upstream docs page, which still lists them.

### Fixed

- Adversarial review pass on the ladder/rotations/status slice: explicit nulls now parse like absences on the status op's models and their rotations/league-list siblings — this op demonstrably sends nulls, and `tuple(data.get(key, ()))` was `tuple(None)` waiting to raise, so every status, rotation, and apex-entries field guards with `or` and null-feeding tests pin it; the league-exp docstring's "byte-identical" claim is corrected to what the recordings actually show (same 205-player page in the same order, with per-player LP/win values drifting between the two fetches — one index differs); the master docstring no longer mislabels the measured 10,000 as an LP cutoff (it is the entry count); the cache comment on the division glob now states the real no-shadow mechanism — two literal slashes after `/entries/` versus the one a by-puuid URL carries, verified through the library's own `url_match` — and a unit test proves it structurally by resolving a by-puuid URL against the division glob alone (it falls through to the session default, where the old full-dict assertion could not tell shadowing from matching); the unpinned paths are pinned (apex-tier rejection over all three apex tiers, pre-sorted LP over all three apex ladders, a `LeagueItem` mini-series value, the by-design `ValueError` on an unknown tier); and the status snippet no longer labels the first update it prints as the latest.

- The timeline example snippet guards its frame-series indexing against an empty `frames_for` result (a puuid not in the timeline), matching the guard the champion-mastery snippet already carries — an empty series now prints a message instead of raising IndexError mid-example.

- Internal: the timeline test helper now carries the recording's real end-of-game snapshots and one real event of each salient type — its second frame previously duplicated minute-one stats under a 26-minute timestamp (the asserted gold curve read 500, 500, a pair that cannot occur), and the champion kill dropped the teamfight breakdown the recorded payload keeps. Every field the first review listed gained a recorded value point, pinned so a parser constant or fixture-mixing regression fails the suite (verified by mutation on a tree copy).

- Internal: a second adversarial review pass found the gaps the first could not see, now closed: the champion-kill victim damage *dealt* breakdowns (previously unpinned — a wire-key typo would have shipped silently) are pinned by the recording's four-breakdown kill, which also carries a nonzero `killStreakLength` and a real assists list; `ITEM_SOLD` (in no fixture before) and the three types only the shared fixture carries (`TURRET_PLATE_DESTROYED`, `WARD_KILL`, `ITEM_DESTROYED`) gain recorded value assertions, so all 17 event types the live payload showed are now asserted somewhere; and the helper's final frame lists its cherry-picked events sorted by timestamp, as the wire always frames them. One residual is documented rather than pinned: `afterId` — all eight ITEM_UNDO events in the recording carry 0, so no distinguishing value exists in this match's data.

- Timeline model corrections from the adversarial review pass: `TimelineParticipantFrame.time_enemy_spent_controlled` is documented in milliseconds (the wire value; "seconds" was a 1000x mislabel — this field is not `timeCCingOthers`), the `attack_speed` docstring no longer invents a unit the reference never declares, and `TimelineInfo` now `.get`-hardens its `participants`/`frames` arrays so a payload that omits an empty array parses instead of raising (only `gameId` stays a direct identity read).

- The match-v5 cache glob (`*/lol/match/v5/matches/*`, which timeline URLs also ride) now carries `-1`, aiohttp-client-cache's never-expire sentinel — its `None` value was skipped by the library's expiration coalescing, so "cached forever" rows (match detail and timeline alike) actually expired after the 1-hour session default since the row landed. The effective expiry is now pinned by a unit test resolved through the library's own `CacheActions` path.

- The champion-mastery example snippet guards its single-champion lookup against an empty mastery list, so an account with no masteries no longer raises IndexError mid-example (score still prints, as the scores endpoint works regardless).

- Snippet fixes surfaced by the new gates: the two client-features snippets that fetched `RIOT_API_KEY` at module level now guard inside `main()` (module-level narrowing does not survive into function bodies, so the old pattern failed strict mypy), `match_list_stats.py` guards `participant.challenges` before reading `gold_per_minute` (the same pre-2022 `AttributeError` class the `get_average_stat` docstring guards against), and `league_comparison.py` dropped an unused `Region` import.

- `get_cache_info()` now reports a real `cached_responses` row count via the cache storage's `size()` instead of a structurally-zero `hasattr` probe; the never-present `cache_size` key was dropped.

## [2.0.0] - 2026-11-19

### Changed

- **Breaking:** Rate limiter rewritten as a sliding-window log that mirrors Riot's documented enforcement. Batches now run at the full documented quota (e.g. 12 match fetches in ~1s instead of ~14s under the previous burst=1 buckets). `RateLimiter.acquire()` no longer takes a `method` argument. Method and service rate limit headers are no longer tracked — the application window always binds first at every key tier, so tracking them cannot change behavior.
- On a 429 without a parseable `Retry-After` header, the region is now blocked for a conservative 5s default instead of retrying unpaced.
- `aiolimiter` dependency removed; rate limiting is now stdlib-only.
- `aiohttp-client-cache` narrowed to the `sqlite` extra — aioboto3, motor, redis and friends no longer land in the lockfile of a SQLite-only SDK.
- `ruff` is now a declared dev dependency, so a clean checkout can run the lint gates via `uv`.
- `Participant.placement` and `Participant.summoner_name` are now `int | None` / `str | None` (parsed to `None` when Riot omits them).
- `Perks.styles`, `PerkStyle.selections` and `Challenges.legendary_item_used` are tuples now, so those frozen dataclasses are hashable.
- `ChampionStats.avg_kda` now treats a zero-death record as a perfect KDA instead of returning `0.0`.
- `Objectives.horde` is now `Objective | None` (pre-14.1 matches have no Voidgrubs), a new optional `Objectives.atakhan` field parses the 2025-season objective, and `Team.bans`, `TeamInfo.bans` and `TeamInfo.participants` are tuples now, making `Team` hashable.
- `LeagueEntry.division` gains a `RankDivision.EMPTY` member for apex and decayed entries, which Riot sends without a `rank`.
- `MatchInfo.game_duration` is now documented and normalized as seconds: a payload from before patch 11.20 (reported in milliseconds) is divided by 1000 at parse time.
- **Breaking:** `Player.get_matches` now raises `BatchError` carrying the successfully fetched matches when any match id fails, instead of discarding the whole batch with a bare `NotFoundError` (mirrors `get_players`).
- **Breaking:** `TeamInfo`/`TeamsInfo` removed — dead public API that nothing in the SDK constructed; the `Team`/`Ban`/`Objective` parse contracts survive as `tests/unit/test_team_parse.py`.
- **Breaking:** unknown `queueType` strings in league entries map to `Queue.UNKNOWN` (raw string preserved in `queue_type_raw`) instead of conflating new ranked queues with `Queue.CUSTOM`.
- An unrecognized participant position value degrades to `EMPTY` with a warning instead of aborting the whole match parse, mirroring the `Queue`/`MapId` UNKNOWN sentinels.
- `Participant.from_api_response` is table-driven: one `(api_name, python_name, default)` row per omissible field replaces ~160 lines of triple bookkeeping, with a sync test pinning the table to the dataclass fields.
- The unreachable `from_cache` accounting branch in `_make_api_call` is deleted; `_try_cache_response` stays and is documented as load-bearing (cache hits skip the rate limiter, which the library's own cache interception cannot do).
- `NexarClient._ensure_session()` returns the session, so the unreachable "session not initialized" `RuntimeError` and its seam-only test are gone; retry-exhaustion messages say "attempts", 4xx responses log one warning line instead of a full ERROR traceback, and a `Retry-After` that parses as NaN/inf falls back to the 5s default.
- Riot-ID parsing is one `_parse_riot_id` helper shared by `Player.create` and `Player.by_riot_id` (the two hand-copies had already diverged in error wording), and the `get_player`/`Player.create` docstrings state the real first-supplied-wins contract.
- The memory cache backend is a real `CacheBackend` (with its default in-memory storage) — a bare `DictCache` is a storage, not a backend, and `CachedSession` silently swapped the falsy object for a default, dropping the smart-TTL and 200-only wiring.
- Unreadable sqlite cache rows are dropped as misses across the full unpickle failure set (`CookieError`, `UnpicklingError`, `EOFError`, `sqlite3.Error`), not just poisoned cookies.
- `Queue.is_ranked` derives from `get_ranked_queues()`, the limiter seed mutates the admission deque in place, `MatchList`/`ParticipantList.__getitem__` drop their defensive isinstance branches, and the batch gathers zip `strict=True`.
- Docs: all 30 snippet include markers use the `--8<--` form and a CI step rejects the one-dash variant; the request-lifecycle diagram documents the current limiter; reference pages added for enums, exceptions, cache, rate limiting and `MatchList`; the aiolimiter prose is gone from the landing pages.
- One test entry point: `run_tests.sh` without the `--maxfail` stop-at-first-failure flag, the justfile is gone, and the lint gates run on `src` and `tests` both locally and in CI.

### Removed

- `RateLimiter.update_from_headers()` and `RateLimiter.dump_state()`.
- `NexarClient._extract_method_id()` (the limiter no longer tracks per-method limits).
- `tests/generate_mocks.py` — it wrote a snake_case shape the parsers reject and manufactured the seconds-vs-milliseconds `revisionDate` fixture bug; `tests/mock_responses.json` is recorded payload data (see `tests/README.md`).
- `justfile` and the `just` entry-point references (`just` was installed nowhere and declared nowhere).

### Added

- `Participant.get_player(client, *, region=None)` — async method to get a `Player` from a match participant via PUUID.
- Restart orientation: every fresh response hands Riot's `X-App-Rate-Limit-Count` to the limiter, which pre-fills its window log once per region — rerunning a script within 2 minutes of a heavy run no longer re-bursts into a partially spent quota (the cold-start 429 hole).
- CI now runs tests, mypy and ruff on every pull request and push to main, gating the docs deploy; Python is pinned to 3.13 in both jobs.

### Fixed

- `ruff check src` now passes on a clean checkout: D213 (the other half of the D212 docstring toggle) is ignored, and `NexarClient.__aenter__` is typed as `Self` (PYI034).
- Participants and perks now parse with sane defaults when Riot omits zero-valued keys (Riot includes only non-empty values), instead of raising `KeyError` — including `placement`, `summonerName`, `statPerks`, perk vars and zero-stat pings.
- `Objectives` no longer requires `horde`: pre-14.1 matches parse with `horde=None` and the new optional `atakhan` parses when Riot sends it.
- `LeagueEntry` now tolerates omitted `leaguePoints`/`wins`/`losses` (defaulting to 0) and empty or missing `rank` (mapped to `RankDivision.EMPTY`), so apex and decayed entries parse instead of raising.
- `MatchInfo.game_duration` is normalized to seconds at parse time (pre-11.20 matches were reported in milliseconds and inflated `MatchList.get_performance_stats` averages ~60x).
- The `get_average_stat` docstring example now guards participants with no `challenges` block (pre-2022 matches) instead of raising `AttributeError`, and a test executes the documented example so it cannot rot again.
- `MatchList.get_performance_stats` treats a zero-death match list as a perfect KDA instead of returning `0.0`.
- `get_api_call_stats().errors` now counts 404, 401 and 403 responses, which previously vanished from the error total.
- `Player.get_recent_performance_by_role` reports participants with an empty team position under `UNKNOWN` instead of an empty role key, and treats zero-death role records as a perfect KDA instead of `0.0`.
- `LeagueEntry` tolerates a missing `leagueId` — the live by-puuid entries endpoint no longer returns it — defaulting `league_id` to an empty string instead of raising `KeyError`.
- `scripts/update_readme_example.py` now refuses to rewrite the README when the example run fails or prints untrustworthy output, instead of silently blanking the Example Output section; `README_example.py` uses keyword-only `get_player` and `participant.kda` (no `challenges` dependency), and the README block is regenerated from a real run.
- The README's test guidance now describes both paths accurately: mocked tests are the default and need no key, live tests run only with `RIOT_API_KEY` and skip silently without it; the Installation section states the Python 3.13 floor, and mkdocs builds strictly so missing snippet files fail the deploy.
- `riot-key.sh.example` is now a copy-me template: the header warns to copy it to the gitignored `riot-key.sh` instead of editing the tracked file, and it prompts for the key with `read` rather than storing one inline.
- `sort_players_by_rank`'s docstring example and `ValueError` message now name the real `ranked_queue_type` parameter instead of `queue_type`.
- The test suite no longer stops at the first failure: the forced `maxfail` override (and a dead xdist `numprocesses` option) are gone from `tests/conftest.py`, so a failing run reports every failure.
- Mocked tests no longer read or write the shared `~/.nexar` dogfood cache — every test client now uses an isolated cache, so a stale or cookie-poisoned dogfood cache can never satisfy or break a test.
- The suite now enforces a 95% coverage floor (measured at 95.35% keyless), so coverage regressions fail the run.
- The sqlite cache no longer stores cookies — Riot's Cloudflare `Partitioned` cookie made rows unreadable and crashed every later cache read — and a row that still fails to load is dropped and refetched, so an already-poisoned cache heals itself.
- The mock fixture stored `summoner.revisionDate` in seconds while the parser divides by 1000, so every mocked summoner parse silently reported a 1970 revision date — the fixture now carries the recorded milliseconds and the parse is pinned by an exact-value test.
- The suite was pruned against the 2026-11 audit: ~51 probe-proven vacuous tests deleted, ~45 rows collapsed into ~10 parametrized tables, ~25 rewritten at stronger boundaries (exact-URL match-ids, value-level performance stats, offline win-streak and top-champions rows, populated-then-cleared cache tests, behavioral `app_rate_limits` pacing); 271 collected tests became 239 and the coverage floor was re-baselined to the measured 96.91% keyless (`fail_under` 96).

## [1.1.0] - 2026-05-17

> [!WARNING]
> This release includes breaking changes. Please review the "Changed" section carefully before upgrading. [^1]

### Added

- `get_riot_account_by_puuid(puuid, *, region)` — new public client method for account lookup by PUUID.
- `get_player()` and `Player.create()` now accept three identification patterns:
  - `get_player(game_name="...", tag_line="...")` — by game name + tag line (unchanged)
  - `get_player(puuid="...")` — by PUUID
  - `get_player(riot_id="name#tag")` — by Riot ID string
- Gracefully handle unknown `Queue` and `MapId` enum values from the Riot API.
- Add `Participant.kda()`. Not all matches return a participant's "challenges", despite participants from matches of all gamemodes having kills, deaths, and assists. This is a useful convenience method for a common statistic. By default it returns a ratio float, but can return a formatted string if `as_str=True` is passed (e.g. "10/2/5").

### Changed

- **Breaking:** `get_player()` and `Player.create()` are now keyword-only. Use `get_player(game_name="...", tag_line="...")` instead of `get_player("...", "...")`.
- **Breaking:** Remove `Participant.kda_string` property. Use `Participant.kda(as_str=True)` instead.

### Fixed

- Make `challenges`, `perks`, and `missions` fields optional on `Participant` to prevent deserialization errors.

### Wrapped API Endpoints

- **Account API**
  - `GET /riot/account/v1/accounts/by-puuid/{puuid}` → `RiotAccount` (via `get_riot_account_by_puuid`)

## [1.0.0] - 2026-05-14

Initial release.

### Added

- Persistent (SQLite) and in-memory caching for API responses with configurable TTLs and per-endpoint smart TTLs.
- In-memory rate limiter supporting app, method, and service limits per region, with per-region locking to prevent race conditions.
- Pre-configured rate limits for both personal and production API keys.
- Automatic retries for rate limit errors with Retry-After header parsing.
- Configurable HTTP timeout support exposed via `CacheConfig`.
- `BatchError` exception to collect and report all errors when using `get_players()`.
- `team_total_percentage()` utility function.
- Dataclasses for all API response models with type hints, docstrings, and helper methods.
- High-level `Player` object with lazy-loaded summoner, league entries, and match history.
- `ParticipantList` and `MatchList` specialized list classes with filtering and stats methods.
- `sort_players_by_rank()` utility for comparing players by ranked queue standing.
- Champion and performance stats aggregation.
- Convenience properties: `Participant.kda()`, `Participant.creep_score`, `Participant.champion_icon_url`, `Summoner.profile_icon_url`.
- `NEXAR_DEBUG_RESPONSES` environment variable for debugging API responses.

### Wrapped API Endpoints

- **Account API**
  - `GET /riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}` → `RiotAccount`
- **Summoner API**
  - `GET /lol/summoner/v4/summoners/by-puuid/{puuid}` → `Summoner`
- **League API**
  - `GET /lol/league/v4/entries/by-puuid/{puuid}` → `list[LeagueEntry]`
- **Match API**
  - `GET /lol/match/v5/matches/{match_id}` → `Match`
  - `GET /lol/match/v5/matches/by-puuid/{puuid}/ids` → `list[str]`
- **Convenience Methods**
  - `client.get_player(game_name, tag_line)` → `Player`
  - `client.get_players(riot_ids)` → `list[Player]`

---

[^1]: Pretending to have users is fun :)
