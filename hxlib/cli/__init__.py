"""CLI entry point."""

import argparse
import sys

from hxlib.cli._browse import browse
from hxlib.cli._build_cache import build_cache
from hxlib.cli._inspect import inspect
from hxlib.cli._search import search


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hx", description="HX preset tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_cache_p = subparsers.add_parser(
        "build-cache", help="Build the local SQLite model cache"
    )
    build_cache_p.add_argument(
        "--force", action="store_true", help="Rebuild even if cache is fresh"
    )
    build_cache_p.set_defaults(func=build_cache)

    browse_p = subparsers.add_parser("browse", help="List categories or models")
    browse_p.add_argument(
        "category", nargs="?", default=None, help="Category name or partial match"
    )
    browse_p.set_defaults(func=browse)

    inspect_p = subparsers.add_parser("inspect", help="Show model details and params")
    inspect_p.add_argument(
        "model_id", help="Symbolic model ID (e.g. HD2_DistKinkyBoost)"
    )
    inspect_p.set_defaults(func=inspect)

    search_p = subparsers.add_parser("search", help="Search models by name")
    search_p.add_argument("query", help="Search term")
    search_p.add_argument("-c", "--category", default=None, help="Filter by category")
    search_p.set_defaults(func=search)

    return parser


def main() -> None:
    args = _build_parser().parse_args()
    sys.exit(args.func(args))
