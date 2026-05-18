---
name: Backend Java rules
description: Java 24 + Spring Boot 4 patterns enforced on backend code only.
applyTo:
  - "backend/**/*.java"
  - "backend/**/pom.xml"
  - "backend/**/db/changelog/**/*.yaml"
---

# Backend Java rules

## Build + test
- Build : `cd backend && mvn -B -ntp verify` (full reactor).
- Test : `cd backend && mvn -B -ntp test` (unit) or `mvn -B verify`
  (unit + integration via Testcontainers).
- Coverage gate : JaCoCo 70% line / 60% branch ; do not lower.

## Style
- Lombok for boilerplate (`@Data`, `@Builder`, `@RequiredArgsConstructor`).
- MapStruct for DTO mapping — no hand-written mappers.
- Records for immutable DTOs (request + response).
- Constructor injection over field injection ; final fields only.

## Persistence
- Spring Data JPA + Hibernate, but service layers DTO-out at the boundary
  (never leak managed entities through controllers).
- Migrations : Liquibase YAML under
  `backend/smith-database/src/main/resources/db/changelog/`.
  Naming : `<NNN>-<verb-noun>.yaml`. NNN increments monotonically per
  feature ; never rewrite history.
- IDs : UUID v7 dual-id pattern — internal `long` primary key for joins,
  public `UUID` for API surfaces. Never leak the long id.

## REST
- OpenAPI-first : controllers implement generated interfaces.
- Bean Validation on every request DTO (`@NotNull`, `@Size`, `@Pattern`).
- HTTP status semantics : 201 on POST that creates, 204 on PUT/DELETE
  that returns no body, 200 on read.

## Observability
- Every service-method entry log uses key=value structured fields :
  `log.info("op=createUser email={} workspaceId={}", email, wsId)`.
- Micrometer metric for every external call : `http.client.duration`,
  `db.query.duration`, `redis.command.duration`.
- MDC fields : `traceId`, `userId`, `workspaceId` — propagated by the
  servlet filter under `smith-common`.

## What to avoid
- `@Autowired` field injection.
- Mockito for integration tests (use real containers).
- `RestTemplate` (deprecated) — use `RestClient` instead.
- Raw SQL in service code — go through repositories or `@Query`.

## Glossary
- Reactor : the multi-module Maven build under `backend/pom.xml`.
- Workspace : RBAC boundary ; every entity carries a `workspace_id`.
- Public id : the UUID exposed in APIs ; internal long stays in JPA only.
