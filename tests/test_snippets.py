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
import os
import re
import sys
import textwrap
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

DOCS_DIR = Path(__file__).parent.parent / "docs"
SNIPPETS_DIR = DOCS_DIR / "snippets"
SNIPPETS = sorted(SNIPPETS_DIR.rglob("*.py"))

# A python fence whose body is not a snippet include: code the gate cannot run.
PYTHON_BLOCK = re.compile(r"^[ \t]*```(?:py|python)(?![A-Za-z])[^\n]*\n(.*?)^[ \t]*```", re.DOTALL | re.MULTILINE)

# Snippets that demonstrate construction or configuration and reach no endpoint.
# Everything else must produce at least one mocked request.
CONSTRUCTION_ONLY = frozenset(
    {
        "caching/demo.py",
        "caching/location.py",
        "caching/manage.py",
        "client-features/debug_responses.py",
        "quick_start/01_client_demo.py",
    }
)

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
def _restored_process_state():
    """Undo a snippet's logging and environment changes so no row changes the next."""
    root = logging.getLogger()
    root_level, root_handlers = root.level, list(root.handlers)
    nexar = logging.getLogger("nexar")
    nexar_level, nexar_handlers = nexar.level, list(nexar.handlers)
    environ = dict(os.environ)
    try:
        yield
    finally:
        _restore_logger(root, root_level, root_handlers)
        _restore_logger(nexar, nexar_level, nexar_handlers)
        # NEXAR_DEBUG_RESPONSES set by one snippet would otherwise turn every
        # later row's output into a full response dump.
        os.environ.clear()
        os.environ.update(environ)


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
    with aioresponses() as mock, _restored_process_state():
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


def test_every_python_block_is_a_snippet_include() -> None:
    """Hand-written python blocks are the class that shipped twice-crashed code.

    The execution gate only sees ``docs/snippets``; a fenced block on a page was
    run by no one. A page block is now a snippet include, so the file it shows is
    the file the gate executes.
    """
    offenders: list[str] = []
    for page in sorted(DOCS_DIR.rglob("*.md")):
        text = page.read_text()
        for match in PYTHON_BLOCK.finditer(text):
            body = [line.strip() for line in match.group(1).splitlines() if line.strip()]
            if not body or not body[0].startswith("--8<--"):
                line_no = text[: match.start()].count("\n") + 1
                offenders.append(f"{page.relative_to(DOCS_DIR)}:{line_no}")
    assert not offenders, "Python blocks outside a snippet include: " + ", ".join(offenders)


def test_debug_flag_name_matches_the_snippet() -> None:
    """The env var the docs set is the one the client reads.

    The debug snippet has no entry point, so execution alone proves only that
    ``os.environ`` accepted the assignment. Pinning both literals catches a
    rename on either side.
    """
    flag = "NEXAR_DEBUG_RESPONSES"
    client_source = (Path(__file__).parent.parent / "src" / "nexar" / "client_plumbing.py").read_text()
    snippet = (SNIPPETS_DIR / "client-features" / "debug_responses.py").read_text()
    assert f'"{flag}"' in client_source
    assert f'"{flag}"' in snippet


EXAMPLES_DIR = DOCS_DIR / "examples"

# `--8<-- "examples/all_examples.py:section-name"` renders a slice of a snippet
# file. Whole-file includes carry their own imports and are executed as files
# by test_snippet_runs_under_mocks; a section is what the reader copies.
INCLUDE = re.compile(r'--8<--\s+"([^"\n]+?)(?::([^"\n]+?))?"')

# What the quick start hands every reader before an examples page: a client
# with a default region, used inside `async with`. A section that reaches for
# anything else must import it itself, or the page's code fails as copied.
PAGE_BOILERPLATE = """\
import os

from nexar.client import NexarClient
from nexar.enums import Region

api_key = os.getenv("RIOT_API_KEY")
client = NexarClient(api_key, default_region=Region.NA1)


async def main() -> None:
    async with client:
"""


def _section_include_pages() -> list[Path]:
    """Examples pages that render one or more snippet sections."""
    pages: list[Path] = []
    for page in sorted(EXAMPLES_DIR.rglob("*.md")):
        targets = INCLUDE.findall(page.read_text())
        if any(section for _, section in targets):
            pages.append(page)
    return pages


def _extract_section(snippet: Path, section: str) -> str:
    """The named section's lines, dedented, between its --8<-- markers."""
    pattern = re.compile(
        rf"^[ \t]*# --8<-- \[start:{re.escape(section)}\]\n(.*?)^[ \t]*# --8<-- \[end:{re.escape(section)}\]",
        re.DOTALL | re.MULTILINE,
    )
    match = pattern.search(snippet.read_text())
    assert match is not None, f"{snippet.name} has no section {section!r}"
    lines = match.group(1).splitlines()
    assert any(line.strip() for line in lines), f"{snippet.name} section {section!r} is empty"
    indent = min(len(line) - len(line.lstrip()) for line in lines if line.strip())
    return "\n".join(line[indent:] if line.strip() else "" for line in lines) + "\n"


@pytest.mark.parametrize(
    "page",
    _section_include_pages(),
    ids=lambda path: str(path.relative_to(DOCS_DIR)),
)
def test_example_page_demo_runs_as_copied(
    page: Path,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A page's rendered demo must run pasted into the quick-start boilerplate.

    The execution gate runs whole snippet files, imports included, so a
    section that reaches for a name defined above its markers passed every
    check while the code the page actually shows raised NameError. Two
    shipped that way: match-history's `dt` (imported at the top of
    all_examples.py, never rendered on the page) and sort-players-by-rank's
    helper from nexar.utils.
    """
    # A scan that gates nothing is a broken scan: the two pages that shipped
    # broken must stay inside it.
    gated = {str(p.relative_to(DOCS_DIR)) for p in _section_include_pages()}
    assert {"examples/match_history.md", "examples/sort_players_by_rank.md"} <= gated

    body = ""
    for target, section in INCLUDE.findall(page.read_text()):
        if not section:
            continue
        snippet = SNIPPETS_DIR / target
        assert snippet.exists(), f"{page.name} includes missing file {target}"
        body += _extract_section(snippet, section)
    assert body.strip(), f"{page.name} renders no section demo"

    source = PAGE_BOILERPLATE + textwrap.indent(body, " " * 8)
    synthetic = tmp_path / f"page_demo_{page.stem}.py"
    synthetic.write_text(source)

    monkeypatch.setenv("RIOT_API_KEY", DUMMY_KEY)
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("nexar.client.DEFAULT_CACHE_CONFIG", NO_CACHE_CONFIG)

    sandbox = SnippetSandbox()
    with aioresponses() as mock, _restored_process_state():
        sandbox.register(mock)
        module = _load(synthetic)
        asyncio.run(module.main())

    output = capsys.readouterr().out
    assert sandbox.requests, f"{page.name} demo ran but never reached the mocked API"
    if "print(" in body:
        assert output.strip(), f"{page.name} demo prints, but printed nothing"
