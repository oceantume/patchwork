---
name: write-tests
description: Write integration tests for this project. Use when tests are needed for new or existing functionality.
argument-hint: [what to test]
allowed-tools: Read, Glob, Grep, Bash(uv run:*), Write, Edit
---

# write-tests

Write integration tests for the patchwork / hxlib project.

## Principles

- Protect **user-facing behaviour** from regression — what the public API returns, not how internals work.
- Tests must be **fast** — milliseconds per test. No I/O against the real `assets/` directory.
- Prefer small, hand-crafted **fixture data** that covers the important cases.
- Prefer not test private methods (`_encode_scalar`, `_insert_models_file`, etc.).

## Setting up the database in tests

Always use an **in-memory SQLite database** by passing `Path(":memory:")` as `db_path` and pointing `assets_dir` at a local fixture directory:

```python
from pathlib import Path
from hxlib.db import ModelDB

db = ModelDB(Path(":memory:"), assets_dir=Path("tests/fixtures/assets"))
db.build(force=True)
```

`Path(":memory:")` is never on disk — `is_fresh()` returns `False` immediately, so `build()` always runs without any freshness checks. The same connection is reused for all subsequent queries on that instance.

## Fixture data

Put fixture files under `tests/fixtures/assets/`. They should mirror the real asset format.

## Pytest conventions

- One test file per module: `tests/test_db.py` for `hxlib/db.py`.
- Use a shared `@pytest.fixture` in `tests/conftest.py` for the `ModelDB` instance.
- Group tests in classes (`class TestListCategories:`) or by function prefix.
- For `is_fresh()` tests that need a real file, use pytest's `tmp_path` fixture.
- All tests must pass under `uv run check`.

## Skeleton

```python
# tests/conftest.py
import pytest
from pathlib import Path
from hxlib.db import ModelDB

FIXTURES = Path(__file__).parent / "fixtures" / "assets"

@pytest.fixture()
def db() -> ModelDB:
    instance = ModelDB(Path(":memory:"), assets_dir=FIXTURES)
    instance.build(force=True)
    return instance
```
