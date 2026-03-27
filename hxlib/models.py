"""SQLite cache for HX model data."""

import json
import pathlib
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import NotRequired, TypedDict

Path = pathlib.Path


# ---------------------------------------------------------------------------
# Public return types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Category:
    id: int
    name: str
    short_name: str
    model_count: int


@dataclass(frozen=True)
class Model:
    symbolic_id: str
    name: str
    category_id: int | None
    category_name: str | None
    mono: bool
    stereo: bool
    load: float | None
    load_stereo: float | None
    based_on: str | None


@dataclass(frozen=True)
class Param:
    symbolic_id: str
    name: str
    value_type: int
    display_type: str | None
    min_val: str | None
    max_val: str | None
    default_val: str | None


def _assets_dir() -> Path:
    # models.py → hxlib/ → project_root/ → assets/res/
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
    based_on     TEXT,
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

            model_info = self._load_model_info()
            for sym, based_on in model_info.items():
                conn.execute(
                    "UPDATE models SET based_on = ? WHERE symbolic_id = ?",
                    (based_on, sym),
                )

            self._write_meta(conn)

        return (model_count, param_count)

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def list_categories(self) -> list[Category]:
        """All categories with model count, ordered by id."""
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT c.id, c.name, c.short_name, COUNT(m.symbolic_id)
            FROM categories c
            LEFT JOIN models m ON m.category_id = c.id
            GROUP BY c.id
            ORDER BY c.id
            """
        ).fetchall()
        return [
            Category(id=r[0], name=r[1], short_name=r[2], model_count=r[3])
            for r in rows
        ]

    def find_category(self, query: str) -> list[Category]:
        """Case-insensitive match on name or short_name (exact first, then LIKE)."""
        conn = self._get_conn()
        q = query.lower()
        rows = conn.execute(
            """
            SELECT c.id, c.name, c.short_name, COUNT(m.symbolic_id)
            FROM categories c
            LEFT JOIN models m ON m.category_id = c.id
            WHERE LOWER(c.name) = ? OR LOWER(c.short_name) = ?
            GROUP BY c.id
            ORDER BY c.id
            """,
            (q, q),
        ).fetchall()
        if rows:
            return [
                Category(id=r[0], name=r[1], short_name=r[2], model_count=r[3])
                for r in rows
            ]
        rows = conn.execute(
            """
            SELECT c.id, c.name, c.short_name, COUNT(m.symbolic_id)
            FROM categories c
            LEFT JOIN models m ON m.category_id = c.id
            WHERE LOWER(c.name) LIKE '%' || ? || '%'
            GROUP BY c.id
            ORDER BY c.id
            """,
            (q,),
        ).fetchall()
        return [
            Category(id=r[0], name=r[1], short_name=r[2], model_count=r[3])
            for r in rows
        ]

    def list_models(self, category_id: int) -> list[Model]:
        """Models in a category, ordered by name, with category_name joined."""
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT m.symbolic_id, m.name, m.category_id, c.name,
                   m.mono, m.stereo, m.load, m.load_stereo, m.based_on
            FROM models m
            LEFT JOIN categories c ON c.id = m.category_id
            WHERE m.category_id = ?
            ORDER BY m.name
            """,
            (category_id,),
        ).fetchall()
        return [
            Model(
                symbolic_id=r[0],
                name=r[1],
                category_id=r[2],
                category_name=r[3],
                mono=bool(r[4]),
                stereo=bool(r[5]),
                load=r[6],
                load_stereo=r[7],
                based_on=r[8],
            )
            for r in rows
        ]

    def get_model(self, symbolic_id: str) -> Model | None:
        """Single model by symbolic_id, or None if not found."""
        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT m.symbolic_id, m.name, m.category_id, c.name,
                   m.mono, m.stereo, m.load, m.load_stereo, m.based_on
            FROM models m
            LEFT JOIN categories c ON c.id = m.category_id
            WHERE m.symbolic_id = ?
            """,
            (symbolic_id,),
        ).fetchone()
        if row is None:
            return None
        return Model(
            symbolic_id=row[0],
            name=row[1],
            category_id=row[2],
            category_name=row[3],
            mono=bool(row[4]),
            stereo=bool(row[5]),
            load=row[6],
            load_stereo=row[7],
            based_on=row[8],
        )

    def get_params(self, symbolic_id: str) -> list[Param]:
        """Params for a model, in sort_order."""
        conn = self._get_conn()
        rows = conn.execute(
            """
            SELECT symbolic_id, name, value_type, display_type,
                   min_val, max_val, default_val
            FROM params
            WHERE model_id = ?
            ORDER BY sort_order
            """,
            (symbolic_id,),
        ).fetchall()
        return [
            Param(
                symbolic_id=r[0],
                name=r[1],
                value_type=r[2],
                display_type=r[3],
                min_val=r[4],
                max_val=r[5],
                default_val=r[6],
            )
            for r in rows
        ]

    def search_models(self, query: str, category_id: int | None = None) -> list[Model]:
        """Case-insensitive LIKE search on model name, with optional category filter."""
        conn = self._get_conn()
        q = query.lower()
        rows = conn.execute(
            """
            SELECT m.symbolic_id, m.name, m.category_id, c.name,
                   m.mono, m.stereo, m.load, m.load_stereo, m.based_on
            FROM models m
            LEFT JOIN categories c ON c.id = m.category_id
            WHERE (LOWER(m.name) LIKE '%' || ? || '%'
                OR LOWER(COALESCE(m.based_on, '')) LIKE '%' || ? || '%')
              AND (? IS NULL OR m.category_id = ?)
            ORDER BY m.name
            """,
            (q, q, category_id, category_id),
        ).fetchall()
        return [
            Model(
                symbolic_id=r[0],
                name=r[1],
                category_id=r[2],
                category_name=r[3],
                mono=bool(r[4]),
                stereo=bool(r[5]),
                load=r[6],
                load_stereo=r[7],
                based_on=r[8],
            )
            for r in rows
        ]

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
        info_path = self._assets_dir.parent / "model-info.json"
        if info_path.exists():
            files.append(info_path)
        if not files:
            return 0.0
        return max(f.stat().st_mtime for f in files)

    def _load_model_info(self) -> dict[str, str]:
        """Load model-info.json → {symbolic_id: based_on}. Returns {} if absent."""
        info_path = self._assets_dir.parent / "model-info.json"
        if not info_path.exists():
            return {}
        with info_path.open(encoding="utf-8") as fh:
            raw: dict[str, dict[str, str]] = json.load(fh)
        return {
            sid: entry["based_on"] for sid, entry in raw.items() if "based_on" in entry
        }

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
