# TheNexustory2

Architecture-first foundation for a production-grade Discord story bot.

## Current implementation scope
- Application bootstrap and configuration model.
- Story domain contracts and deterministic engine core.
- Session lifecycle service with safer state-transition guards.
- Repository abstractions plus in-memory implementation for tests/dev.
- Discord-facing command handler layer with signed custom_id flow, ownership checks, and stale-interaction rejection.
- Unit tests for engine behavior, session rules, and Discord interaction contracts.

## Next steps
- Add actual Discord gateway adapter wiring (slash commands + component callbacks).
- Add Postgres repositories and migrations.
- Add content loader/validator pipeline.
- Add admin/debug command surface.

## Quality gates
- Unit tests run via `pytest -q`.
- A merge-conflict marker check (`python scripts/ci/check_merge_conflicts.py`) blocks unresolved conflict artifacts (`<<<<<<<`, `=======`, `>>>>>>>`) from landing in commits/PRs.

## Conflict recovery helper
If a file contains merge markers from GitHub (`<<<<<<<`, `=======`, `>>>>>>>`), you can auto-resolve it with:

```bash
python scripts/dev/resolve_conflicts.py --strategy current README.md src/storybot/app/config.py
```

Available strategies: `current`, `incoming`, `both`.

Quick PR conflict repair command:

```bash
python scripts/dev/fix_pr_conflicts.py --strategy current
```

If you are in an active merge/rebase with unmerged files, run:

```bash
python scripts/dev/merge_assistant.py --strategy current --continue
```

This resolves all currently unmerged files from `git status --porcelain`, stages them, runs conflict-marker checks, and continues merge/rebase when possible.
