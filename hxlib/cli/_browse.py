"""browse command handler."""

import argparse
import sys

from hxlib.cli._common import DB_PATH, W_ID, W_NAME, col, db
from hxlib.db import CategoryRow, ModelRow


def _print_categories(rows: list[CategoryRow]) -> None:
    print(f"{'ID':>4}  {'Name':<20}  {'Short':<8}  {'Models':>6}")
    for r in rows:
        print(f"{r.id:>4}  {r.name:<20}  {r.short_name:<8}  {r.model_count:>6}")


def _print_models(category: CategoryRow, models: list[ModelRow]) -> None:
    print(f"{category.name} — {category.model_count} models\n")
    print(
        f"{col('Name', W_NAME)}  {col('ID', W_ID)}"
        f"  {'Mono':>4}  {'Stereo':>6}  {'Load':>6}"
    )
    for m in models:
        load_str = f"{m.load:.2f}" if m.load is not None else ""
        mono_s = "y" if m.mono else "n"
        stereo_s = "y" if m.stereo else "n"
        print(
            f"{col(m.name, W_NAME)}  {col(m.symbolic_id, W_ID)}"
            f"  {mono_s:>4}  {stereo_s:>6}  {load_str:>6}"
        )


def browse(args: argparse.Namespace) -> int:
    conn = db(DB_PATH)
    if conn is None:
        return 1
    with conn:
        if args.category is None:
            rows = conn.list_categories()
            _print_categories(rows)
        else:
            matches = conn.find_category(args.category)
            if not matches:
                print(f"error: no category matching '{args.category}'", file=sys.stderr)
                return 1
            if len(matches) > 1:
                names = ", ".join(r.name for r in matches)
                print(f"error: ambiguous — matches: {names}", file=sys.stderr)
                return 1
            models = conn.list_models(matches[0].id)
            _print_models(matches[0], models)
    return 0
