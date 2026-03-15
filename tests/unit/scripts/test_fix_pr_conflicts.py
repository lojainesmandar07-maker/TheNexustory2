from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


def _load_module():
    path = Path("scripts/dev/fix_pr_conflicts.py")
    spec = spec_from_file_location("fix_pr_conflicts", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load fix_pr_conflicts module")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_conflict_file_list_includes_expected_paths() -> None:
    module = _load_module()
    assert "README.md" in module.DEFAULT_FILES
    assert "src/storybot/app/config.py" in module.DEFAULT_FILES
    assert "tests/unit/test_engine.py" in module.DEFAULT_FILES
