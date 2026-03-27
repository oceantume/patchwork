# Plan: Add move_block to Preset

## Context

Preset blocks have a `@position` (0–5) and `@path` (0=A, 1=B) that define their
place in the signal chain. There is currently no way to change these without
removing and re-adding a block (which loses params and snapshot state). A
`move_block` operation lets an agent reorder the chain while keeping everything
else intact.

Positions are sparse — no shifting of other blocks is needed. The only
constraint is that the target `(path, position)` must not be occupied by another
effect block.

---

## Files to Modify

- `hxlib/preset.py` — add `move_block` method
- `hxlib/cli/_preset.py` — add `_move` handler and export `preset_move`
- `hxlib/cli/__init__.py` — wire up `move` sub-subcommand
- `tests/test_preset.py` — add `TestMoveBlock` class

---

## Implementation

### `Preset.move_block` (`hxlib/preset.py`)

Add after `remove_block`:

```python
def move_block(self, key: str, position: int, *, path: int | None = None) -> None:
```

Logic:
1. Look up block — raise `PresetError("block not found: {key}")` if missing or in FIXED_KEYS
2. Validate `position` in 0–5 — raise `PresetError("position {position} out of range 0–5")`
3. Resolve `path`: use `blk.get("@path", 0)` if `path` is None
4. Check no other effect block has `(resolved_path, position)` — reuse same loop pattern as `add_block`
5. Update: `blk["@path"] = resolved_path`, `blk["@position"] = position`

No snapshot state changes needed — move doesn't affect enable/disable state.

### CLI handler `_move` (`hxlib/cli/_preset.py`)

Follows the same load → modify → save pattern as `_remove`:

```python
def _move(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        p = Preset.load(path)
        p.move_block(args.block_key, args.position, path=args.path)
        p.save(path)
    except (PresetError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Moved {args.block_key} to position {args.position}")
    return 0
```

Export as `preset_move = _move` at the bottom of the file.

`args.path` defaults to `None` (not provided → keep current path).

### Parser (`hxlib/cli/__init__.py`)

Import `preset_move` and add after the `remove` subparser:

```python
move_p = preset_sub.add_parser("move", help="Move a block to a different position")
move_p.add_argument("file", help="Preset file (.hlx)")
move_p.add_argument("block_key", help="Block key (e.g. block0)")
move_p.add_argument("--position", type=int, required=True, help="New position 0–5")
move_p.add_argument("--path", type=int, default=None, help="New signal path (0=A, 1=B)")
move_p.set_defaults(preset_func=preset_move)
```

### Tests (`tests/test_preset.py`)

Add `TestMoveBlock` class:

- `test_position_updated` — move block, verify `get_block().position` changed
- `test_path_updated` — move with explicit path, verify `get_block().path` changed
- `test_path_unchanged_when_not_specified` — omit path arg, verify path stays the same
- `test_params_preserved` — params dict unchanged after move
- `test_snapshot_state_preserved` — snapshot state unchanged after move
- `test_raises_on_unknown_key` — `PresetError` for bad key
- `test_raises_on_position_conflict` — two blocks, move one onto the other's position
- `test_raises_on_position_out_of_range` — position 9

---

## Verification

```bash
uv run check
hx preset new "Test" test.hlx
hx preset add test.hlx HD2_DistCigaretteFuzz --position 0 --snapshots 0,1,2
hx preset move test.hlx block0 --position 3
hx preset show test.hlx
```

Verify `block0` now shows at position 3 with params intact.
