# Plan: `browse`, `inspect`, `search` Commands

## Context

`build-cache` is done and the SQLite schema is in place. This plan adds three read-only commands
that query the cache. No new files are created — all changes land in `hxlib/db.py` (query methods
+ return types) and `hxlib/cli.py` (handlers + parser entries).

---

## Commands

```
hx browse                         list all categories with model counts
hx browse <category>              list models in a category (name or partial match)
hx inspect <MODEL_ID>             show one model's details and all its params
hx search <query>                 search model names; optional --category filter
```

---

## Return Types (added to `hxlib/db.py`, exported via `hxlib/__init__.py`)

Use frozen dataclasses — clean attribute access, strict-typing-friendly, no third-party deps.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CategoryRow:
    id: int
    name: str
    short_name: str
    model_count: int

@dataclass(frozen=True)
class ModelRow:
    symbolic_id: str
    name: str
    category_id: int | None
    category_name: str | None   # joined from categories table, None if unmatched
    mono: bool
    stereo: bool
    load: float | None
    load_stereo: float | None

@dataclass(frozen=True)
class ParamRow:
    symbolic_id: str
    name: str
    value_type: int             # 0=int 1=float 2=bool 3=str
    display_type: str | None
    min_val: str | None
    max_val: str | None
    default_val: str | None
```

---

## New `ModelDB` Query Methods

```python
def list_categories(self) -> list[CategoryRow]:
    """All categories with model count, ordered by id."""
    # SELECT c.id, c.name, c.short_name, COUNT(m.symbolic_id)
    # FROM categories c LEFT JOIN models m ON m.category_id = c.id
    # GROUP BY c.id ORDER BY c.id

def find_category(self, query: str) -> list[CategoryRow]:
    """Case-insensitive match on name or short_name (exact first, then LIKE)."""
    # 1. Try WHERE LOWER(name) = LOWER(query) OR LOWER(short_name) = LOWER(query)
    # 2. If no exact match, try WHERE LOWER(name) LIKE '%' || LOWER(query) || '%'
    # Returns list — caller handles 0 results or ambiguity

def list_models(self, category_id: int) -> list[ModelRow]:
    """Models in a category, ordered by name, with category_name joined."""

def get_model(self, symbolic_id: str) -> ModelRow | None:
    """Single model by symbolic_id, or None if not found."""

def get_params(self, symbolic_id: str) -> list[ParamRow]:
    """Params for a model, in sort_order."""

def search_models(self, query: str, category_id: int | None = None) -> list[ModelRow]:
    """Case-insensitive LIKE search on model name, with optional category filter.
    Results ordered by name."""
    # WHERE LOWER(m.name) LIKE '%' || LOWER(query) || '%'
    # AND (category_id IS NULL OR m.category_id = category_id)
```

All methods raise `sqlite3.OperationalError` if the DB schema is missing (i.e. cache never built).
CLI handlers catch this and print the "run build-cache first" message.

---

## CLI Handlers (`hxlib/cli.py`)

### Cache-not-found helper

```python
def _db(db_path: Path) -> ModelDB | None:
    """Return open ModelDB, or print error and return None if cache missing."""
    if not db_path.exists():
        print('error: cache not found — run "hx build-cache" first', file=sys.stderr)
        return None
    return ModelDB(db_path=db_path)
```

### `_browse(args)`

```python
def _browse(args: argparse.Namespace) -> int:
    db_path = Path(__file__).parent.parent / "hx_cache.db"
    db = _db(db_path)
    if db is None:
        return 1
    with db:
        if args.category is None:
            rows = db.list_categories()
            _print_categories(rows)
        else:
            matches = db.find_category(args.category)
            if not matches:
                print(f"error: no category matching '{args.category}'", file=sys.stderr)
                return 1
            if len(matches) > 1:
                names = ", ".join(r.name for r in matches)
                print(f"error: ambiguous — matches: {names}", file=sys.stderr)
                return 1
            models = db.list_models(matches[0].id)
            _print_models(matches[0], models)
    return 0
```

### `_inspect(args)`

```python
def _inspect(args: argparse.Namespace) -> int:
    db_path = Path(__file__).parent.parent / "hx_cache.db"
    db = _db(db_path)
    if db is None:
        return 1
    with db:
        model = db.get_model(args.model_id)
        if model is None:
            print(f"error: model '{args.model_id}' not found", file=sys.stderr)
            return 1
        params = db.get_params(args.model_id)
        _print_model_detail(model, params)
    return 0
```

### `_search(args)`

```python
def _search(args: argparse.Namespace) -> int:
    db_path = Path(__file__).parent.parent / "hx_cache.db"
    db = _db(db_path)
    if db is None:
        return 1
    with db:
        category_id: int | None = None
        if args.category is not None:
            matches = db.find_category(args.category)
            if not matches:
                print(f"error: no category matching '{args.category}'", file=sys.stderr)
                return 1
            if len(matches) > 1:
                names = ", ".join(r.name for r in matches)
                print(f"error: ambiguous — matches: {names}", file=sys.stderr)
                return 1
            category_id = matches[0].id
        results = db.search_models(args.query, category_id=category_id)
        _print_search_results(args.query, results)
    return 0
```

---

## Output Formatting (plain text, no third-party libs)

### `hx browse` — category list

```
 ID  Name              Short   Models
  0  None              None         1
  1  Distortion        Dist        42
  2  Dynamics          Dyn         18
  ...
```

### `hx browse distortion` — model list

```
Distortion — 42 models

Name                             ID                              Mono  Stereo   Load
Kinky Boost                      HD2_DistKinkyBoost                 y       y   3.21
Deranged Master                  HD2_DistDerangedMaster             y       y   3.21
...
```

### `hx inspect HD2_AmpGermanMahadeva`

```
German Mahadeva
  ID:       HD2_AmpGermanMahadeva
  Category: Amp
  Modes:    mono
  Load:     28.27 (mono)

Params:
  Name        Sym          Type     Min    Max    Default
  Drive       Drive        float    0.0    1.0    0.39
  Bass        Bass         float    0.0    1.0    0.31
  ...
```

### `hx search "reverb"`

```
7 models matching "reverb"

Name                             ID                              Category
Plate Reverb                     HD2_RevPlate140                 Reverb
...

# 0 results:
No models found matching "reverb".
```

### Formatting helpers (private to `cli.py`)

```python
def _col(value: str, width: int, align: str = "<") -> str:
    """Left/right-align a string in a fixed-width column."""
    return format(value, f"{align}{width}")

def _print_categories(rows: list[CategoryRow]) -> None: ...
def _print_models(category: CategoryRow, models: list[ModelRow]) -> None: ...
def _print_model_detail(model: ModelRow, params: list[ParamRow]) -> None: ...
def _print_search_results(query: str, results: list[ModelRow]) -> None: ...
```

Column widths are fixed constants — no dynamic terminal-width detection needed at this stage.

---

## Parser additions (`_build_parser`)

```python
# browse
browse = subparsers.add_parser("browse", help="List categories or models")
browse.add_argument("category", nargs="?", default=None, help="Category name or partial match")
browse.set_defaults(func=_browse)

# inspect
inspect_ = subparsers.add_parser("inspect", help="Show model details and params")
inspect_.add_argument("model_id", help="Symbolic model ID (e.g. HD2_DistKinkyBoost)")
inspect_.set_defaults(func=_inspect)

# search
search = subparsers.add_parser("search", help="Search models by name")
search.add_argument("query", help="Search term")
search.add_argument("-c", "--category", default=None, help="Filter by category")
search.set_defaults(func=_search)
```

---

## `hxlib/__init__.py` additions

```python
from hxlib.db import CategoryRow, ModelDB, ModelRow, ParamRow
__all__ = ["CategoryRow", "ModelDB", "ModelRow", "ParamRow"]
```

---

## What is NOT included

- `--json` output flag (save for later)
- Dynamic terminal width / pagination
- Fuzzy matching beyond SQLite LIKE (no third-party deps)
- Any write operations

---

## Verification

```bash
python hx.py browse
python hx.py browse distortion
python hx.py browse dist          # partial match
python hx.py browse xyz           # error: no match
python hx.py inspect HD2_DistKinkyBoost
python hx.py inspect NOPE         # error: not found
python hx.py search "plate"
python hx.py search "reverb" -c reverb
python hx.py search "reverb" -c xyz   # error: no category match
uv run check
```
