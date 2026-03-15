import subprocess


def test_repository_has_no_merge_conflict_markers() -> None:
    result = subprocess.run(
        ["python", "scripts/ci/check_merge_conflicts.py"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
