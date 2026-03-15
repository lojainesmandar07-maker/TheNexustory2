from __future__ import annotations

import argparse
import subprocess
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

try:
    from scripts.dev.resolve_conflicts import resolve_file
except ModuleNotFoundError:
    resolver_path = Path(__file__).with_name("resolve_conflicts.py")
    resolver_spec = spec_from_file_location("resolve_conflicts", resolver_path)
    if resolver_spec is None or resolver_spec.loader is None:
        raise RuntimeError("Unable to load resolve_conflicts module")
    resolver_module = module_from_spec(resolver_spec)
    resolver_spec.loader.exec_module(resolver_module)
    resolve_file = resolver_module.resolve_file


DEFAULT_FILES = (
    "README.md",
    "src/storybot/app/bootstrap.py",
    "src/storybot/app/config.py",
    "src/storybot/domain/session_service.py",
    "src/storybot/interfaces/discord/contracts.py",
    "tests/unit/test_engine.py",
    "tests/unit/test_session_service.py",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve common PR merge-conflict files and run local validation checks."
    )
    parser.add_argument(
        "--strategy",
        choices=["current", "incoming", "both"],
        default="current",
        help="Conflict resolution strategy passed to resolver.",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=list(DEFAULT_FILES),
        help="Override default file list.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip pytest after conflict resolution.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    changed_count = 0
    for raw in args.files:
        path = Path(raw)
        if not path.exists() or path.is_dir():
            print(f"skip (missing): {raw}")
            continue

        changed = resolve_file(path, strategy=args.strategy)
        if changed:
            changed_count += 1
            print(f"resolved: {raw}")
        else:
            print(f"clean: {raw}")

    print(f"files resolved: {changed_count}")

    subprocess.check_call(["python", "scripts/ci/check_merge_conflicts.py"])
    if not args.skip_tests:
        subprocess.check_call(["pytest", "-q"])

    print("Conflict repair checks passed. You can now commit and push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
