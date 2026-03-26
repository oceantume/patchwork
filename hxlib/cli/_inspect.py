"""inspect command handler."""

import argparse
import sys

from hxlib.cli._common import DB_PATH, col, db
from hxlib.db import ModelRow, ParamRow


def _print_model_detail(model: ModelRow, params: list[ParamRow]) -> None:
    modes: list[str] = []
    if model.mono:
        modes.append("mono")
    if model.stereo:
        modes.append("stereo")
    print(model.name)
    print(f"  ID:       {model.symbolic_id}")
    print(f"  Category: {model.category_name or 'None'}")
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


def inspect(args: argparse.Namespace) -> int:
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
