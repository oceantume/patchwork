"""CLI commands for model browsing: hx model <subcommand>."""

import argparse
import sys

from hxlib.cli._common import DB_PATH, W_CAT, W_ID, W_NAME, col, db
from hxlib.models import Category, Model, ModelDB, Param


def _print_categories(rows: list[Category]) -> None:
    print(f"{'ID':>4}  {'Name':<20}  {'Short':<8}  {'Models':>6}")
    for r in rows:
        print(f"{r.id:>4}  {r.name:<20}  {r.short_name:<8}  {r.model_count:>6}")


def _print_models(category: Category, models: list[Model]) -> None:
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


def _browse(args: argparse.Namespace) -> int:
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


def _print_model_detail(model: Model, params: list[Param]) -> None:
    modes: list[str] = []
    if model.mono:
        modes.append("mono")
    if model.stereo:
        modes.append("stereo")
    print(model.name)
    print(f"  ID:       {model.symbolic_id}")
    print(f"  Category: {model.category_name or 'None'}")
    if model.based_on:
        print(f"  Based on: {model.based_on}")
    print(f"  Modes:    {', '.join(modes) if modes else 'none'}")
    if model.load is not None and model.mono:
        load_str = f"{model.load:.2f} (mono)"
        if model.load_stereo is not None:
            load_str += f" / {model.load_stereo:.2f} (stereo)"
        print(f"  Load:     {load_str}")
    elif model.load_stereo is not None:
        print(f"  Load:     {model.load_stereo:.2f} (stereo)")

    if params:
        print()
        print("Params:")
        _W_PNAME = 20
        _W_PSYM = 20
        _W_TYPE = 8
        _W_VAL = 8
        print(
            f"  {col('Name', _W_PNAME)}  {col('Sym', _W_PSYM)}"
            f"  {col('Type', _W_TYPE)}  {col('Min', _W_VAL)}"
            f"  {col('Max', _W_VAL)}  {col('Default', _W_VAL)}"
        )
        type_names = {0: "int", 1: "float", 2: "bool", 3: "str"}
        for p in params:
            tname = type_names.get(p.value_type, str(p.value_type))
            print(
                f"  {col(p.name, _W_PNAME)}  {col(p.symbolic_id, _W_PSYM)}"
                f"  {col(tname, _W_TYPE)}  {col(p.min_val or '', _W_VAL)}"
                f"  {col(p.max_val or '', _W_VAL)}"
                f"  {col(p.default_val or '', _W_VAL)}"
            )


def _inspect(args: argparse.Namespace) -> int:
    conn = db(DB_PATH)
    if conn is None:
        return 1
    with conn:
        model = conn.get_model(args.model_id)
        if model is None:
            print(f"error: model '{args.model_id}' not found", file=sys.stderr)
            return 1
        params = conn.get_params(args.model_id)
        _print_model_detail(model, params)
    return 0


def _print_search_results(query: str, results: list[Model]) -> None:
    n = len(results)
    if n == 0:
        print(f'No models found matching "{query}".')
        return
    print(f'{n} model{"s" if n != 1 else ""} matching "{query}"\n')
    print(
        f"{col('Name', W_NAME)}  {col('ID', W_ID)}"
        f"  {col('Category', W_CAT)}  {'Load':>6}"
    )
    for m in results:
        load_str = f"{m.load:.2f}" if m.load is not None else ""
        print(
            f"{col(m.name, W_NAME)}  {col(m.symbolic_id, W_ID)}"
            f"  {col(m.category_name or '', W_CAT)}  {load_str:>6}"
        )


def _search(args: argparse.Namespace) -> int:
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


def _build_cache(args: argparse.Namespace) -> int:
    conn = ModelDB(db_path=DB_PATH)
    try:
        if not args.force and conn.is_fresh():
            print("Cache is already up to date. Use --force to rebuild.")
            return 0
        print("Building cache...", flush=True)
        category_count, model_count, param_count = conn.build(force=args.force)
        print(
            f"Cached {category_count} categories,"
            f" {model_count} models, {param_count} params"
        )
        return 0
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"error: malformed asset data — {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()


def model(args: argparse.Namespace) -> int:
    return args.model_func(args)


# Handler references for parser setup (used by cli/__init__.py)
model_browse = _browse
model_inspect = _inspect
model_search = _search
model_build_cache = _build_cache
