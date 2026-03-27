# HX Stuff — Project Scaffold Plan

## Context
Initialize the `C:\devel\hx-stuff` project with modern Python tooling — no features yet, just a working scaffold. The goal is a `uv run check` command an AI agent can run to validate everything at once (lint, format, types, tests all pass on a clean project).

---

## Chosen Stack
| Concern | Tool |
|---|---|
| Package manager | uv |
| Python version | 3.14+ |
| Type checker | pyright (strict mode) |
| Lint + format | ruff |
| Tests | pytest |
| Composite check | `uv run check` → `scripts/check.py` |
| Layout | Flat: `hx.py` + `hxlib/` at root |
| Pre-commit / CI | None |

---

## Files Created

### `pyproject.toml`
Defines the project, build system (hatchling), dev dependencies (pyright, pytest, ruff), tool config for ruff/pyright/pytest, and uv script aliases.

Key uv scripts:
- `uv run check` — runs all checks in sequence via `scripts/check.py`
- `uv run lint` — ruff lint only
- `uv run fmt` — ruff format check only
- `uv run types` — pyright only
- `uv run test` — pytest only

### `scripts/check.py`
Runs all four tools in sequence, collects failures, reports them all, exits non-zero if any failed.

### `hxlib/__init__.py`
Package root (stub).

### `hxlib/py.typed`
PEP 561 marker — tells type checkers this package ships type annotations.

### `hxlib/cli.py`
`main()` entry point stub — to be implemented.

### `hx.py`
Thin shim for `python hx.py` direct invocation. Delegates to `hxlib.cli.main`.

### `tests/test_placeholder.py`
Single passing test so pytest runs cleanly on a fresh scaffold.

### `.gitignore`
Excludes `.venv/`, `__pycache__/`, `hx_cache.db`, build artifacts.

---

## Initialization Sequence

```sh
uv sync --group dev   # creates .venv, installs pyright + ruff + pytest
uv run check          # must exit 0
```

---

## Verification

`uv run check` exits 0 with all four checks passing:
- `ruff check .` — no lint errors
- `ruff format --check .` — no formatting issues
- `pyright` (strict) — 0 errors, 0 warnings
- `pytest` — 1 passed (placeholder test)
