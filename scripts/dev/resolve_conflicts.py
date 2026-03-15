from __future__ import annotations

import argparse
from pathlib import Path


class ConflictResolutionError(RuntimeError):
    """Raised when merge-conflict blocks are malformed."""


def resolve_text(text: str, strategy: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()

        if not stripped.startswith("<<<<<<<"):
            out.append(line)
            i += 1
            continue

        i += 1
        current: list[str] = []
        while i < len(lines) and not lines[i].lstrip().startswith("======="):
            current.append(lines[i])
            i += 1

        if i >= len(lines):
            raise ConflictResolutionError("Missing ======= marker in conflict block")

        i += 1
        incoming: list[str] = []
        while i < len(lines) and not lines[i].lstrip().startswith(">>>>>>>"):
            incoming.append(lines[i])
            i += 1

        if i >= len(lines):
            raise ConflictResolutionError("Missing >>>>>>> marker in conflict block")

        i += 1

        if strategy == "current":
            out.extend(current)
        elif strategy == "incoming":
            out.extend(incoming)
        elif strategy == "both":
            out.extend(current)
            out.extend(incoming)
        else:
            raise ConflictResolutionError(f"Unsupported strategy: {strategy}")

    return "".join(out)


def resolve_file(path: Path, strategy: str) -> bool:
    text = path.read_text(encoding="utf-8")
    resolved = resolve_text(text, strategy)
    changed = resolved != text
    if changed:
        path.write_text(resolved, encoding="utf-8")
    return changed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Resolve git merge conflict markers in files.")
    parser.add_argument("files", nargs="+", help="File paths to resolve")
    parser.add_argument(
        "--strategy",
        choices=["current", "incoming", "both"],
        default="current",
        help="How to resolve conflict blocks",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    changed_count = 0

    for raw in args.files:
        path = Path(raw)
        if not path.exists() or path.is_dir():
            raise SystemExit(f"Invalid file path: {raw}")

        changed = resolve_file(path, strategy=args.strategy)
        if changed:
            changed_count += 1
            print(f"resolved: {path}")
        else:
            print(f"no-conflicts: {path}")

    print(f"done, files updated: {changed_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
