"""Run all checks in parallel and report failures."""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed


def _run(name: str, cmd: list[str]) -> tuple[str, int, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = (result.stdout + result.stderr).rstrip()
    return name, result.returncode, output


def main() -> None:
    checks: list[tuple[str, list[str]]] = [
        ("lint", ["ruff", "check", "."]),
        ("fmt", ["ruff", "format", "--check", "."]),
        ("types", ["pyright"]),
        ("test", ["pytest"]),
    ]

    results: dict[str, tuple[int, str]] = {}

    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(_run, name, cmd): name for name, cmd in checks}
        for future in as_completed(futures):
            name, code, output = future.result()
            results[name] = (code, output)

    failures: list[str] = []
    for name, cmd in checks:
        code, output = results[name]
        print(f"\n{'=' * 60}")
        print(f"  {name}: {' '.join(cmd)}  ({'PASS' if code == 0 else 'FAIL'})")
        print(f"{'=' * 60}")
        if output:
            print(output)
        if code != 0:
            failures.append(name)

    print(f"\n{'=' * 60}")
    if failures:
        print(f"FAILED: {', '.join(failures)}")
        sys.exit(1)
    else:
        print("All checks passed.")
