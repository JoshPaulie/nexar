"""Every docs snippet runs end to end against mocked Riot routes.

An import-only gate let a snippet whose ``main()`` crashes at runtime ship in
the docs: a missing ``default_region``, an error label parsed as a number, a
lookup that silently returns an empty list. This gate executes each snippet's
``main()`` (every top-level coroutine where there is no ``main``, module body
otherwise) against ``tests/payloads/sandbox.py``, so runtime-only breakage is
red before publish.

The gate owns the sandbox, not the snippets: the snippet files stay verbatim,
while ``HOME`` is redirected, the process chdirs into a temp dir, and the
construction-time cache default is replaced -- a no-arg client must never read
or write the real ``~/.nexar`` cache, where a warm row would answer the snippet
without ever reaching the mock.

Green means the example demonstrated something, not merely that it did not
raise: a row that makes no mocked request, and a row whose example prints
nothing while its source contains a ``print``, both fail. Those two checks are
what catch the silent-empty class -- a fixture that stops carrying the data a
snippet reads sends the example through its ``if not data: return`` guard and
out the back door without an exception.
"""

import asyncio
import contextlib
import importlib.util
import inspect
import logging
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from aioresponses import aioresponses

from nexar.cache import NO_CACHE_CONFIG
from tests.payloads.sandbox import (
    DUMMY_KEY,
    FAILURE_MARKER,
    MISSING_ACCOUNTS,
    SnippetSandbox,
    match_payload,
    timeline_payload,
)

SNIPPETS_DIR = Path(__file__).parent.parent / "docs" / "snippets"
SNIPPETS = sorted(SNIPPETS_DIR.rglob("*.py"))

# Snippets that demonstrate construction or configuration and reach no endpoint.
# Everything else must produce at least one mocked request.
CONSTRUCTION_ONLY = frozenset({"caching/demo.py", "quick_start/01_client_demo.py"})

RIOT_ID_LITERAL = re.compile(r'"([A-Za-z0-9_.\-]+#[A-Za-z0-9_.\-]+)"')


def _load(snippet: Path) -> ModuleType:
    """Import one snippet file under a name that cannot collide in ``sys.modules``."""
    name = f"snippet_{snippet.parent.name}_{snippet.stem}"
    spec = importlib.util.spec_from_file_location(name, snippet)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _executables(module: ModuleType) -> list[Any]:
    """The snippet's entry points: ``main()``, or every coroutine the module defines.

    ``client-features/production_rate_limits.py`` is the reason for the second
    branch: it has no ``main()``, and its only API-calling example would
    otherwise never run.
    """
    main = getattr(module, "main", None)
    if main is not None:
        return [main]
    return [
        value
        for value in vars(module).values()
        if inspect.iscoroutinefunction(value) and getattr(value, "__module__", None) == module.__name__
    ]


def _restore_logger(logger: logging.Logger, level: int, handlers: list[logging.Handler]) -> None:
    for handler in logger.handlers:
        if handler not in handlers:
            handler.close()
    logger.handlers[:] = handlers
    logger.setLevel(level)


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
        _restore_logger(root, root_level, root_handlers)
        _restore_logger(nexar, nexar_level, nexar_handlers)


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda path: str(path.relative_to(SNIPPETS_DIR)))
def test_snippet_runs_under_mocks(
    snippet: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    relative = snippet.relative_to(SNIPPETS_DIR).as_posix()
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
        for entry_point in _executables(module):
            asyncio.run(entry_point())

    output = capsys.readouterr().out
    # Two snippets wrap their body in `except Exception` for keyless readers. Under
    # mocks that banner means an exception was swallowed, which is the silent green
    # this gate exists to stop.
    assert FAILURE_MARKER not in output, f"{relative} swallowed an exception:\n{output}"
    if relative not in CONSTRUCTION_ONLY:
        assert sandbox.requests, f"{relative} ran but never reached the mocked API: its body did nothing"
    if "print(" in snippet.read_text():
        assert output.strip(), f"{relative} prints, but printed nothing: the example's data path was empty"


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


def test_every_riot_id_in_the_docs_resolves() -> None:
    """Every Riot ID the snippets hardcode must resolve, apart from the documented misses."""
    sandbox = SnippetSandbox()
    literals: set[str] = set()
    for snippet in SNIPPETS:
        literals |= set(RIOT_ID_LITERAL.findall(snippet.read_text()))

    # A scan that finds nothing is a broken scan, not a clean bill of health.
    assert {"bexli#bex", "nonexistent#user"} <= literals
    for riot_id in sorted(literals):
        game_name, tag_line = riot_id.split("#", 1)
        missing = (game_name.casefold(), tag_line.casefold()) in MISSING_ACCOUNTS
        resolved = sandbox.identity_for(game_name, tag_line)
        assert (resolved is None) == missing, riot_id
        if resolved is not None:
            assert resolved.puuid in {identity.puuid for identity in sandbox.roster}
