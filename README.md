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
