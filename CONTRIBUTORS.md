# Contributing

Features requests should start as issues. Bugs may start as PRs.

```sh
# Fork the repo

# Clone fork locally
git clone https://github.com/username/nexar

# Make changes on branch

# Ensure functionality and new tests if needed

# Ensure tests are still passing

# Make PR
```

## Running Tests

Tests are mocked by default. The standard suite replays recorded API responses through
`aioresponses` (see the `client` fixture in `tests/conftest.py`), so it needs no Riot API key and
makes no network calls:

```bash
uv run pytest tests -q
```

A smaller set of integration tests hit the real Riot API. The live ones are marked
`@pytest.mark.slow` (registered in `pyproject.toml`), and every test that needs a real key asks for
the `riot_api_key` fixture, which calls `pytest.skip` when `RIOT_API_KEY` is unset — so those tests
skip silently rather than fail, and the suite stays green on a machine with no key.

To run the live tests too:

1. Copy `riot-key.sh.example` to `riot-key.sh` (gitignored) and add your key
2. Run the suite with the provided script:

```bash
./run_tests.sh
```

The script sources `riot-key.sh` before invoking `pytest`, which is what makes the live tests run.

## Live Test Requirements

- Valid Riot API key exposed as `RIOT_API_KEY` (normally sourced from `riot-key.sh`)
- Active internet connection
- Live calls are paced by the client's rate limiter and may be slowed by Riot's API

## LLMs and the project

Tests, transforming the API response schemas to models, and other large scale chores were contributed by an assortment of LLMs. The client, cache, rate limiter, and accompanying logic were written by hand, and likely much worse for it. Rest easy knowing this was mostly created by a fallible human, as `$DEITY` intended.

For some reading on how AI almost ruined this project, check out the [llm post-mortem](docs/llm-post-mortem.md).

### LLM Contributions

Used sparingly, and in the same fashion as above, it would hypocritical to not allow LLM contributions. But vibe coded, unchecked, slop may result in ban.
