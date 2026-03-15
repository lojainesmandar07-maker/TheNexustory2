from __future__ import annotations

from pathlib import Path
import subprocess


_MARKER_PREFIXES = ("<" * 7, "=" * 7, ">" * 7)


def tracked_text_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], text=True)
    files: list[Path] = []
    for line in output.splitlines():
        path = Path(line.strip())
        if not path.exists() or path.is_dir():
            continue
        if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".lock", ".pyc"}:
            continue
        files.append(path)
    return files


def has_conflict_marker(text: str) -> bool:
    for raw_line in text.splitlines():
        line = raw_line.lstrip()
        if line.startswith(_MARKER_PREFIXES):
            return True
    return False


def main() -> int:
    flagged: list[str] = []
    for path in tracked_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if has_conflict_marker(text):
            flagged.append(str(path))

    if flagged:
        print("Unresolved merge conflict markers found:")
        for item in flagged:
            print(f" - {item}")
        return 1

    print("No unresolved merge conflict markers found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
