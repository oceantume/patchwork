"""Shared CLI utilities."""

from __future__ import annotations

import sys
from pathlib import Path

from hxlib.db import ModelDB

W_NAME = 32
W_ID = 32
W_CAT = 16

DB_PATH = Path(__file__).parent.parent.parent / "hx_cache.db"


def col(value: str, width: int, align: str = "<") -> str:
    return format(value, f"{align}{width}")


def db(db_path: Path) -> ModelDB | None:
    if not db_path.exists():
        print('error: cache not found — run "hx build-cache" first', file=sys.stderr)
        return None
    return ModelDB(db_path=db_path)
