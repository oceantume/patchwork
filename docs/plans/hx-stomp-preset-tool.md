# HX Stomp Preset Tool — Implementation Plan

## Context
Building a Python-based toolkit for creating, modifying, and exploring presets for the Line 6 HX Stomp guitar processor. Presets are `.hlx` JSON files. The goal is to make preset engineering accessible and programmatic, supporting discovery, creation, and on-the-fly tweaks. The user is a beginner to guitar effects/synthesis but comfortable with code.

---

## Source Data (read-only, never modified)
All from `C:/Program Files (x86)/Line6/HX Edit/res/`:
- `*.models` (19 files, JSON arrays) — parametric definitions for 7,542+ models: symbolicID, name, category, load, params (with types/ranges/defaults)
- `HX_ModelCatalog.json` — UI hierarchy: categories → subcategories → models with display names and param display order
- `Helix.sym` — symbolicID → parameter name list cross-reference
- `HelixControls.json` — display formatting per param type (units, scale, step)
- `default_preset_hxs.hlx` — canonical empty HX Stomp preset (structural template)

---

## Project Structure
```
C:\devel\hx-stuff\
  hx.py              # CLI entry point (argparse)
  hxlib/
    __init__.py      # exports: ModelDB, Preset, Block
    db.py            # ModelDB: SQLite cache build + query
    preset.py        # Preset + Block: .hlx load/modify/save
    cli.py           # CLI command implementations
  hx_cache.db        # Auto-generated SQLite (add to .gitignore)
```

---

## Data Layer: SQLite Cache (`hxlib/db.py`)

### Schema
```sql
CREATE TABLE categories (id INTEGER PRIMARY KEY, name TEXT, short_name TEXT, color TEXT);

CREATE TABLE models (
  id TEXT PRIMARY KEY,          -- symbolicID e.g. "HD2_DistTriangleFuzz"
  name TEXT,                    -- display name e.g. "Triangle Fuzz"
  category_id INTEGER,
  mono INTEGER, stereo INTEGER,
  load REAL, load_stereo REAL,
  FOREIGN KEY(category_id) REFERENCES categories(id)
);

CREATE TABLE params (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  model_id TEXT,
  symbolic_id TEXT,             -- e.g. "Sustain", "@enabled"
  name TEXT,                    -- display name
  value_type INTEGER,           -- 0=int, 1=float, 2=bool
  display_type TEXT,            -- e.g. "generic_knob", "percent"
  min_val REAL, max_val REAL, default_val REAL,
  FOREIGN KEY(model_id) REFERENCES models(id)
);
```

### Cache Invalidation
- Store mtime of each source `.models` file in a `cache_meta` table
- On `ModelDB()` init: compare mtimes → rebuild if any changed

### Key Methods
```python
class ModelDB:
    def __init__(self, db_path='hx_cache.db', res_dir=DEFAULT_RES_DIR)
    def browse(self, category=None) -> list[dict]    # list categories or models
    def inspect(self, model_id: str) -> dict          # full model + params
    def search(self, query='', category=None, max_load=None, has_param=None) -> list[dict]
    def get(self, model_id: str) -> dict              # for use with Preset.add_block()
    def find_similar(self, model_id: str) -> list[dict]  # same category, similar params
```

---

## Preset Layer (`hxlib/preset.py`)

### Structure mapped from .hlx
- `data.tone.dsp0` — main signal chain dict (blocks keyed block0…blockN, plus fixed keys: inputA, inputB, split, join, outputA, outputB)
- `data.tone.snapshot0/1/2` — per-snapshot block enable states
- `data.tone.global` — tempo, topology, etc.
- `data.meta.name` — preset name

### Key Methods
```python
class Preset:
    @classmethod
    def new(cls, name: str) -> 'Preset'               # from default_preset_hxs.hlx template
    @classmethod
    def load(cls, path: str) -> 'Preset'              # load existing .hlx

    def show(self) -> str                             # human-readable summary
    def add_block(self, dsp: str, model: dict, position: int, path: int = 0) -> str  # returns block key
    def remove_block(self, dsp: str, block_key: str)
    def set_param(self, dsp: str, block_key: str, param: str, value)  # validates against model def
    def get_block(self, dsp: str, block_key: str) -> dict
    def list_blocks(self) -> list[dict]               # ordered by position

    def save(self, path: str)
```

### Block key assignment
- Scan existing blockN keys, pick next available (block0, block1…block5 max on HX Stomp)
- Store `@path` (0=A, 1=B), `@position`, `@type` (0=effect, 1=amp) based on model category

### Parameter validation
- On `set_param`: look up model def in ModelDB, check value is within [min, max]
- Warn (don't hard-fail) if value out of range, so users can still experiment

### Snapshot handling
- `add_block` defaults to enabling the block in all snapshots
- Optional `snapshots=[0,1]` arg to control which snapshots enable the block

---

## CLI (`hx.py` + `hxlib/cli.py`)

```
python hx.py build-cache                          # (re)build SQLite from source JSON
python hx.py browse                               # list all categories
python hx.py browse distortion                    # list models in category
python hx.py inspect HD2_DistTriangleFuzz         # show params with ranges + defaults
python hx.py search "fuzz"                        # fuzzy name search
python hx.py search --category delay --max-load 8 # filter query

python hx.py show MusePlugInBaby.hlx              # human-readable preset dump
python hx.py new MyPreset.hlx                     # blank preset from template
python hx.py add MyPreset.hlx HD2_DistTriangleFuzz --position 1
python hx.py tweak MyPreset.hlx block1 Sustain 0.95
python hx.py remove MyPreset.hlx block1
```

CLI outputs plain text tables, readable in a terminal (no rich/curses dependencies).

---

## Implementation Order

1. **`hxlib/db.py`** — ModelDB with cache build + core queries (foundation everything else needs)
2. **`hxlib/preset.py`** — Preset/Block load, show, save, add_block, set_param
3. **`hxlib/__init__.py`** — package exports
4. **`hx.py` + `hxlib/cli.py`** — CLI wiring

---

## Dependencies
- Python 3.14+ stdlib only: `json`, `sqlite3`, `argparse`, `pathlib`, `os`
- No third-party runtime packages

---

## Verification
1. `python hx.py build-cache` — completes without error, `hx_cache.db` exists
2. `python hx.py browse compressor` — lists HD2_CompressorDeluxeComp and others
3. `python hx.py inspect HD2_CompressorDeluxeComp` — shows Threshold/Ratio/Attack/Release/Level matching MusePlugInBaby.hlx values
4. `python hx.py show MusePlugInBaby.hlx` — human-readable dump matches known blocks (DeluxeComp → TriangleFuzz → BritPlexiBrt)
5. `python hx.py new Test.hlx && python hx.py add Test.hlx HD2_DistTriangleFuzz` — load Test.hlx in HX Edit and verify it opens correctly
6. `python hx.py tweak MusePlugInBaby.hlx block1 Sustain 0.95` — open in HX Edit and confirm Triangle Fuzz Sustain = 0.95
