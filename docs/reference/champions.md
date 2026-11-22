# Champions

`nexar.champions` is a static champion ID-to-name map snapshotted from Data Dragon, so champion ids can resolve to names offline. `scripts/regen_champion_names.py` refreshes the snapshot on a patch bump. Until it runs, an id newer than the snapshot (or a game-mode id) resolves to `None` instead of raising.

::: nexar.champions
