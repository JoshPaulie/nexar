"""Every docs snippet imports cleanly — snippets rot when the API drifts.

Module-level snippet code runs here with a dummy key, so a snippet that
references a name the SDK removed (or mis-imports anything) fails the suite
instead of shipping in the docs. All network calls live inside ``main()``
blocks behind ``if __name__ == "__main__"``, so importing makes no requests.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

SNIPPETS_DIR = Path(__file__).parent.parent / "docs" / "snippets"
SNIPPETS = sorted(SNIPPETS_DIR.rglob("*.py"))


@pytest.mark.parametrize("snippet", SNIPPETS, ids=lambda p: str(p.relative_to(SNIPPETS_DIR)))
def test_snippet_imports(snippet: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # A dummy key keeps module-level client construction import-safe; runtime key
    # guards live inside main() so import time never needs a real key.
    monkeypatch.setenv("RIOT_API_KEY", "RGAPI-SNIPPET-TEST")
    # Import without leaving __pycache__ dirs in the docs tree.
    monkeypatch.setattr(sys, "dont_write_bytecode", True)
    spec = importlib.util.spec_from_file_location(f"snippet_{snippet.stem}", snippet)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
