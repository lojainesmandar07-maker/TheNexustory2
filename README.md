# TheNexustory2

Architecture-first foundation for a production-grade Discord story bot.

## Current implementation scope
- Application bootstrap and configuration model.
- Story domain contracts and deterministic engine core.
- Session lifecycle service with concurrency-safe transitions.
- Repository abstractions plus in-memory implementation for tests/dev.
- Unit tests for engine behavior and session rules.

## Next steps
- Add Discord gateway adapters and command handlers.
- Add Postgres repositories and migrations.
- Add content loader/validator pipeline.
