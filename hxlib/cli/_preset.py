"""CLI commands for preset manipulation: hx preset <subcommand>."""

import argparse
import json
import sys
from pathlib import Path

from hxlib.cli._common import DB_PATH, col, db
from hxlib.preset import Preset, PresetError

_DEVICE_NAMES = {2162694: "HX Stomp"}
W_POS = 5
W_KEY = 8
W_MODEL = 32


def preset(args: argparse.Namespace) -> int:
    return args.preset_func(args)


# ---------------------------------------------------------------------------
# show
# ---------------------------------------------------------------------------


def _show(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        p = Preset.load(path)
    except (PresetError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    meta = p.meta
    blocks = p.list_blocks()
    did = p.device_id
    device_name = (
        _DEVICE_NAMES.get(did, f"device {did}") if did is not None else "unknown"
    )
    snapshots = p.list_snapshot_states()

    if args.json:
        snap_list: list[dict[str, object]] = []
        for idx, name, dsp0_snap in snapshots:
            snap_list.append(
                {
                    "index": idx,
                    "name": name,
                    "blocks": {k: v for k, v in dsp0_snap.items()},
                }
            )
        out = {
            "meta": {
                "name": meta.name,
                "application": meta.application,
                "modifieddate": meta.modifieddate,
            },
            "blocks": [
                {
                    "key": b.key,
                    "model_id": b.model_id,
                    "enabled": b.enabled,
                    "position": b.position,
                    "path": b.path,
                    "stereo": b.stereo,
                    "block_type": b.block_type,
                    "params": b.params,
                }
                for b in blocks
            ],
            "snapshots": snap_list,
        }
        print(json.dumps(out, indent=2))
        return 0

    print(f"Preset: {meta.name} ({device_name})")
    print()
    print("Signal Chain:")
    header = (
        "  "
        + col("pos", W_POS)
        + col("key", W_KEY)
        + col("model_id", W_MODEL)
        + "enabled"
    )
    print(header)
    for b in blocks:
        row = (
            "  "
            + col(str(b.position), W_POS)
            + col(b.key, W_KEY)
            + col(b.model_id, W_MODEL)
            + ("yes" if b.enabled else "no")
        )
        print(row)
    print()
    print("Snapshots:")
    for idx, name, dsp0_snap in snapshots:
        block_states = "  ".join(
            f"{k}={'on' if v else 'off'}" for k, v in sorted(dsp0_snap.items())
        )
        line = f"  {idx}  {name}"
        if block_states:
            line += f"  {block_states}"
        print(line)
    return 0


# ---------------------------------------------------------------------------
# new
# ---------------------------------------------------------------------------


def _new(args: argparse.Namespace) -> int:
    p = Preset.new(args.name)
    out = Path(args.output)
    try:
        p.save(out)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Created {out}")
    return 0


# ---------------------------------------------------------------------------
# add
# ---------------------------------------------------------------------------


def _add(args: argparse.Namespace) -> int:
    mdb = db(DB_PATH)
    if mdb is None:
        return 1

    path = Path(args.file)
    try:
        p = Preset.load(path)
    except (PresetError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    try:
        snapshots = [int(s) for s in args.snapshots.split(",") if s.strip()]
    except ValueError:
        print("error: --snapshots must be comma-separated integers", file=sys.stderr)
        return 1

    try:
        block_key = p.add_block(
            model_id=args.model_id,
            position=args.position,
            snapshots=snapshots,
            db=mdb,
            path=args.path,
            stereo=args.stereo,
        )
    except PresetError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        mdb.close()

    try:
        p.save(path)
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    if args.json:
        blk = p.get_block(block_key)
        assert blk is not None
        print(
            json.dumps(
                {
                    "block_key": block_key,
                    "model_id": blk.model_id,
                    "position": blk.position,
                    "path": blk.path,
                },
                indent=2,
            )
        )
    else:
        print(f"Added {args.model_id} as {block_key} at position {args.position}")
    return 0


# ---------------------------------------------------------------------------
# remove
# ---------------------------------------------------------------------------


def _remove(args: argparse.Namespace) -> int:
    path = Path(args.file)
    try:
        p = Preset.load(path)
        p.remove_block(args.block_key)
        p.save(path)
    except (PresetError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    print(f"Removed {args.block_key}")
    return 0


# ---------------------------------------------------------------------------
# set
# ---------------------------------------------------------------------------


def _coerce_value(s: str) -> int | float | bool:
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    try:
        return int(s)
    except ValueError:
        return float(s)


def _set(args: argparse.Namespace) -> int:
    mdb = db(DB_PATH)
    path = Path(args.file)
    try:
        p = Preset.load(path)
        value = _coerce_value(args.value)
        p.set_param(args.block_key, args.param, value, db=mdb)
        p.save(path)
    except (PresetError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        if mdb is not None:
            mdb.close()
    print(f"Set {args.block_key}/{args.param} = {args.value}")
    return 0


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------


def _validate(args: argparse.Namespace) -> int:
    mdb = db(DB_PATH)
    if mdb is None:
        return 1

    path = Path(args.file)
    try:
        p = Preset.load(path)
        issues = p.validate(mdb)
    except (PresetError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    finally:
        mdb.close()

    if args.json:
        print(
            json.dumps(
                {
                    "valid": len(issues) == 0,
                    "issues": [
                        {
                            "severity": i.severity,
                            "location": i.location,
                            "message": i.message,
                        }
                        for i in issues
                    ],
                },
                indent=2,
            )
        )
        return 0

    if not issues:
        print("Preset is valid.")
    else:
        for i in issues:
            print(f"{i.severity}: [{i.location}] {i.message}")
    return 1 if issues else 0


# Handler references for parser setup (used by cli/__init__.py)
preset_show = _show
preset_new = _new
preset_add = _add
preset_remove = _remove
preset_set = _set
preset_validate = _validate
