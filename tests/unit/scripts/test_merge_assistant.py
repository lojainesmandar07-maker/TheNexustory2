from importlib.util import module_from_spec, spec_from_file_location


def _load_module():
    spec = spec_from_file_location("merge_assistant", "scripts/dev/merge_assistant.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load merge_assistant")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_unmerged_from_porcelain_detects_conflicts() -> None:
    module = _load_module()
    status = """UU README.md
 M pyproject.toml
AA src/storybot/app/config.py
DU docs/architecture-blueprint.md
"""
    files = module.parse_unmerged_from_porcelain(status)
    assert files == [
        "README.md",
        "src/storybot/app/config.py",
        "docs/architecture-blueprint.md",
    ]


def test_parse_unmerged_from_porcelain_ignores_clean_lines() -> None:
    module = _load_module()
    status = """ M README.md
?? new_file.py
"""
    assert module.parse_unmerged_from_porcelain(status) == []
