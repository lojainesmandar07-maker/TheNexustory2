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


def parse_unmerged_from_porcelain(status_text: str) -> list[str]:
    paths: list[str] = []
    for raw in status_text.splitlines():
        if len(raw) < 4:
            continue
        xy = raw[:2]
        if "U" not in xy and xy not in {"AA", "DD"}:
            continue
        path = raw[3:].strip()
        if path:
            paths.append(path)
    return paths


def get_unmerged_files() -> list[str]:
    output = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    return parse_unmerged_from_porcelain(output)


def resolve_unmerged_files(paths: list[str], strategy: str) -> int:
    resolved = 0
    for raw in paths:
        path = Path(raw)
        if not path.exists() or path.is_dir():
            print(f"skip (missing): {raw}")
            continue
        if resolve_file(path, strategy=strategy):
            resolved += 1
            print(f"resolved: {raw}")
        else:
            print(f"clean: {raw}")
    return resolved


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve currently unmerged files in git status, stage them, and optionally continue merge/rebase."
    )
    parser.add_argument(
        "--strategy",
        choices=["current", "incoming", "both"],
        default="current",
        help="Conflict resolution strategy.",
    )
    parser.add_argument(
        "--continue",
        dest="do_continue",
        action="store_true",
        help="Run git merge --continue / rebase --continue / cherry-pick --continue if detected.",
    )
    return parser


def continue_if_needed() -> None:
    git_dir = Path(".git")
    if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
        subprocess.check_call(["git", "rebase", "--continue"])
        return
    if (git_dir / "MERGE_HEAD").exists():
        subprocess.check_call(["git", "merge", "--continue"])
        return
    if (git_dir / "CHERRY_PICK_HEAD").exists():
        subprocess.check_call(["git", "cherry-pick", "--continue"])


def main() -> int:
    args = build_parser().parse_args()
    unmerged = get_unmerged_files()
    if not unmerged:
        print("No unmerged files found.")
        return 0

    count = resolve_unmerged_files(unmerged, strategy=args.strategy)
    subprocess.check_call(["git", "add", *unmerged])
    print(f"staged files: {len(unmerged)} (resolved: {count})")

    subprocess.check_call(["python", "scripts/ci/check_merge_conflicts.py"])

    if args.do_continue:
        continue_if_needed()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
