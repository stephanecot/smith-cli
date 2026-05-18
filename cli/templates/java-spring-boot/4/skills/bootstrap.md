# Skill — bootstrap a Java / Spring Boot 4 project

Use this skill when the user asks to scaffold a new Java / Spring Boot
4 service from scratch — the project root is empty (or contains only
`.smith/`) and the user wants a working `mvn -B verify` baseline.

## How to invoke

The user types something like "bootstrap a new Spring Boot service",
"set up a Java backend", "create a new Spring Boot app called X".

If the slash form is wired by the consumer, also `/{{slash-name}}`.

## What you do

### Phase 0 — Pre-flight (ask, don't guess)

Ask the user via `AskUserQuestion` (or inline questions) :

1. **Group + artifact id** (Maven coordinates). Defaults :
   `groupId = com.example`, `artifactId = <project-name>` from the
   current directory's base name. Use `--name` if passed.
2. **Java version** : 24 (matches Spring Boot 4 baseline) by default.
   Confirm the toolchain (Temurin / Corretto / Liberica) — store in
   `pom.xml` properties.
3. **Persistence** : `none` | `jpa-postgres` | `jpa-h2` |
   `mongo` | `dynamodb`. Default `none`.
4. **Inbound interface(s)** : `rest` (default) | `rest+websocket` |
   `grpc` | `cli`.
5. **Liquibase** : on/off (default `on` when persistence ≠ `none`,
   `off` otherwise).
6. **OpenAPI** : springdoc-openapi to expose `/v3/api-docs` (default
   `on` when `rest` is selected).
7. **Module layout** : single module (default) | multi-module (asks
   for the module list).
8. **Test stack** : JUnit 5 + Mockito (default) ; if persistence is
   on, also Testcontainers.

### Phase 1 — Generate the project tree

Write the files **atomically** (Write tool, tempfile if available).

#### Single-module layout

```
<project-root>/
├── .gitignore
├── README.md
├── pom.xml
├── src/
│   ├── main/
│   │   ├── java/{{groupId-as-path}}/{{ArtifactName}}Application.java
│   │   └── resources/
│   │       ├── application.yaml
│   │       └── db/changelog/db.changelog-master.yaml   # if liquibase
│   └── test/
│       └── java/{{groupId-as-path}}/{{ArtifactName}}ApplicationTests.java
```

#### Multi-module layout

Adapt — root pom is `<packaging>pom</packaging>` with `<modules>` ;
each module mirrors the single-module shape under its sub-folder.
Recommended split for a service : `*-api` (controllers + DTOs),
`*-service` (business logic), `*-data` (entities + Liquibase),
`*-common` (shared types + filters).

### Phase 2 — `pom.xml` essentials

- `<parent>` `org.springframework.boot:spring-boot-starter-parent:4.0.0`.
- `<properties>` `java.version = 24`, `project.build.sourceEncoding = UTF-8`.
- Starters added per the user's answers :
  - REST : `spring-boot-starter-web` + `spring-boot-starter-validation`.
  - JPA : `spring-boot-starter-data-jpa` + `postgresql` (runtime) or `h2` (runtime+test).
  - Mongo : `spring-boot-starter-data-mongodb`.
  - Actuator : always (`spring-boot-starter-actuator`).
  - Test : `spring-boot-starter-test` (transitively : JUnit 5,
    Mockito, AssertJ). Add `org.testcontainers:postgresql:1.20.1`
    when JPA + postgres.
- Liquibase : `org.liquibase:liquibase-core` + the
  `liquibase-maven-plugin` if you want CLI goals (otherwise the
  starter's auto-run is enough).
- springdoc-openapi : `org.springdoc:springdoc-openapi-starter-webmvc-ui:2.7.0`.
- Plugins : `spring-boot-maven-plugin` (mandatory),
  `maven-compiler-plugin` with `--enable-preview` only if the user
  opts in.

### Phase 3 — Application entry point + minimal endpoint

`{{ArtifactName}}Application.java` :

```java
package {{groupId}};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class {{ArtifactName}}Application {
  public static void main(String[] args) {
    SpringApplication.run({{ArtifactName}}Application.class, args);
  }
}
```

If REST was selected, also add a smoke controller at
`src/main/java/{{groupId-as-path}}/web/HealthController.java` that
exposes `GET /api/health` returning `{"status":"UP"}` — gives the user
a confidence-building first endpoint to curl.

### Phase 4 — `application.yaml`

Bare-minimum content :

```yaml
spring:
  application:
    name: {{artifactId}}
{{#if persistence == jpa-postgres}}
  datasource:
    url: jdbc:postgresql://localhost:5432/{{artifactId}}
    username: {{artifactId}}
    password: {{artifactId}}
  jpa:
    hibernate:
      ddl-auto: validate
  liquibase:
    change-log: classpath:db/changelog/db.changelog-master.yaml
{{/if}}
server:
  port: 8080
management:
  endpoints:
    web:
      exposure:
        include: health, info
```

### Phase 5 — Liquibase scaffold (if enabled)

`src/main/resources/db/changelog/db.changelog-master.yaml` :

```yaml
databaseChangeLog:
  - includeAll:
      path: db/changelog/changes/
      relativeToChangelogFile: false
```

Create an empty `db/changelog/changes/.gitkeep` so the folder ships in
git.

### Phase 6 — `.gitignore` + `README.md`

`.gitignore` : standard Java + Maven + IDE ignores (`target/`, `.idea/`,
`*.iml`, `.vscode/`, `.DS_Store`).

`README.md` : project title from the user, the Maven coordinates, a
one-line "Run with `mvn spring-boot:run`", and a pointer to
`.smith/TECHNICAL_SPECIFICATION.MD` when `/smith-generate-docs` is run.

### Phase 7 — Smoke check

Run `mvn -B -ntp verify` once (via the consumer's `/mvn` skill if the
`mvn` Smith bundle is installed ; otherwise via Bash). Report :
- One-line headline : `mvn verify` ✅ PASS or ❌ FAIL.
- If FAIL : quote the failure section only.

## Quality bar

- Every generated file must be **valid syntactically** and **compile /
  resolve cleanly** in a `mvn -B verify`. If a feature can't be
  fully scaffolded (e.g. database not running locally), generate the
  config but tell the user what to do next — never half-write.
- Maven coordinates use kebab-case `<artifactId>` and dotted
  `<groupId>` derived from the project name + user input.
- Spring Boot 4 baselines (Java 24, Jakarta EE 11, Hibernate 7) ; do
  not pin older versions unless the user explicitly asks.
- Liquibase is the canonical migration tool — never Flyway.
- DDL `auto` stays `validate` in production-shaped configs. `create`
  / `update` are off-limits.

## What you do NOT do

- Don't invent application logic the user didn't ask for. Bootstrap
  produces a runnable empty service ; features come later.
- Don't generate sample CRUD endpoints unless the user explicitly
  asks. The health controller is enough to validate the wiring.
- Don't add lombok / mapstruct / micrometer-prometheus / etc. unless
  the user asks. Bootstrap is a baseline ; extra opinions belong in
  the team's own coding-standards skill.
- Don't auto-commit. The user reviews the tree before deciding what
  goes into the first commit.
- Don't try to start the application (`mvn spring-boot:run`,
  `java -jar`). `mvn verify` is enough to validate the scaffold.

## Reporting back

```
✅ Spring Boot 4 project scaffolded at {{project-root}}.
   Coordinates : {{groupId}}:{{artifactId}}:0.0.1-SNAPSHOT
   Java        : 24
   Persistence : {{choice}}
   Inbound     : {{choice}}
   Liquibase   : {{on|off}}
   OpenAPI     : {{on|off}}
   mvn verify  : ✅ PASS ({{N}} tests run, 0 failures)

Next : run `/smith-generate-docs` to write the functional + technical specs.
```
