"""search command handler."""

from __future__ import annotations

import argparse
import sys

from hxlib.cli._common import DB_PATH, W_CAT, W_ID, W_NAME, col, db
from hxlib.db import ModelRow


def _print_search_results(query: str, results: list[ModelRow]) -> None:
    n = len(results)
    if n == 0:
        print(f'No models found matching "{query}".')
        return
    print(f'{n} model{"s" if n != 1 else ""} matching "{query}"\n')
    print(f"{col('Name', W_NAME)}  {col('ID', W_ID)}  {col('Category', W_CAT)}")
    for m in results:
        print(
            f"{col(m.name, W_NAME)}  {col(m.symbolic_id, W_ID)}"
            f"  {col(m.category_name or '', W_CAT)}"
        )


def search(args: argparse.Namespace) -> int:
    conn = db(DB_PATH)
    if conn is None:
        return 1
    with conn:
        category_id: int | None = None
        if args.category is not None:
            matches = conn.find_category(args.category)
            if not matches:
                print(f"error: no category matching '{args.category}'", file=sys.stderr)
                return 1
            if len(matches) > 1:
                names = ", ".join(r.name for r in matches)
                print(f"error: ambiguous — matches: {names}", file=sys.stderr)
                return 1
            category_id = matches[0].id
        results = conn.search_models(args.query, category_id=category_id)
        _print_search_results(args.query, results)
    return 0
