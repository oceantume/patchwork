"""CLI entry point."""

import argparse
import sys

from hxlib.cli._browse import browse
from hxlib.cli._build_cache import build_cache
from hxlib.cli._inspect import inspect
from hxlib.cli._preset import (
    preset,
    preset_add,
    preset_move,
    preset_new,
    preset_remove,
    preset_set,
    preset_show,
    preset_validate,
)
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

    preset_p = subparsers.add_parser("preset", help="Load, create, and edit presets")
    preset_p.set_defaults(func=preset)
    preset_sub = preset_p.add_subparsers(dest="preset_command", required=True)

    show_p = preset_sub.add_parser("show", help="Print block list and snapshot state")
    show_p.add_argument("file", help="Preset file (.hlx)")
    show_p.add_argument("--json", action="store_true", help="Output JSON")
    show_p.set_defaults(preset_func=preset_show)

    new_p = preset_sub.add_parser("new", help="Create preset from template")
    new_p.add_argument("name", help="Preset name")
    new_p.add_argument("output", help="Output file path")
    new_p.set_defaults(preset_func=preset_new)

    add_p = preset_sub.add_parser("add", help="Add effect block")
    add_p.add_argument("file", help="Preset file (.hlx)")
    add_p.add_argument("model_id", help="Symbolic model ID")
    add_p.add_argument("--position", type=int, required=True, help="Position 0-5")
    add_p.add_argument(
        "--snapshots",
        required=True,
        help="Comma-separated snapshot indices (e.g. 0,1,2)",
    )
    add_p.add_argument("--path", type=int, default=0, help="Signal path (0=A, 1=B)")
    add_p.add_argument("--stereo", action="store_true", help="Stereo block")
    add_p.add_argument("--json", action="store_true", help="Output JSON")
    add_p.set_defaults(preset_func=preset_add)

    remove_p = preset_sub.add_parser("remove", help="Remove effect block")
    remove_p.add_argument("file", help="Preset file (.hlx)")
    remove_p.add_argument("block_key", help="Block key (e.g. block0)")
    remove_p.set_defaults(preset_func=preset_remove)

    move_p = preset_sub.add_parser("move", help="Move a block to a different position")
    move_p.add_argument("file", help="Preset file (.hlx)")
    move_p.add_argument("block_key", help="Block key (e.g. block0)")
    move_p.add_argument("--position", type=int, required=True, help="New position 0–5")
    move_p.add_argument(
        "--path", type=int, default=None, help="New signal path (0=A, 1=B)"
    )
    move_p.set_defaults(preset_func=preset_move)

    set_p = preset_sub.add_parser("set", help="Set a block parameter value")
    set_p.add_argument("file", help="Preset file (.hlx)")
    set_p.add_argument("block_key", help="Block key (e.g. block0)")
    set_p.add_argument("param", help="Parameter name")
    set_p.add_argument("value", help="Parameter value")
    set_p.set_defaults(preset_func=preset_set)

    validate_p = preset_sub.add_parser(
        "validate", help="Validate preset against model DB"
    )
    validate_p.add_argument("file", help="Preset file (.hlx)")
    validate_p.add_argument("--json", action="store_true", help="Output JSON")
    validate_p.set_defaults(preset_func=preset_validate)

    return parser


def main() -> None:
    args = _build_parser().parse_args()
    sys.exit(args.func(args))
