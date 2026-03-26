"""CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hxlib.db import ModelDB


def _build_cache(args: argparse.Namespace) -> int:
    db_path = Path(__file__).parent.parent / "hx_cache.db"
    db = ModelDB(db_path=db_path)
    try:
        if not args.force and db.is_fresh():
            print("Cache is already up to date. Use --force to rebuild.")
            return 0
        print("Building cache...", flush=True)
        model_count, param_count = db.build(force=args.force)
        print(f"Cached {model_count} models, {param_count} params")
        return 0
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"error: malformed asset data — {e}", file=sys.stderr)
        return 1
    finally:
        db.close()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hx", description="HX preset tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_cache = subparsers.add_parser(
        "build-cache", help="Build the local SQLite model cache"
    )
    build_cache.add_argument(
        "--force", action="store_true", help="Rebuild even if cache is fresh"
    )
    build_cache.set_defaults(func=_build_cache)

    return parser


def main() -> None:
    args = _build_parser().parse_args()
    sys.exit(args.func(args))
