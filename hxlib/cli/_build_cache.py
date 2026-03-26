"""build-cache command handler."""

import argparse
import sys

from hxlib.cli._common import DB_PATH
from hxlib.db import ModelDB


def build_cache(args: argparse.Namespace) -> int:
    conn = ModelDB(db_path=DB_PATH)
    try:
        if not args.force and conn.is_fresh():
            print("Cache is already up to date. Use --force to rebuild.")
            return 0
        print("Building cache...", flush=True)
        model_count, param_count = conn.build(force=args.force)
        print(f"Cached {model_count} models, {param_count} params")
        return 0
    except FileNotFoundError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"error: malformed asset data — {e}", file=sys.stderr)
        return 1
    finally:
        conn.close()
