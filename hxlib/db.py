"""SQLite cache for HX model data."""

from __future__ import annotations

import json
import pathlib
import sqlite3
from datetime import UTC, datetime
from typing import NotRequired, TypedDict

Path = pathlib.Path


def _assets_dir() -> Path:
    # db.py → hxlib/ → project_root/ → assets/res/
    return Path(__file__).parent.parent / "assets" / "res"


# ---------------------------------------------------------------------------
# Internal TypedDicts (private)
# ---------------------------------------------------------------------------


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
    name: NotRequired[str]
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


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA = """
CREATE TABLE categories (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL,
    short_name TEXT NOT NULL
);

CREATE TABLE models (
    symbolic_id  TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    category_id  INTEGER REFERENCES categories(id),
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
    value_type   INTEGER NOT NULL,
    display_type TEXT,
    min_val      TEXT,
    max_val      TEXT,
    default_val  TEXT,
    sort_order   INTEGER NOT NULL
);

CREATE TABLE build_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


# ---------------------------------------------------------------------------
# ModelDB
# ---------------------------------------------------------------------------


class ModelDB:
    def __init__(self, db_path: Path, assets_dir: Path | None = None) -> None:
        self._db_path = db_path
        self._assets_dir = assets_dir if assets_dir is not None else _assets_dir()
        self._conn: sqlite3.Connection | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_fresh(self) -> bool:
        """True if DB exists and assets_mtime in build_meta >= max .models mtime."""
        if not self._db_path.exists():
            return False
        try:
            conn = sqlite3.connect(self._db_path)
            try:
                row = conn.execute(
                    "SELECT value FROM build_meta WHERE key = 'assets_mtime'"
                ).fetchone()
            finally:
                conn.close()
        except sqlite3.DatabaseError:
            return False
        if row is None:
            return False
        stored_mtime = float(row[0])
        current_mtime = self._max_mtime()
        return stored_mtime >= current_mtime

    def build(self, *, force: bool = False) -> tuple[int, int]:
        """Build/rebuild the cache. Returns (model_count, param_count).

        Raises FileNotFoundError if assets_dir is missing.
        Raises ValueError on malformed JSON or missing symbolicID.
        """
        if not self._assets_dir.exists():
            raise FileNotFoundError(f"assets directory not found: {self._assets_dir}")

        models_files = sorted(self._assets_dir.glob("*.models"))

        if not force and self.is_fresh():
            conn = self._get_conn()
            model_count = conn.execute("SELECT COUNT(*) FROM models").fetchone()[0]
            param_count = conn.execute("SELECT COUNT(*) FROM params").fetchone()[0]
            return (model_count, param_count)

        categories = self._load_categories()

        conn = self._get_conn()
        with conn:
            # Drop and recreate all tables
            for table in ("params", "models", "categories", "build_meta"):
                conn.execute(f"DROP TABLE IF EXISTS {table}")
            for stmt in _SCHEMA.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(stmt)

            # Insert categories
            for cat in categories:
                conn.execute(
                    "INSERT INTO categories (id, name, short_name) VALUES (?, ?, ?)",
                    (cat["id"], cat["name"], cat["shortName"]),
                )

            model_count = 0
            param_count = 0

            for models_file in models_files:
                m, p = self._insert_models_file(conn, models_file)
                model_count += m
                param_count += p

            self._write_meta(conn)

        return (model_count, param_count)

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> ModelDB:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self._db_path)
        return self._conn

    def _max_mtime(self) -> float:
        files = list(self._assets_dir.glob("*.models"))
        if not files:
            return 0.0
        return max(f.stat().st_mtime for f in files)

    def _load_categories(self) -> list[_RawCategory]:
        catalog_path = self._assets_dir / "HX_ModelCatalog.json"
        if not catalog_path.exists():
            return []
        with catalog_path.open(encoding="utf-8") as fh:
            raw: dict[str, list[_RawCategory]] | list[_RawCategory] = json.load(fh)
        # Catalog may be {"categories": [...]} or directly a list
        if isinstance(raw, dict):
            return raw.get("categories", [])
        return raw

    def _insert_models_file(
        self, conn: sqlite3.Connection, path: Path
    ) -> tuple[int, int]:
        with path.open(encoding="utf-8") as fh:
            items: list[_RawModel] = json.load(fh)

        model_count = 0
        param_count = 0
        source = path.name

        for idx, item in enumerate(items):
            if "symbolicID" not in item:
                raise ValueError(f"missing symbolicID in {source} at index {idx}")
            sym = item["symbolicID"]
            name = item.get("name", sym)
            conn.execute(
                """
                INSERT OR REPLACE INTO models
                    (symbolic_id, name, category_id, mono, stereo,
                     load, load_stereo, source_file)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sym,
                    name,
                    item.get("category"),
                    int(item.get("mono", False)),
                    int(item.get("stereo", False)),
                    item.get("load"),
                    item.get("load_stereo"),
                    source,
                ),
            )
            model_count += 1

            for order, param in enumerate(item.get("params", [])):
                if "symbolicID" not in param:
                    raise ValueError(
                        f"missing symbolicID in param of"
                        f" {source}[{idx}] at param index {order}"
                    )
                conn.execute(
                    """
                    INSERT INTO params
                        (model_id, symbolic_id, name, value_type, display_type,
                         min_val, max_val, default_val, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        sym,
                        param["symbolicID"],
                        param.get("name", param["symbolicID"]),
                        param["valueType"],
                        param.get("displayType"),
                        self._encode_scalar(param.get("min")),
                        self._encode_scalar(param.get("max")),
                        self._encode_scalar(param.get("default")),
                        order,
                    ),
                )
                param_count += 1

        return (model_count, param_count)

    def _encode_scalar(self, v: float | bool | str | int | None) -> str | None:
        if v is None:
            return None
        if isinstance(v, bool):  # must precede int — bool is subclass of int
            return "true" if v else "false"
        return str(v)

    def _write_meta(self, conn: sqlite3.Connection) -> None:
        now = datetime.now(UTC).isoformat()
        mtime = self._max_mtime()
        conn.execute(
            "INSERT OR REPLACE INTO build_meta (key, value) VALUES ('built_at', ?)",
            (now,),
        )
        conn.execute(
            "INSERT OR REPLACE INTO build_meta (key, value) VALUES ('assets_mtime', ?)",
            (str(mtime),),
        )
