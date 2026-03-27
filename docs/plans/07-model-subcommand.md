# Plan: Move model commands under `hx model` subcommand

## Context

The CLI currently has four top-level model-related commands (`browse`, `inspect`, `search`,
`build-cache`) alongside the `preset` subcommand group. Two problems:

1. `preset` has nested subcommands while model commands are flat — inconsistent CLI surface.
2. The model handlers live in four separate files while all preset handlers live in one
   `_preset.py` — inconsistent module structure.

The fix mirrors `_preset.py` exactly: consolidate all model handlers into `_model.py` and group
the commands under `hx model`.

**Resulting CLI structure:**
```
hx model browse [CATEGORY]
hx model inspect MODEL_ID
hx model search QUERY [-c CATEGORY]
hx model build-cache [--force]
```

**Resulting file structure:**
```
hxlib/cli/
  __init__.py
  _common.py
  _model.py    ← new, consolidates _browse, _inspect, _search, _build_cache
  _preset.py   ← unchanged
```

## Files

| File | Action |
|------|--------|
| `hxlib/cli/_model.py` | Create — move all four handlers here |
| `hxlib/cli/__init__.py` | Update imports and parser |
| `hxlib/cli/_browse.py` | Delete |
| `hxlib/cli/_inspect.py` | Delete |
| `hxlib/cli/_search.py` | Delete |
| `hxlib/cli/_build_cache.py` | Delete |

## Implementation

### 1. Create `hxlib/cli/_model.py`

Move handler code from the four deleted files verbatim. Export references at the bottom,
mirroring `_preset.py`:

```python
"""CLI commands for model browsing: hx model <subcommand>."""

# ... (moved code from _browse.py, _inspect.py, _search.py, _build_cache.py)

# Handler references for parser setup (used by cli/__init__.py)
model_browse = _browse
model_inspect = _inspect
model_search = _search
model_build_cache = _build_cache
```

Add a top-level dispatcher:

```python
def model(args: argparse.Namespace) -> int:
    return args.model_func(args)
```

### 2. Update `hxlib/cli/__init__.py`

Replace the four separate imports with a single import block:

```python
from hxlib.cli._model import (
    model,
    model_browse,
    model_build_cache,
    model_inspect,
    model_search,
)
```

In `_build_parser()`, remove the four standalone subparsers and replace with a `model` group:

```python
model_p = subparsers.add_parser("model", help="Browse and inspect the model database")
model_p.set_defaults(func=model)
model_sub = model_p.add_subparsers(dest="model_command", required=True)

build_cache_p = model_sub.add_parser("build-cache", help="Build the local SQLite model cache")
build_cache_p.add_argument("--force", action="store_true", help="Rebuild even if cache is fresh")
build_cache_p.set_defaults(model_func=model_build_cache)

browse_p = model_sub.add_parser("browse", help="List categories or models")
browse_p.add_argument("category", nargs="?", default=None, help="Category name or partial match")
browse_p.set_defaults(model_func=model_browse)

inspect_p = model_sub.add_parser("inspect", help="Show model details and params")
inspect_p.add_argument("model_id", help="Symbolic model ID (e.g. HD2_DistKinkyBoost)")
inspect_p.set_defaults(model_func=model_inspect)

search_p = model_sub.add_parser("search", help="Search models by name")
search_p.add_argument("query", help="Search term")
search_p.add_argument("-c", "--category", default=None, help="Filter by category")
search_p.set_defaults(model_func=model_search)
```

`main()` is unchanged — it calls `args.func(args)`, and `model()` dispatches to
`args.model_func(args)`.

### 3. Delete the four old files

```
hxlib/cli/_browse.py
hxlib/cli/_inspect.py
hxlib/cli/_search.py
hxlib/cli/_build_cache.py
```

## Verification

```
uv run check
hx model browse
hx model browse Distortion
hx model inspect HD2_DistKinkyBoost
hx model search boost
hx model build-cache --force
hx preset show <some.hlx>   # ensure preset group is unaffected
hx --help
hx model --help
```
