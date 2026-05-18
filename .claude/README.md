# Smith — `.claude/` catalog

This directory holds the agents, skills and rules that drive Claude Code on the Smith codebase. **Read this first** before adding or editing anything under `.claude/`.

## Mental model

```
agents       =  who works on a part of the codebase (backend / frontend)
skills       =  how a specific concern is done (REST, tests, i18n, OpenAPI, design system, ...)
rules        =  non-negotiable quality bars applied to every diff
```

Agents reference skills, skills reference rules. A skill is loaded when its description matches the task; a rule is always in effect for files under its `paths:` glob.

## Agents

Two agents — strictly scoped by directory. Each one studies the existing code before editing, runs the appropriate test suite, and refuses to declare a task complete on a failing build / coverage drop.

| Agent | Owns | Tooling | When to use |
|---|---|---|---|
| [`agents/java-springboot-developer.md`](agents/java-springboot-developer.md) | `backend/` (Java 24, Spring Boot 4, multi-module Maven) | `mvn -f backend/pom.xml verify`, Liquibase YAML, springdoc, Micrometer | Any backend change: REST endpoint, service, repository, connector, schema migration, metric, log event. |
| [`agents/angular-developer.md`](agents/angular-developer.md) | `frontend/` (Angular 21 zoneless, Tailwind v4, Transloco, Vitest) | `npm run lint`, `npm test --coverage`, `npm run build`, `npm run api:generate` | Any frontend change: component, signal store, http client wrapper, design-system primitive, i18n key. |

The two agents **delegate** to each other when work crosses the boundary. The Angular agent never invokes Maven; the Java agent never edits files under `frontend/`.

## Skills

A skill is loaded by an agent (or invoked directly) when the task it describes matches.

### Backend (`smi-java-springboot-developer`)

| Skill | One-line purpose |
|---|---|
| [`skills/java-springboot-standards`](skills/java-springboot-standards/SKILL.md) | Module layout, OpenAPI-first REST (springdoc), Lombok/MapStruct, exception handling, build-time `backend/openapi/` generation, **YAML-only** config. |
| [`skills/java-tests-coverage`](skills/java-tests-coverage/SKILL.md) | JUnit 5 + Mockito + Spring slices + Testcontainers, Jacoco gate (≥ 80% line / ≥ 70% branch). |
| [`skills/liquibase-conventions`](skills/liquibase-conventions/SKILL.md) | YAML changesets in `smith-database`, version-folder naming aligned with the Maven `<version>`, mandatory `comment` / `author` / `rollback`. |
| [`skills/backend-metrics`](skills/backend-metrics/SKILL.md) | Micrometer + Prometheus naming (`smith.<domain>.<entity>.<action>`), tag whitelist (low cardinality), what to instrument per surface, `application.yml` block. |
| [`skills/backend-logging`](skills/backend-logging/SKILL.md) | SLF4J + Logback levels semantics, structured `event.name key=value` messages, MDC correlation (`traceId` / `request_id` / `user_id`), JSON in prod, redaction, hot-path sampling, log testing. **Paired with `smi-backend-metrics`** — every business event has a metric and a log line that share names. |

### Frontend (`smi-angular-developer`)

| Skill | One-line purpose |
|---|---|
| [`skills/angular-standards`](skills/angular-standards/SKILL.md) | Project shape, standalone components, separated `.html` / `.ts`, signals, signal stores (TIER 3), Signal &gt; Observable &gt; Promise hierarchy. |
| [`skills/angular-tests-coverage`](skills/angular-tests-coverage/SKILL.md) | Vitest 4 + Testing Library, store/component/http-client patterns, ≥ 80% line/function/statement, ≥ 70% branch. |
| [`skills/angular-i18n-transloco`](skills/angular-i18n-transloco/SKILL.md) | Transloco with `fr` (default) + `en` (fallback), key convention, no hardcoded text, parity check between locale files. |
| [`skills/angular-openapi-client`](skills/angular-openapi-client/SKILL.md) | Three-tier HTTP architecture: TIER 1 generated (`src/app/api/`) ← TIER 2 hand-written shared per backend resource (`src/app/http-clients/`) ← TIER 3 stores. **Never invokes Maven** — consumes `backend/openapi/smith-api.json` and delegates regeneration to the Java agent. |
| [`skills/angular-design-system`](skills/angular-design-system/SKILL.md) | Unified UI primitives (`<ds-*>`), Tailwind v4 theme tokens, zero custom CSS in feature components, accessibility built into the design system. |

## Rules

Rules are **always on** for files matching their `paths:` glob. Both rules per language are mandatory; they pair `code-quality` (clean / secure / documented) with `code-reusability` (generic / DRY / no duplication).

### Java

| Rule | Scope |
|---|---|
| [`rules/java/code-quality.md`](rules/java/code-quality.md) | Java sources, Maven POMs, Spring YAML config, Liquibase changelogs. **YAML-only** for Spring config; `.properties` are forbidden. |
| [`rules/java/code-reusability.md`](rules/java/code-reusability.md) | DRY (with judgment), shared base classes / advices / mappers, central `dependencyManagement`, Liquibase folder ↔ Maven `<version>` coupling. |

### Angular

| Rule | Scope |
|---|---|
| [`rules/angular/code-quality.md`](rules/angular/code-quality.md) | TypeScript strict, signals over Observables over Promises, separated templates, Angular sanitization on, TSDoc on every export. |
| [`rules/angular/code-reusability.md`](rules/angular/code-reusability.md) | Shared design system, generated HTTP clients (no hand-rolled), no duplicate CSS, signal store pattern. |

## How a typical task flows

### Adding a new backend endpoint

1. **`smi-java-springboot-developer`** picks up the task, loads `smi-java-springboot-standards` + `smi-java-tests-coverage` + `smi-backend-metrics` + `smi-backend-logging`.
2. Implements layer-by-layer (`api → service → {database, connectors}`), with Bean Validation, springdoc annotations, MapStruct mapper.
3. Adds Liquibase changeset under `backend/smith-database/src/main/resources/db/changelog/<version>/` if the schema changes.
4. Adds Micrometer Timer + matching `INFO` log event with shared name.
5. Writes slice + integration tests covering every documented response code.
6. Runs `mvn -f backend/pom.xml verify` (Jacoco gate).
7. Runs `mvn -f backend/pom.xml -Popenapi -pl smith-api -am verify` to regenerate `backend/openapi/smith-api.{json,yaml}`.
8. Commits the contract delta in the same change.

### Consuming that endpoint from the frontend

1. **`smi-angular-developer`** picks up the task, loads `smi-angular-standards` + `smi-angular-openapi-client` + `smi-angular-tests-coverage` + (if visible) `smi-angular-i18n-transloco` + `smi-angular-design-system`.
2. Confirms `backend/openapi/smith-api.json` includes the endpoint. **Stops and delegates** to the Java agent if not.
3. Runs `npm run api:generate` (TIER 1 regenerated, no manual edits).
4. Adds / updates `frontend/src/app/http-clients/<resource>.http-client.ts` (TIER 2 — one per backend resource, shared).
5. Updates the feature store (TIER 3) — signals only, Observable subscribed at the boundary, no `firstValueFrom` / `await`.
6. Wires the smart container, dumb components from the design system, Transloco keys in `fr.json` + `en.json`.
7. Runs `npm run lint`, `npm test -- --coverage`, `npm run build`.

## Editing the catalog

When adding a new skill, agent or rule:

1. Place the file under the right folder (`agents/`, `skills/<name>/SKILL.md`, `rules/<lang>/<name>.md`).
2. Use the existing frontmatter format (`name:` / `description:` for skills, `description:` / `paths:` for rules).
3. Update **this README** in the same change — the catalog is the entry point and must stay accurate.
4. If the new piece changes the agents' procedure, update the relevant agent file too (`agents/*.md`).

Structural changes (new layer, new directory convention, new tier) **must** be reflected in `smi-angular-standards` (frontend) or `smi-java-springboot-standards` (backend) — these are the entry-point standards skills referenced by everything else.

## Companion artefacts in the repo

- `backend/openapi/smith-api.{json,yaml}` — API contract built by `mvn -Popenapi verify`. Single source of truth for the frontend HTTP client generator.
- `backend/smith-common/` — pure-Java utility module (no Spring / JPA / web). Hosts `UuidV7Generator` and other framework-agnostic helpers. Every other backend module depends on it (directly or transitively).
- `deploy/local/docker-compose.yml` — Postgres 17 + Redis 7 stack for local dev. **Not** required for OpenAPI generation (that runs in MockMvc with H2).
- `CLAUDE.md` (repo root) — pointer file; project context lives in `prompt.MD`.
