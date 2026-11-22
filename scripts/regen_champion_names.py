"""Regenerate ``src/nexar/champions.py`` from Riot's Data Dragon.

A patch bump is one command: fetch the latest Data Dragon version, snapshot
its champion list into the static map module, and rewrite the file with the
new patch version pinned in the docstring. Run the offline gates afterwards
and commit the diff.
"""

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = ROOT / "src" / "nexar" / "champions.py"
VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"
CHAMPIONS_URL = "https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json"


def _fetch_versions() -> list[str]:
    """The live Data Dragon version list, newest patch first."""
    with urllib.request.urlopen(VERSIONS_URL, timeout=30) as response:  # noqa: S310
        return json.loads(response.read().decode())


def _fetch_champions(patch: str) -> dict[str, dict[str, str]]:
    """The patch's champion entries keyed by Data Dragon id, each carrying ``key`` and ``name``."""
    with urllib.request.urlopen(CHAMPIONS_URL.format(patch=patch), timeout=30) as response:  # noqa: S310
        document: dict[str, dict[str, dict[str, str]]] = json.loads(response.read().decode())
    return document["data"]


def _champion_pairs(patch: str) -> list[tuple[int, str]]:
    """The patch's champion list as (id, display name) pairs, id ascending."""
    return sorted((int(entry["key"]), entry["name"]) for entry in _fetch_champions(patch).values())


def _module_text(patch: str, pairs: list[tuple[int, str]]) -> str:
    """Render the map module: pinned patch version, ids sorted ascending."""
    entries = "\n".join(f'    {champion_id}: "{name}",' for champion_id, name in pairs)
    return f'''"""Static champion ID-to-name map, snapshotted from Riot's Data Dragon.

Data Dragon patch {patch}: the map is generated once and checked in, so
champion ids resolve offline with no runtime network dependency. Refresh it
on a patch bump with ``uv run python scripts/regen_champion_names.py``.

Source: https://ddragon.leagueoflegends.com/cdn/{patch}/data/en_US/champion.json
"""

__all__ = ["CHAMPION_NAMES", "champion_name"]

CHAMPION_NAMES: dict[int, str] = {{
{entries}
}}


def champion_name(champion_id: int) -> str | None:
    """Return the champion's display name for a Data Dragon id, or None.

    None means the id is absent from the pinned snapshot: a champion
    released after it, or a game-mode id Data Dragon does not list. The raw
    id stays on the model, and an unknown id is forward drift, not an
    error; refresh the snapshot with ``scripts/regen_champion_names.py``.
    """
    return CHAMPION_NAMES.get(champion_id)
'''


def main() -> None:
    """Snapshot the latest Data Dragon patch into the map module."""
    patch = _fetch_versions()[0]
    pairs = _champion_pairs(patch)
    if not pairs:
        msg = "Data Dragon returned no champions; the module was not modified."
        raise RuntimeError(msg)

    MODULE_PATH.write_text(_module_text(patch, pairs), encoding="utf-8")
    print(f"Data Dragon patch {patch}: {len(pairs)} champions written to {MODULE_PATH.relative_to(ROOT)}")
    print("Run the offline gates (pytest, ty, ruff) and commit the diff.")


if __name__ == "__main__":
    main()
