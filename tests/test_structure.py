"""Structural guardrails: API surface baseline, size budgets, seam discipline.

Three gates, each failing for a reason:

- ``test_api_surface_matches_baseline`` — the public surface of every module
  and key class is pinned in ``api_baseline.json`` (exact match: additions
  and removals both fail). Any deliberate surface change must refresh the
  baseline in the same commit: set ``UPDATE_BASELINE=1`` to regenerate.
- file/function budget tests — tripwires against the next god-file, not style
  police. The budgets cover src and tests alike. Current src maxima:
  participant.py 816 lines; the two over-cap test functions are recorded
  fixture payloads pinned in ``KNOWN_LONG`` at their measured size.
  Caps sit above them with headroom; a file crossing 1000 lines or a function
  crossing 100 gets split before it lands, by decision.
- seam tests — no underscore attribute access off ``self``/``cls`` anywhere in
  src, and no importing another module's underscore names. A module's own
  privates are reached as bare names; anything else is a hidden link (the
  hasattr probing of cache internals this repo already retired once).
"""

import ast
import dataclasses
import importlib
import inspect
import json
import os
from pathlib import Path
from typing import TypedDict

import pytest

SRC = Path(__file__).parent.parent / "src" / "nexar"
TESTS = Path(__file__).parent
BASELINE = Path(__file__).parent / "api_baseline.json"
SCAN_ROOTS = (SRC, TESTS)

# Modules whose top-level definitions are the SDK's public API surface.
SURFACE_MODULES = [
    "nexar/__init__.py",
    "nexar/client.py",
    "nexar/client_match.py",
    "nexar/client_plumbing.py",
    "nexar/cache.py",
    "nexar/champions.py",
    "nexar/enums.py",
    "nexar/exceptions.py",
    "nexar/rate_limiter.py",
    "nexar/utils.py",
    "nexar/models/__init__.py",
    "nexar/models/match/__init__.py",
]

# Classes whose member set is pinned (the assembled dataclasses and the client).
SURFACE_CLASSES = [
    ("nexar.client", "NexarClient"),
    ("nexar.client", "CallStats"),
    ("nexar.models.player", "Player"),
    ("nexar.models.match_list", "MatchList"),
    ("nexar.models.match.participant", "Participant"),
    ("nexar.models.match.participant_list", "ParticipantList"),
]

MAX_FILE_LINES = 1000
MAX_FUNCTION_LINES = 100

# Function debt recorded at its measured size, never above it: growth past
# the recorded number fails the budget test, and the companion test below
# fails when an entry no longer needs its ceiling or a ceiling drifts above
# the measured size, so the table only shrinks. Both entries predate the cap
# (they are recorded fixture payloads, moved verbatim out of helpers.py when
# the test tree came under the budgets).
KNOWN_LONG: dict[tuple[str, str], int] = {
    ("tests/payloads/match.py", "create_test_participant"): 128,
    ("tests/payloads/timeline.py", "timeline_response_payload"): 814,
}


def _module_surface(path: Path) -> dict[str, list[str] | None]:
    """Top-level public defs, plus ``__all__`` where a module declares it."""
    tree = ast.parse(path.read_text())
    defs: list[str] = []
    exported: list[str] | None = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            if not node.name.startswith("_"):
                defs.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper() and not target.id.startswith("_"):
                    defs.append(target.id)
                if (
                    isinstance(target, ast.Name)
                    and target.id == "__all__"
                    and isinstance(node.value, ast.List | ast.Tuple | ast.Set)
                ):
                    exported = sorted(
                        elt.value
                        for elt in node.value.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    )
    return {"defs": sorted(set(defs)), "all": exported}


def _class_surface(cls: type) -> list[str]:
    """Public members, plus field names when the class is a dataclass.

    ``dir(cls)`` cannot see dataclass fields (they are assigned per instance
    in ``__init__``), so a removed field would otherwise slip the baseline.
    """
    names = {n for n in dir(cls) if not n.startswith("_")}
    if dataclasses.is_dataclass(cls):
        names.update(f.name for f in dataclasses.fields(cls))
    return sorted(names)


class Surface(TypedDict):
    """The baseline's shape: modules carry ``__all__``, classes carry member names."""

    modules: dict[str, dict[str, list[str] | None]]
    classes: dict[str, list[str]]


def capture_surface() -> Surface:
    """The current public surface, as the baseline file stores it."""
    modules = {rel: _module_surface(SRC.parent / rel) for rel in SURFACE_MODULES}
    classes: dict[str, list[str]] = {}
    for mod_name, cls_name in SURFACE_CLASSES:
        cls = getattr(importlib.import_module(mod_name), cls_name)
        classes[f"{mod_name}.{cls_name}"] = _class_surface(cls)
    return {"modules": modules, "classes": classes}


def test_api_surface_matches_baseline() -> None:
    """Additions and removals both fail; refresh deliberately, in the commit."""
    current = capture_surface()

    if os.environ.get("UPDATE_BASELINE"):
        BASELINE.write_text(json.dumps(current, indent=1, sort_keys=True) + "\n")
        return

    recorded = json.loads(BASELINE.read_text())
    assert current == recorded, (
        "Public API surface changed without a baseline refresh. If the change "
        "is deliberate, regenerate with UPDATE_BASELINE=1 in the same commit "
        "that changes the surface."
    )


def test_no_file_exceeds_the_line_budget() -> None:
    """A file crossing 1000 lines is the next god-file; split before landing.

    The budget covers the test tree too: helpers.py was 1060 lines with the
    test tree unguarded, so the payload families moved to ``payloads/``.
    """
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            line_count = len(path.read_text().splitlines())
            assert line_count <= MAX_FILE_LINES, f"{path} is {line_count} lines (cap {MAX_FILE_LINES})"


def _repo_rel(path: Path) -> str:
    return str(path.relative_to(Path(__file__).parent.parent))


def test_no_function_exceeds_the_line_budget() -> None:
    """A function crossing 100 lines collapses (table, chain, or phases).

    Functions predating the cap carry a ceiling in ``KNOWN_LONG`` at their
    measured size, so the table is debt, not an allowance.
    """
    over: list[tuple[int, str, str]] = []
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    length = (node.end_lineno or node.lineno) - node.lineno + 1
                    cap = KNOWN_LONG.get((_repo_rel(path), node.name), MAX_FUNCTION_LINES)
                    if length > cap:
                        over.append((length, f"{path}:{node.lineno}", node.name))
    assert not over, f"functions over their budget: {over}"


def test_known_long_entries_stay_necessary() -> None:
    """The allowance table must track the tree exactly: entries live, ceilings exact.

    Three staleness shapes fail: an entry whose function vanished, an entry
    whose function now fits the cap (delete it), and a ceiling left above the
    measured size after a partial shrink (lower it — a loose ceiling is a
    silent growth budget).
    """
    measured: dict[tuple[str, str], int] = {}
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.py")):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                    key = (_repo_rel(path), node.name)
                    length = (node.end_lineno or node.lineno) - node.lineno + 1
                    measured[key] = max(measured.get(key, 0), length)
    problems: list[str] = []
    for key, ceiling in KNOWN_LONG.items():
        size = measured.get(key)
        if size is None:
            problems.append(f"{key}: function no longer exists; delete the entry")
        elif size <= MAX_FUNCTION_LINES:
            problems.append(f"{key}: fits the cap at {size} lines; delete the entry")
        elif ceiling > size:
            problems.append(f"{key}: ceiling {ceiling} is above the measured {size}; lower it")
    assert not problems, "KNOWN_LONG must track the tree: " + "; ".join(problems)


def _stub_params(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[tuple[str, str, bool]]:
    """A signature as the parity language: (name, kind, has-default) per parameter."""
    out: list[tuple[str, str, bool]] = []
    args = fn.args
    positional = list(args.posonlyargs) + list(args.args)
    defaults = [None] * (len(positional) - len(args.defaults)) + list(args.defaults)
    for arg, default in zip(positional, defaults, strict=True):
        out.append((arg.arg, "positional", default is not None))
    if args.vararg:
        out.append((args.vararg.arg, "vararg", True))
    for arg, default in zip(args.kwonlyargs, args.kw_defaults, strict=True):
        out.append((arg.arg, "keyword-only", default is not None))
    if args.kwarg:
        out.append((args.kwarg.arg, "keyword-dict", True))
    return out


def test_core_seam_stubs_match_the_real_signatures() -> None:
    """core.py's TYPE_CHECKING stubs must mirror the methods the mixins call.

    The stubs vanish at runtime, so a stub that drifts from the real
    definition still type-checks every mixin call site against the stale
    shape. Compare each stub's parameter list against the method that
    actually executes on ``NexarClient``.
    """
    tree = ast.parse((SRC / "core.py").read_text())
    stubs: dict[str, list[tuple[str, str, bool]]] = {}
    for node in ast.walk(tree):
        if not (isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING"):
            continue
        for fn in node.body:
            if isinstance(fn, ast.FunctionDef | ast.AsyncFunctionDef):
                stubs[fn.name] = _stub_params(fn)
    assert stubs, "core.py's TYPE_CHECKING stub block is gone; move this test with it"

    client_cls = importlib.import_module("nexar.client").NexarClient
    problems: list[str] = []
    for name, stub in stubs.items():
        real = getattr(client_cls, name, None)
        if real is None:
            problems.append(f"{name}: stub has no real method on NexarClient")
            continue
        kinds = {
            inspect.Parameter.POSITIONAL_ONLY: "positional",
            inspect.Parameter.POSITIONAL_OR_KEYWORD: "positional",
            inspect.Parameter.KEYWORD_ONLY: "keyword-only",
            inspect.Parameter.VAR_POSITIONAL: "vararg",
            inspect.Parameter.VAR_KEYWORD: "keyword-dict",
        }
        live = [
            (p.name, kinds[p.kind], p.default is not inspect.Parameter.empty)
            for p in inspect.signature(real).parameters.values()
        ]
        if live != stub:
            problems.append(f"{name}: stub {stub} != real {live}")
    assert not problems, "core seam stubs drifted from the real methods: " + "; ".join(problems)


def test_no_underscore_attribute_access_off_self_or_cls() -> None:
    """Own-module privates are bare names; other objects' privates are never touched."""
    findings: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Attribute) and node.attr.startswith("_") and not node.attr.startswith("__")):
                continue
            value = node.value
            while isinstance(value, ast.Attribute):
                value = value.value
            if isinstance(value, ast.Name) and value.id in ("self", "cls"):
                continue
            findings.append(f"{path}:{node.lineno} .{node.attr}")
    assert not findings, "underscore attribute access off self/cls:\n" + "\n".join(findings)


def test_no_cross_module_underscore_imports() -> None:
    """Importing another module's underscore name widens a private seam."""
    findings: list[str] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                findings.extend(
                    f"{path}:{node.lineno} {node.module}.{alias.name}"
                    for alias in node.names
                    if alias.name.startswith("_") and not alias.name.startswith("__")
                )
    assert not findings, "underscore imports:\n" + "\n".join(findings)


@pytest.mark.parametrize("path", sorted(SRC.rglob("*.py")), ids=lambda p: p.name)
def test_module_compiles(path: Path) -> None:
    """Every source file parses (catches orphaned literals mid-edit)."""
    ast.parse(path.read_text())
