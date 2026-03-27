# Plan: Add `based_on` field — storage, build overlay, search integration

## Context

The HX Stomp manual contains tables mapping each effect/amp model to the real-world gear it
emulates. This data doesn't exist in the `.models` asset files. The goal is to:
1. Author the mapping in a hand-maintained JSON sidecar (`assets/res/model-info.json`)
2. Apply it during cache build via a batch `UPDATE` after all `.models` files are inserted
3. Expose `based_on` on the `Model` dataclass and surface it in `inspect` output
4. Extend `search_models()` to match on `based_on` so users can find models by real-gear name

## Files

| File | Change |
|------|--------|
| `.gitignore` | Un-ignore `assets/res/model-info.json` specifically |
| `assets/model-info.json` | **New** — hand-authored mapping |
| `hxlib/models.py` | Schema, `Model` dataclass, build pipeline, queries, search |
| `hxlib/cli/_model.py` | Display `based_on` in `_print_model_detail` |
| `tests/fixtures/assets/model-info.json` | **New** — test fixture |
| `tests/test_models.py` | New test class `TestBasedOn`, extend `TestSearchModels` |

## Implementation

### 1. `.gitignore` — un-ignore the new file

The current rule `assets` ignores the whole directory. Git won't apply negations inside an
ignored directory, so a multi-step pattern is required:

```gitignore
# Replace: assets
/assets/**
!/assets/res/
/assets/res/**
!/assets/res/model-info.json
!tests/fixtures/assets/
```

- `/assets/**` — anchored to root, ignores all proprietary Line 6 files
- `!/assets/res/` — un-ignores the `res/` directory so git can look inside
- `/assets/res/**` — re-ignores everything inside `res/`
- `!/assets/res/model-info.json` — un-ignores only this file
- The existing `!tests/fixtures/assets/` exception stays (harmless; `tests/fixtures/assets/`
  is no longer caught by the new anchored pattern anyway)

### 2. `assets/res/model-info.json` (new)

Format: object-per-model, keyed by `symbolicID`. Start with the manual dump data.

```json
{
  "HD2_AmpGermanMahadeva": {"based_on": "Mesa/Boogie Mark IIC+"},
  "HD2_DistTopSecretOD": {"based_on": "Boss OD-1"}
}
```

Only `based_on` is needed initially. The per-model object structure allows adding fields
later without restructuring.

### 3. `hxlib/models.py`

#### a. `Model` dataclass — add field

```python
@dataclass(frozen=True)
class Model:
    ...
    load_stereo: float | None
    based_on: str | None          # ← add after load_stereo
```

#### b. `_SCHEMA` — add column to `models` table

```sql
CREATE TABLE models (
    ...
    load_stereo  REAL,
    based_on     TEXT,            -- ← add after load_stereo
    source_file  TEXT NOT NULL
);
```

#### c. `_max_mtime()` — include `model-info.json` in freshness check

```python
def _max_mtime(self) -> float:
    files = list(self._assets_dir.glob("*.models"))
    info_path = self._assets_dir / "model-info.json"
    if info_path.exists():
        files.append(info_path)
    if not files:
        return 0.0
    return max(f.stat().st_mtime for f in files)
```

#### d. New `_load_model_info()` method

```python
def _load_model_info(self) -> dict[str, str]:
    """Load model-info.json → {symbolic_id: based_on}. Returns {} if absent."""
    info_path = self._assets_dir / "model-info.json"
    if not info_path.exists():
        return {}
    with info_path.open(encoding="utf-8") as fh:
        raw: dict[str, dict[str, str]] = json.load(fh)
    return {sid: entry["based_on"] for sid, entry in raw.items() if "based_on" in entry}
```

#### e. `build()` — apply overlay after models are inserted

After the `for models_file in models_files` loop (line ~205), before `_write_meta`:

```python
model_info = self._load_model_info()
for sym, based_on in model_info.items():
    conn.execute(
        "UPDATE models SET based_on = ? WHERE symbolic_id = ?",
        (based_on, sym),
    )
```

#### f. All SELECT queries — add `m.based_on` as column index 8

Affected methods: `list_models`, `get_model`, `search_models`.
Each `SELECT` gains `m.based_on` appended to the column list.
Each `Model(...)` constructor gains `based_on=r[8]`.

#### g. `search_models()` — extend WHERE clause

```sql
WHERE (LOWER(m.name) LIKE '%' || ? || '%'
    OR LOWER(COALESCE(m.based_on, '')) LIKE '%' || ? || '%')
  AND (? IS NULL OR m.category_id = ?)
```

Parameters change from `(q, category_id, category_id)` to `(q, q, category_id, category_id)`.

### 4. `hxlib/cli/_model.py` — `_print_model_detail`

After the `Category:` line, add:

```python
if model.based_on:
    print(f"  Based on: {model.based_on}")
```

No changes to `_print_models` (browse list) or `_print_search_results` — display stays compact.

### 5. `tests/fixtures/assets/model-info.json` (new)

```json
{
  "HD2_DistCigaretteFuzz": {"based_on": "Fuzz Face Mk I"}
}
```

Covers one existing fixture model; others intentionally absent to test `None` path.

### 6. `tests/test_models.py`

#### New `TestBasedOn` class

```python
class TestBasedOn:
    def test_based_on_populated(self, db: ModelDB) -> None:
        model = db.get_model("HD2_DistCigaretteFuzz")
        assert model is not None
        assert model.based_on == "Fuzz Face Mk I"

    def test_based_on_none_when_absent(self, db: ModelDB) -> None:
        model = db.get_model("HD2_DistCobaltDrive")
        assert model is not None
        assert model.based_on is None
```

#### Extend `TestSearchModels`

```python
def test_search_by_based_on(self, db: ModelDB) -> None:
    results = db.search_models("fuzz face")
    assert len(results) == 1
    assert results[0].symbolic_id == "HD2_DistCigaretteFuzz"

def test_search_by_based_on_case_insensitive(self, db: ModelDB) -> None:
    results = db.search_models("FUZZ FACE")
    assert len(results) == 1
    assert results[0].symbolic_id == "HD2_DistCigaretteFuzz"
```

## Verification

```
uv run check
hx model build-cache --force
hx model inspect HD2_AmpGermanMahadeva   # should show "Based on: Mesa/Boogie Mark IIC+"
hx model search "mark iic"              # should find the amp model
hx model search "boss od"               # should find the OD model
```

All existing tests should pass. Two new `TestBasedOn` tests + two new search tests should pass.
