"""Every docs snippet runs end to end against mocked Riot routes.

An import-only gate let a snippet whose ``main()`` crashes at runtime ship in
the docs: a missing ``default_region``, an error label parsed as a number, a
lookup that silently returns an empty list. This gate executes each snippet's
``main()`` (module body where there is no ``main``) against
``tests/payloads/sandbox.py``, so runtime-only breakage is red before publish.

The gate owns the sandbox, not the snippets: the snippet files stay verbatim,
while ``HOME`` is redirected, the process chdirs into a temp dir, and the
construction-time cache default is replaced -- a no-arg client must never read
or write the real ``~/.nexar`` cache, where a warm row would answer the snippet
without ever reaching the mock.
"""

import asyncio
import contextlib
import importlib.util
import logging
import sys
from pathlib import Path
from types import ModuleType

import pytest
from aioresponses import aioresponses

from nexar.cache import NO_CACHE_CONFIG
from tests.payloads.sandbox import (
    DUMMY_KEY,
    FAILURE_MARKER,
    SnippetSandbox,
    match_payload,
    timeline_payload,
)

SNIPPETS_DIR = Path(__file__).parent.parent / "docs" / "snippets"
SNIPPETS = sorted(SNIPPETS_DIR.rglob("*.py"))


def _load(snippet: Path) -> ModuleType:
    """Import one snippet file under a name that cannot collide in ``sys.modules``."""
    name = f"snippet_{snippet.parent.name}_{snippet.stem}"
    spec = importlib.util.spec_from_file_location(name, snippet)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def _restored_logging():
    """Undo a snippet's logging configuration so the gate leaks no handlers or levels."""
    root = logging.getLogger()
    root_level, root_handlers = root.level, list(root.handlers)
    nexar = logging.getLogger("nexar")
    nexar_level, nexar_handlers = nexar.level, list(nexar.handlers)
    try:
        yield
    finally:
        root.setLevel(root_level)
        root.handlers[:] = root_handlers
        nexar.setLevel(nexar_level)
        nexar.handlers[:] = nexar_handlers


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda path: str(path.relative_to(SNIPPETS_DIR)))
def test_snippet_runs_under_mocks(
    snippet: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # A dummy key keeps module-level client construction and runtime key guards happy.
    monkeypatch.setenv("RIOT_API_KEY", DUMMY_KEY)
    # Import without leaving __pycache__ dirs in the docs tree.
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    # The gate owns the sandbox: HOME redirects every ~/.nexar path into the temp
    # dir (custom cache names included) and chdir keeps log_config.py's relative
    # "nexar.log" out of the repo. Replacing the construction-time cache default
    # means a no-arg client never opens a cache at all, so no snippet can pass on
    # a warm row that never touched the mock.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("nexar.client.DEFAULT_CACHE_CONFIG", NO_CACHE_CONFIG)

    sandbox = SnippetSandbox()
    with aioresponses() as mock, _restored_logging():
        sandbox.register(mock)
        module = _load(snippet)
        main = getattr(module, "main", None)
        if main is not None:
            asyncio.run(main())

    output = capsys.readouterr().out
    # Two snippets wrap their body in `except Exception` for keyless readers. Under
    # mocks that banner means an exception was swallowed, which is the silent green
    # this gate exists to stop.
    assert FAILURE_MARKER not in output, f"{snippet.relative_to(SNIPPETS_DIR)} swallowed an exception:\n{output}"


def test_match_payload_carries_every_roster_identity() -> None:
    """The match and timeline rows must cover the whole roster, or lookups come back empty."""
    sandbox = SnippetSandbox()
    roster = sandbox.roster
    puuids = {identity.puuid for identity in roster}

    match = match_payload("NA1_1", roster)
    participant_puuids = {participant["puuid"] for participant in match["info"]["participants"]}
    assert puuids <= participant_puuids
    assert set(match["metadata"]["participants"]) == participant_puuids

    timeline = timeline_payload("NA1_1", roster)
    timeline_puuids = {participant["puuid"] for participant in timeline["info"]["participants"]}
    assert puuids == timeline_puuids


def test_sandbox_resolves_every_riot_id_the_snippets_request() -> None:
    """Every hardcoded Riot ID in the docs must resolve, apart from the documented misses."""
    sandbox = SnippetSandbox()
    requested = {
        "bexli#bex",
        "mltsimpleton#na1",
        "roninalex#na1",
        "poydok#na1",
        "boxrog#na1",
        "vynle#na1",
        "Doublelift#NA1",
        "Thebausffs#COOL",
        "Agurin#EUW",
        "PlayerName#NA1",
        "PlayerName#EUW1",
    }
    for riot_id in requested:
        game_name, tag_line = riot_id.split("#", 1)
        assert sandbox.identity_for(game_name, tag_line) is not None, riot_id

    assert sandbox.identity_for("nonexistent", "user") is None
    assert sandbox.identity_for("alsobad", "user") is None
