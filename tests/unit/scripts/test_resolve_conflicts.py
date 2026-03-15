from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


def _load_module():
    path = Path("scripts/dev/resolve_conflicts.py")
    spec = spec_from_file_location("resolve_conflicts", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load resolve_conflicts module")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONFLICT_SAMPLE = """alpha\n<<<<<<< ours\nA\n=======\nB\n>>>>>>> theirs\nomega\n"""


def test_resolve_text_current_strategy() -> None:
    module = _load_module()
    result = module.resolve_text(CONFLICT_SAMPLE, strategy="current")
    assert result == "alpha\nA\nomega\n"


def test_resolve_text_incoming_strategy() -> None:
    module = _load_module()
    result = module.resolve_text(CONFLICT_SAMPLE, strategy="incoming")
    assert result == "alpha\nB\nomega\n"


def test_resolve_text_both_strategy() -> None:
    module = _load_module()
    result = module.resolve_text(CONFLICT_SAMPLE, strategy="both")
    assert result == "alpha\nA\nB\nomega\n"


def test_resolve_text_raises_on_missing_markers() -> None:
    module = _load_module()
    malformed = """x\n<<<<<<< ours\nA\n"""
    with pytest.raises(module.ConflictResolutionError):
        module.resolve_text(malformed, strategy="current")


def test_file_resolution_roundtrip(tmp_path: Path) -> None:
    module = _load_module()
    target = tmp_path / "file.txt"
    target.write_text(CONFLICT_SAMPLE, encoding="utf-8")

    changed = module.resolve_file(target, strategy="incoming")
    assert changed is True
    assert target.read_text(encoding="utf-8") == "alpha\nB\nomega\n"
