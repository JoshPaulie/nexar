# Tests

## Running

One entry point for live runs, plain `uv` for offline runs:

```sh
uv run python -m pytest tests -q -m "not slow"  # mocked only (fast, no key needed)
./run_tests.sh                                  # full suite incl. live Riot API calls (slow)
```

CI runs the mocked suite, mypy (on `src` plus the docs snippets), and ruff on `src`, `tests`, and `docs` directly via `uv`.

## Markers

| Marker | Description |
|--------|-------------|
| `slow` | Makes real Riot API calls. Deselect with `-m "not slow"` for an instant offline run. |

## Recorded payloads

`tests/mock_responses.json` holds **recorded payloads captured from real API
responses** — it is checked-in fixture data, not a generated artifact. Do not
regenerate it by script: the old `generate_mocks.py` wrote a snake_case shape
the parsers reject and a `revisionDate` in seconds that silently broke the
ms-to-datetime parse (found in the 2026-11 audit). To add coverage for a new
endpoint, record the real `response.json()` by hand and keep the raw
camelCase shape exactly as Riot sent it.

## Quota lock

Before `slow` tests run, the session fixture checks `/tmp/nexar-last-ran.txt`. If fewer than 125 seconds have elapsed since the last dogfood bowl or integration test run, it sleeps for the remainder — ensuring the rate limiter starts with a full quota window.
