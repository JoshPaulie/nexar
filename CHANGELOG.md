# Changelog

All notable changes to this project will be documented in this file.

## Unreleased

### Changed

- **Breaking:** Rate limiter rewritten as a sliding-window log that mirrors Riot's documented enforcement. Batches now run at the full documented quota (e.g. 12 match fetches in ~1s instead of ~14s under the previous burst=1 buckets). `RateLimiter.acquire()` no longer takes a `method` argument. Method and service rate limit headers are no longer tracked — the application window always binds first at every key tier, so tracking them cannot change behavior.
- On a 429 without a parseable `Retry-After` header, the region is now blocked for a conservative 5s default instead of retrying unpaced.
- `aiolimiter` dependency removed; rate limiting is now stdlib-only.
- `aiohttp-client-cache` narrowed to the `sqlite` extra — aioboto3, motor, redis and friends no longer land in the lockfile of a SQLite-only SDK.
- `ruff` is now a declared dev dependency, so a clean checkout can run `just check`.
- `Participant.placement` and `Participant.summoner_name` are now `int | None` / `str | None` (parsed to `None` when Riot omits them).
- `Perks.styles`, `PerkStyle.selections` and `Challenges.legendary_item_used` are tuples now, so those frozen dataclasses are hashable.
- `ChampionStats.avg_kda` now treats a zero-death record as a perfect KDA instead of returning `0.0`.
- `Objectives.horde` is now `Objective | None` (pre-14.1 matches have no Voidgrubs), a new optional `Objectives.atakhan` field parses the 2025-season objective, and `Team.bans`, `TeamInfo.bans` and `TeamInfo.participants` are tuples now, making `Team` hashable.
- `LeagueEntry.division` gains a `RankDivision.EMPTY` member for apex and decayed entries, which Riot sends without a `rank`.
- `MatchInfo.game_duration` is now documented and normalized as seconds: a payload from before patch 11.20 (reported in milliseconds) is divided by 1000 at parse time.

### Removed

- `RateLimiter.update_from_headers()` and `RateLimiter.dump_state()`.
- `NexarClient._extract_method_id()` (the limiter no longer tracks per-method limits).

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
