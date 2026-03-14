# Discord Story Bot — AAA Foundation Blueprint

## 1) Vision and Non-Goals

### Product vision
A premium, story-first Discord platform where narrative reliability and continuity are first-class concerns. The bot should feel closer to a live narrative service than a command utility.

### Non-goals (for this phase)
- No real story/chapter JSON content.
- No prose writing.
- No final balancing of narrative pacing.

This phase defines architecture, contracts, and operational foundations.

---

## 2) Architecture Overview

### Style
**Hexagonal / Clean Architecture** with strict boundaries:
- **Interface Layer:** Discord adapters (slash commands, component interactions).
- **Application Layer:** Use cases and orchestration services.
- **Domain Layer:** Story engine, session state machine, validation rules.
- **Infrastructure Layer:** Persistence, caching, config, logging, telemetry.
- **Tooling Layer:** Admin/debug commands, content validation CLI, repair scripts.

### Core design principles
1. **Discord is a delivery channel, not the game logic.**
2. **Content is data, engine is deterministic logic.**
3. **All state transitions are explicit and auditable.**
4. **Every runtime decision should be replayable from logs + persisted state.**
5. **Validation is mandatory in CI and at startup in strict mode.**

### High-level runtime flow
1. User triggers `/story start`.
2. Discord layer maps command to `StartSessionUseCase`.
3. Use case loads player profile + content index + policy checks.
4. Domain `StoryEngine` computes initial scene payload.
5. Session + player state persisted transactionally.
6. Renderer returns Discord-safe view model (embed/buttons metadata).
7. Discord adapter sends message and stores message-session binding.
8. Button clicks route to `AdvanceSessionUseCase` and repeat deterministically.

---

## 3) Subsystems and Responsibilities

## A. Application Bootstrap
Responsibilities:
- Load configuration (env + secrets manager + typed config schema).
- Initialize structured logger and telemetry exporters.
- Build DI container / service registry.
- Load content manifests and run startup validation.
- Register commands and interaction routers.
- Start health heartbeat and graceful shutdown hooks.

Startup modes:
- `strict`: fail boot on content validation errors.
- `warn`: boot allowed, but problematic stories disabled.
- `maintenance`: disable player actions, enable admin diagnostics.

## B. Discord Interaction Layer
Responsibilities:
- Slash command parsing and permission checks.
- Component custom_id parsing + signature verification.
- Interaction ownership and anti-cross-user action checks.
- Rate-limit guards + anti-double-submit idempotency keys.
- Conversion between Discord payloads and app-layer DTOs.

Rules:
- No story branching logic here.
- No persistence SQL logic here.
- Return user-friendly errors + opaque incident code.

### Command set (initial)
Player:
- `/story start [campaign]`
- `/story continue`
- `/story restart [campaign]`
- `/story status`
- `/story help`

Admin:
- `/story-admin validate [campaign|all]`
- `/story-admin reload [campaign|all]`
- `/story-admin inspect-player <user>`
- `/story-admin inspect-session <session_id>`
- `/story-admin move-player <user> <node_ref>`
- `/story-admin repair-session <session_id> [mode]`
- `/story-admin close-session <session_id>`
- `/story-admin reopen-session <session_id>`
- `/story-admin render-preview <node_ref>`

## C. Story Engine (Domain Core)
Responsibilities:
- Resolve node by canonical node ref.
- Evaluate entry guards and choice availability conditions.
- Apply side effects (flags/counters/inventory-like keys if enabled).
- Resolve next node transitions and file handoffs.
- Determine terminal states/endings.
- Return `EngineStepResult` (pure structured response).

### Engine invariants
- Deterministic for same `(content_version, prior_state, action)`.
- No direct Discord classes.
- No IO side effects (except via injected state mutation contract in app layer).
- Emits traceable decision events for diagnostics.

`EngineStepResult` fields (example):
- `result_type`: `render_node | ending | blocked | error`
- `node_ref`
- `scene_payload` (title/body/media tokens)
- `available_choices[]`
- `state_patch` (flags/counters progress mutations)
- `session_patch` (node pointer, turn index, timestamps)
- `telemetry_events[]`

## D. Session System
Session is separate from player profile and from content.

Session lifecycle states:
- `CREATED`
- `ACTIVE`
- `WAITING_INPUT`
- `APPLYING_CHOICE`
- `COMPLETED`
- `CLOSED`
- `STALE`
- `BROKEN`

Required capabilities:
- Start / continue / resume after restart.
- Concurrency lock (optimistic version + short lease).
- Idempotent choice apply via action token.
- Message binding map (guild/channel/message/component version).
- Expiry + stale detection + recovery pathway.

Conflict policy:
- If two clicks race: first valid token wins; second gets stale interaction message.

## E. Player Story State Management
Separate aggregate:
- Campaign progress pointers.
- Global and campaign-scoped flags.
- Endings unlocked.
- Chapter/world unlock maps.
- Audit markers (last completed node, last choice time).

Design:
- Immutable snapshots for important milestones.
- Patch-based updates between snapshots.
- Migration layer for schema version changes.

## F. Content Loader
Responsibilities:
- Load campaign manifests and node files.
- Build in-memory indices:
  - node_ref -> node
  - campaign/chapter maps
  - reverse transition graph
- Track content version hash.
- Hot-reload with atomic swap (new version active only if validation passes).

## G. Content Validator
Mandatory pipeline component.

Validation categories:
1. **Schema validation**: required fields/types/enums.
2. **Integrity validation**: duplicate IDs, unresolved refs.
3. **Graph validation**: unreachable nodes, dead-end non-ending nodes.
4. **Semantic validation**: impossible conditions, contradictory flags.
5. **Convention validation**: naming/ID format, file placement.
6. **Policy validation**: max choice count, text length limits, localization keys.

Outputs:
- machine-readable report (JSON).
- human report (table/markdown).
- severity levels: `ERROR`, `WARN`, `INFO`.

## H. Persistence / Repositories
Use repository interfaces with swappable implementations.

Primary storage recommendation:
- **PostgreSQL** for durable state + audit metadata.
- Optional Redis for short-lived locks/cache.

Repositories:
- `PlayerRepository`
- `SessionRepository`
- `StoryProgressRepository`
- `MessageBindingRepository`
- `AdminActionAuditRepository`
- `ContentVersionRepository`

Transaction boundaries:
- Apply-choice transaction must atomically update session + player progress + turn history.

## I. Admin / Debug / Repair Tools
Concept: **Ops Console via slash commands + CLI parity**.

Capabilities:
- Content: validate/reload/version diff.
- Session: inspect, force close/reopen, rebind message, recompute next render.
- Player: set/mutate flags with audit reason, jump to node, rewind one turn.
- Diagnostics: simulate engine step from stored snapshot.
- Safety: all mutating commands require reason string and emit audit event.

## J. Testing Strategy
Test pyramid:
1. **Unit tests** (engine rules, condition evaluation, mutation application).
2. **Contract tests** (schema + repository interfaces).
3. **Integration tests** (session transactions, concurrency races).
4. **Golden tests** (render output snapshots from node fixtures).
5. **End-to-end tests** (Discord interaction flow with mocked gateway payloads).
6. **Chaos/recovery tests** (restart during apply-choice, lock expiry).

Coverage targets:
- Engine + validator: very high (90%+ meaningful branch coverage).
- App use cases: high.
- Discord adapters: moderate with focus on routing and guards.

## K. Logging / Telemetry / Diagnostics
Structured logging fields (minimum):
- `trace_id`, `span_id`, `guild_id`, `channel_id`, `user_id`
- `session_id`, `campaign_id`, `node_ref`, `content_version`
- `interaction_id`, `command_name`, `outcome`, `latency_ms`

Telemetry:
- Metrics:
  - session starts/completions/aborts
  - choice latency
  - validation errors by type
  - recovery events
  - admin mutation events
- Tracing:
  - command -> use case -> repo + engine spans.
- Alerts:
  - repeated broken sessions
  - spike in unresolved node_ref errors
  - persistent interaction failures

## L. Content Schema Strategy (No story content yet)

### File model
- `campaign.manifest.json`
- `chapters/<chapter_id>/chapter.meta.json`
- `chapters/<chapter_id>/nodes/<node_id>.node.json`
- `shared/conditions/*.cond.json` (optional reusable condition sets)

### Canonical identifiers
- `campaign_id`: `snake_case`
- `chapter_id`: `snake_case`
- `node_id`: `snake_case`
- `node_ref`: `campaign_id.chapter_id.node_id`
- `choice_id`: `choice_<snake_case>`
- `ending_id`: `ending_<snake_case>`

### Node schema (conceptual)
- `schema_version`
- `node_id`
- `node_type`: `scene | decision | transition | ending`
- `metadata`: tags, authoring notes, priority, rollout flags
- `presentation`: title/body/media tokens/localization keys
- `entry_conditions[]`
- `effects_on_enter[]`
- `choices[]` (for decision-capable nodes)
- `default_transition`
- `ending` (if terminal)

### Choice schema
- `choice_id`
- `label_key`
- `visibility_conditions[]`
- `selection_conditions[]`
- `effects_on_select[]`
- `transition`: local node or handoff ref
- `analytics_tag`

### Condition schema
- `op`: `eq | ne | gt | gte | lt | lte | in | not_in | and | or | not`
- `left`: operand ref (flag/counter/path)
- `right`: literal or operand ref
- nested boolean groups supported

### Effect schema
- `effect_type`: `set_flag | clear_flag | inc_counter | dec_counter | unlock | lock | append_log`
- `target`
- `value`
- `scope`: `global | campaign | session`

### Handoff schema
- `handoff_type`: `node_ref | chapter_entry | campaign_entry`
- `target_ref`
- `requirements[]`

### Ending schema
- `ending_id`
- `classification`: `good | bad | neutral | hidden | canonical`
- `reward_flags[]`
- `completion_policy`: `close_session | allow_restart_point`

### Metadata schema
- authored timestamps, owner, review status, test coverage tags.

## M. Project Directory Layout

```text
repo/
  src/
    app/
      bootstrap/
      config/
      container/
      lifecycle/
    interfaces/
      discord/
        commands/
        interactions/
        middleware/
        renderers/
        custom_id/
    application/
      dto/
      use_cases/
      services/
      policies/
    domain/
      engine/
      session/
      player/
      content/
      validation/
      events/
      errors/
    infrastructure/
      persistence/
        postgres/
        redis/
        migrations/
      repositories/
      content_loader/
      telemetry/
      logging/
      cache/
    tools/
      admin/
      validator_cli/
      repair/
  content/
    campaigns/
      <campaign_id>/
        campaign.manifest.json
        chapters/
          <chapter_id>/
            chapter.meta.json
            nodes/
  tests/
    unit/
    contract/
    integration/
    e2e/
    fixtures/
      content/
      sessions/
  docs/
    architecture-blueprint.md
    adr/
  scripts/
    ci/
    local/
  .github/
    workflows/
```

## N. Recovery and Reliability Strategy

Reliability patterns:
- **Optimistic concurrency** on session row version.
- **Idempotency tokens** per interaction action.
- **Outbox pattern** for audit/telemetry side-effects.
- **Graceful degraded mode** if content reload fails (keep previous valid version).
- **Session repair playbook** with deterministic recompute from turn history.

Restart recovery:
- On startup, scan sessions in transient states (`APPLYING_CHOICE`) older than threshold.
- Reconcile by replaying pending action log.
- Mark unresolved records `BROKEN` with admin-visible remediation hint.

---

## 4) Discord UX and Interaction Contract

### custom_id strategy
Format (signed):
`sb|v1|action:<type>|sid:<session_id>|turn:<n>|choice:<id>|nonce:<short>|sig:<hmac>`

Properties:
- Versioned.
- Tamper resistant.
- Encodes only routing essentials.
- Works across restarts/persistent views.

### Ownership and safety
- Session stores `owner_user_id` and permitted guild/channel.
- Reject interactions from non-owner with ephemeral guidance.
- Reject channel mismatches if configured as story-room strict mode.

### Session-to-message mapping
- Primary binding: active story message.
- Secondary bindings: historical transcript references (optional).
- Rebind command for admins when message deleted.

### Error UX
- User-facing errors are concise and recoverable.
- Include action hints (`/story continue`, `/story status`).
- Internal incident IDs logged for support trace.

---

## 5) Data Model (Persistence Concept)

Core tables (illustrative):
- `players`
- `player_campaign_progress`
- `player_flags`
- `sessions`
- `session_turns`
- `session_message_bindings`
- `unlocked_endings`
- `admin_audit_events`
- `content_versions`
- `idempotency_keys`

Key practices:
- Use UUID primary keys for session/audit entities.
- Composite unique constraints for natural keys (user+campaign active session).
- Soft-close sessions instead of hard delete.
- Keep append-only turn history for replay/debug.

---

## 6) Engineering Standards

### Naming and boundaries
- Domain terms must be ubiquitous language (`NodeRef`, `SessionState`, `ChoiceResolution`).
- No Discord-specific types in domain/application core.
- Every module exposes interfaces first, implementations second.

### Error handling
- Typed error categories:
  - `UserRecoverableError`
  - `ContentIntegrityError`
  - `ConcurrencyConflictError`
  - `InfraTransientError`
  - `InfraFatalError`
- Central error mapper for Discord responses.

### Dependency standards
- Dependency injection for repositories, clock, ID generator, random source.
- Avoid hidden globals.
- Deterministic clock in tests.

### Content authoring safety
- Pre-commit validator for changed content files.
- CI blocks merge on validation ERROR.
- Optional preview command for isolated node rendering.

### Maintainability
- ADRs for key decisions (engine DSL, lock model, schema versions).
- Semver for schema versioning and migration docs.

---

## 7) Validation Pipeline Design

Stages:
1. Parse + JSON schema validation.
2. Build symbol tables and detect duplicates.
3. Link references and handoffs.
4. Build graph and run reachability/dead-end checks.
5. Evaluate condition/effect compatibility rules.
6. Convention lint pass.
7. Emit reports and fail policy enforcement.

Modes:
- `quick` (local authoring)
- `full` (CI)
- `strict-prod` (startup)

Artifacts:
- `validation-report.json`
- `validation-report.md`
- optional graph visualization (`.dot`) for campaign maps.

---

## 8) Admin/Ops Workflow Examples

1. **Content incident:**
   - run validate -> inspect broken refs -> hot reload fixed version -> confirm with preview.
2. **Player stuck report:**
   - inspect session -> replay from turn history -> move or repair with reason -> audit log record.
3. **Post-deploy health check:**
   - monitor start/completion rate and error spikes by content version.

---

## 9) Roadmap (Architecture-first)

Phase 1: Foundation
- Bootstrapping, module skeleton, typed configs, logger/telemetry base.

Phase 2: Domain Core
- Engine, session state machine, repository interfaces, validation core.

Phase 3: Persistence + Discord Integration
- Postgres repos, command handlers, custom_id + ownership checks.

Phase 4: Admin and Repair Toolkit
- Validate/reload/inspect/repair commands + audit trail.

Phase 5: Hardening
- Recovery chaos tests, load tests, observability dashboards.

Phase 6: Content Authoring Enablement
- Introduce first campaign content only after validator + preview tooling are stable.

---

## 10) Why this blueprint is production-ready

- Strict separation prevents UI coupling to story logic.
- Deterministic engine + event history enables replay and repair.
- Validation-first pipeline protects content scale.
- Operational tools are planned as core features, not afterthoughts.
- Reliability patterns cover real Discord interaction edge cases.
- Architecture is ready for multi-campaign growth and team collaboration.
