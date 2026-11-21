"""Structural guardrails: API surface baseline, size budgets, seam discipline.

Three gates, each failing for a reason:

- ``test_api_surface_matches_baseline`` — the public surface of every module
  and key class is pinned in ``api_baseline.json`` (exact match: additions
  and removals both fail). Any deliberate surface change must refresh the
  baseline in the same commit: set ``UPDATE_BASELINE=1`` to regenerate.
- file/function budget tests — tripwires against the next god-file, not style
  police. Current maxima: participant.py 816 lines, ``_make_api_call`` 76
  (client_plumbing.py since the topic split).
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
import json
import os
from pathlib import Path
from typing import TypedDict

import pytest

SRC = Path(__file__).parent.parent / "src" / "nexar"
BASELINE = Path(__file__).parent / "api_baseline.json"

# Modules whose top-level definitions are the SDK's public API surface.
SURFACE_MODULES = [
    "nexar/__init__.py",
    "nexar/client.py",
    "nexar/client_match.py",
    "nexar/client_plumbing.py",
    "nexar/cache.py",
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
    """A file crossing 1000 lines is the next god-file; split before landing."""
    for path in sorted(SRC.rglob("*.py")):
        line_count = len(path.read_text().splitlines())
        assert line_count <= MAX_FILE_LINES, f"{path} is {line_count} lines (cap {MAX_FILE_LINES})"


def test_no_function_exceeds_the_line_budget() -> None:
    """A function crossing 100 lines collapses (table, chain, or phases)."""
    over: list[tuple[int, str, str]] = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                length = (node.end_lineno or node.lineno) - node.lineno + 1
                if length > MAX_FUNCTION_LINES:
                    over.append((length, f"{path}:{node.lineno}", node.name))
    assert not over, f"functions over {MAX_FUNCTION_LINES} lines: {over}"


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
