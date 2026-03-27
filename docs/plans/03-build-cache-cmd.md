# Plan: `hx build-cache` — First CLI Command

## Context

The scaffold is complete. The next step from `hx-stomp-preset-tool.md` is to implement the data
layer foundation. Rather than tackling the full plan at once, this scoped task wires up the first
working CLI subcommand: `hx build-cache`. It reads all `.models` files (and optionally
`HX_ModelCatalog.json`) from `assets/res/` and populates a local SQLite cache at `hx_cache.db`.
This establishes the parsing pipeline and CLI dispatch pattern that all future subcommands
(`browse`, `inspect`, `search`, etc.) will build on.

---

## Files

| File | Action |
|---|---|
| `hxlib/db.py` | **Create** — `ModelDB` class, SQLite schema, all data loading logic |
| `hxlib/cli.py` | **Replace stub** — argparse subcommand wiring + `build-cache` handler |
| `hxlib/__init__.py` | **Minimal update** — export `ModelDB` |

---

## SQLite Schema (`hx_cache.db`)

```sql
CREATE TABLE categories (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    short_name TEXT NOT NULL
);

CREATE TABLE models (
    symbolic_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,      -- defaults to symbolicID if absent in source
    category_id  INTEGER REFERENCES categories(id),   -- nullable
    mono         INTEGER NOT NULL DEFAULT 0,
    stereo       INTEGER NOT NULL DEFAULT 0,
    load         REAL,
    load_stereo  REAL,
    source_file  TEXT NOT NULL
);

CREATE TABLE params (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id     TEXT NOT NULL REFERENCES models(symbolic_id),
    symbolic_id  TEXT NOT NULL,
    name         TEXT NOT NULL,
    value_type   INTEGER NOT NULL,    -- 0=int 1=float 2=bool 3=str
    display_type TEXT,
    min_val      TEXT,                -- stored as TEXT; parse via value_type
    max_val      TEXT,
    default_val  TEXT,
    sort_order   INTEGER NOT NULL
);

CREATE TABLE build_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
    -- rows: built_at (ISO timestamp), assets_mtime (max mtime across .models files)
);
```

---

## `hxlib/db.py`

### Asset path resolution

```python
def _assets_dir() -> pathlib.Path:
    # db.py → hxlib/ → project_root/ → assets/res/
    return pathlib.Path(__file__).parent.parent / "assets" / "res"
```

### Internal TypedDicts (private, for strict typing of json.load output)

```python
class _RawParam(TypedDict):
    symbolicID: str
    name: str
    valueType: int
    displayType: NotRequired[str]
    min: float | bool | str | int
    max: float | bool | str | int
    default: float | bool | str | int

class _RawModel(TypedDict):
    symbolicID: str
    name: NotRequired[str]       # absent on e.g. @global_params in fixed.models
    category: NotRequired[int]
    mono: NotRequired[bool]
    stereo: NotRequired[bool]
    load: NotRequired[float]
    load_stereo: NotRequired[float]
    params: list[_RawParam]

class _RawCategory(TypedDict):
    id: int
    name: str
    shortName: str
```

### `ModelDB` class

```python
class ModelDB:
    def __init__(self, db_path: Path, assets_dir: Path | None = None) -> None: ...

    def is_fresh(self) -> bool:
        """True if DB exists and assets_mtime in build_meta >= max .models mtime."""

    def build(self, *, force: bool = False) -> tuple[int, int]:
        """Build/rebuild the cache. Returns (model_count, param_count).
        Raises FileNotFoundError if assets_dir missing.
        Raises ValueError on malformed JSON or missing symbolicID.
        """

    def close(self) -> None: ...
    def __enter__(self) -> "ModelDB": ...
    def __exit__(self, *_: object) -> None: ...
```

### `build()` logic

1. Validate `assets_dir` exists → `FileNotFoundError` if not
2. Gather `sorted(assets_dir.glob("*.models"))`
3. If `not force and is_fresh()` → open DB, return existing counts (no rebuild)
4. Load categories from `HX_ModelCatalog.json` (best-effort: `{}` if file missing)
5. Open connection, begin single transaction
6. DROP + CREATE all four tables
7. INSERT categories
8. For each `.models` file: parse JSON → INSERT models + params
   - Validate each item has `symbolicID` → `ValueError` with filename + index if not
   - `name` defaults to `symbolicID` if absent
9. `_write_meta()` — store `built_at` timestamp and `assets_mtime`
10. COMMIT → return `(model_count, param_count)`

### Scalar encoding

`min`, `max`, `default` can be `float`, `int`, `bool`, or `""` (valueType=3). Store all as TEXT:

```python
def _encode_scalar(self, v: float | bool | str | int | None) -> str | None:
    if v is None:
        return None
    if isinstance(v, bool):   # must precede int — bool is subclass of int
        return "true" if v else "false"
    return str(v)
```

---

## `hxlib/cli.py`

```python
def _build_cache(args: argparse.Namespace) -> int:
    db_path = Path(__file__).parent.parent / "hx_cache.db"
    db = ModelDB(db_path=db_path)
    try:
        if not args.force and db.is_fresh():
            print("Cache is already up to date. Use --force to rebuild.")
            return 0
        print("Building cache...", flush=True)
        model_count, param_count = db.build(force=args.force)
        print(f"Cached {model_count} models, {param_count} params")
        return 0
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"error: malformed asset data — {e}", file=sys.stderr)
        return 1
    finally:
        db.close()

def _build_parser() -> argparse.ArgumentParser:
    # subparsers → "build-cache" with --force
    # build_cache.set_defaults(func=_build_cache)

def main() -> None:
    args = _build_parser().parse_args()
    sys.exit(args.func(args))   # dispatch via set_defaults(func=...)
```

---

## `hxlib/__init__.py`

```python
from hxlib.db import ModelDB
__all__ = ["ModelDB"]
```

---

## Edge Cases

- `@global_params` in `fixed.models` has no `name` or `category` fields — handled by defaults
- `bool` must be checked before `int` in `_encode_scalar` (bool is subclass of int)
- `HX_ModelCatalog.json` missing → categories table stays empty, models still populate
- Use a single transaction for the full rebuild — crash midway leaves old DB intact

---

## Verification

```bash
# Build the cache
python hx.py build-cache
# → "Building cache..."
# → "Cached NNN models, NNNN params"

# Freshness check
python hx.py build-cache
# → "Cache is already up to date. Use --force to rebuild."

# Force rebuild
python hx.py build-cache --force

# Full check suite
uv run check
```
