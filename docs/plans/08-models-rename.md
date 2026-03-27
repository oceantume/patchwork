# Plan: Rename `hxlib/db` → `hxlib/models`, drop `Row` suffix from data classes

## Context

`hxlib/db.py` exposes `ModelRow`, `CategoryRow`, and `ParamRow` as its public API, leaking
SQLite/storage vocabulary into domain-facing code. The module is really a model data store,
not a generic database module. Renaming the file to `hxlib/models.py` and dropping the `Row`
suffix makes the public API reflect the domain rather than the implementation.

`ModelDB` keeps its name — it's a class that explicitly manages a database, so the `DB`
suffix is intentional and descriptive.

## Files

| File | Action |
|------|--------|
| `hxlib/db.py` | Rename → `hxlib/models.py`; rename 3 classes inside |
| `hxlib/__init__.py` | Update import path and symbol names |
| `hxlib/cli/_common.py` | Update import path |
| `hxlib/cli/_model.py` | Update import path and all usages of renamed types |
| `hxlib/preset.py` | Update import path and all usages of renamed types |
| `tests/conftest.py` | Update import path |
| `tests/test_db.py` | Rename → `tests/test_models.py`; update import path |
| `tests/test_preset.py` | Update import path and type annotations |

## Implementation

### 1. Rename `hxlib/db.py` → `hxlib/models.py`

Rename the file, then inside it rename the three data classes:

| Old name | New name |
|----------|----------|
| `CategoryRow` | `Category` |
| `ModelRow` | `Model` |
| `ParamRow` | `Param` |

`ModelDB` is unchanged. The internal `TypedDict` helpers (`_RawParam`, `_RawModel`,
`_RawCategory`) and all private implementation details are unchanged.

### 2. Update `hxlib/__init__.py`

```python
from hxlib.models import Category, Model, ModelDB, Param
```

Update `__all__` to use the new names.

### 3. Update `hxlib/cli/_common.py`

```python
from hxlib.models import ModelDB
```

### 4. Update `hxlib/cli/_model.py`

```python
from hxlib.models import Category, Model, ModelDB, Param
```

Update all type annotations:
- `list[CategoryRow]` → `list[Category]`
- `category: CategoryRow` → `category: Category`
- `list[ModelRow]` → `list[Model]`
- `model: ModelRow` → `model: Model`
- `list[ParamRow]` → `list[Param]`
- `params: list[ParamRow]` → `params: list[Param]`

### 5. Update `hxlib/preset.py`

```python
from hxlib.models import ModelDB
```

No type annotation changes needed — only `ModelDB` is used here.

### 6. Update `tests/conftest.py`

```python
from hxlib.models import ModelDB
```

### 7. Rename `tests/test_db.py` → `tests/test_models.py`

Update import:
```python
from hxlib.models import ModelDB
```

No other changes needed — tests exercise `ModelDB` methods and don't reference the
renamed data classes by name.

### 8. Update `tests/test_preset.py`

```python
from hxlib.models import ModelDB
```

## Verification

```
uv run check
hx model browse
hx model inspect HD2_DistKinkyBoost
```

All 77 tests should pass. Types and lint should be clean.
