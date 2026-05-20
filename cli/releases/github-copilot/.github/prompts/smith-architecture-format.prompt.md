---
name: smith-architecture-format
description: Source of truth for the format of `.smith/architecture.json` — the project identity file (name + description + summary + detected stack with kebab-case tags). Documents every field, its type, allowed values, defaults, and who is allowed to write it. Ships the canonical macro template under `templates/architecture.template.json`. Auto-load whenever the user asks how `architecture.json` is laid out, what a stack field means, what the tag taxonomy is, or who writes / re-writes it. Sister skill `smith-config-format` covers the OTHER file (`.smith/config.json`, the Smith state file) — keep the scope separate.
when_to_use: User asks about `.smith/architecture.json`, the project identity file, the detected stack arrays (`languages` / `runtimes` / `frameworks` / `build_tools` / `test_tools` / `infra_tools` / `databases`), or the kebab-case tag taxonomy. Also fires when a skill needs to compose or re-detect the project descriptor.
user-invocable: false
---

# `.smith/architecture.json` — format reference

This skill is the **single source of truth** for `.smith/architecture.json`,
the project identity file Smith writes once per consumer project. Every
field, type, default and ownership rule is documented below. The macro
template under `templates/architecture.template.json` is the canonical
fill-in-the-blank skeleton that `/smith-init` reads to produce the file.

The sister skill `smith-config-format` covers the OTHER managed file
(`.smith/config.json` — the Smith state file). Their scopes never
overlap : one file describes what the project IS, the other describes
what Smith has DONE to it.

`AGENTS.md` at the project root is **out of scope** here — it is owned
by `/smith-init` and never re-written by other Smith skills.

## File summary

| Field | Value |
|---|---|
| Path                  | `.smith/architecture.json` |
| Purpose               | What the project IS — name + description + detected stack with `tags[]`. |
| Template              | `templates/architecture.template.json` |
| Created by            | `/smith-init` (idempotent — if file exists, do not touch). |
| Re-written by         | Nobody. To re-detect the stack, delete the file and re-run `/smith-init`. |
| Read by               | `/smith-dashboard`, `/smith-template-install`, `/smith-generate-docs`. |

## Top-level keys

| Key | Type | Required | Meaning |
|---|---|:---:|---|
| `version`      | number                | yes | Schema version. `1` today. Bump only on incompatible shape changes. |
| `generated_at` | string (ISO-8601 UTC) | yes | Write timestamp. |
| `project`      | object                | yes | The full project descriptor. |

## `project.*` keys

| Key | Type | Required | Meaning |
|---|---|:---:|---|
| `name`        | string         | yes | Project name. Inferred from `package.json` / `pom.xml` / dir name, or overridden via `--name`. |
| `description` | string         | yes | Verbatim copy of the `<description>` arg passed to `/smith-init`. |
| `summary`     | string         | no  | Optional one-line tech summary (e.g. `"Angular 21 + Spring Boot 4"`). |
| `languages`   | array          | yes | Detected languages with tags. Empty array `[]` if none confidently detected. |
| `runtimes`    | array          | yes | Detected runtimes (`nodejs`, `jvm`, `python3`, `dotnet`, …). |
| `frameworks`  | array          | yes | **Main** frameworks only. Fine-grained libs (`rxjs`, `lombok`, JDBC drivers, …) deliberately omitted. |
| `build_tools` | array          | yes | Build / packaging tools (`maven`, `npm`, `gradle`, `vite`, `pip`, …). |
| `test_tools`  | array          | yes | Test frameworks + runners (`vitest`, `junit`, `pytest`, `playwright`, `testcontainers`, …). |
| `infra_tools` | array          | yes | Container / IaC / CI tools (`docker`, `docker-compose`, `terraform`, `github-actions`, …). |
| `databases`   | array          | yes | Persistence engines (`postgresql`, `mysql`, `mongodb`, `redis`, …). |
| `git_sha`     | string \| null | yes | `HEAD` sha when the project is a git working tree, `null` otherwise. |

## Entry shape (every stack array element)

```json
{ "name": "<kebab-case>", "version": "<exact resolved version>", "tags": ["<keyword>"] }
```

`tags[]` MUST use kebab-case keywords drawn from the canonical taxonomy
maintained by `/smith-bundle-add` (role / language / runtime / tier /
provider / integration). Example : Spring Boot →
`["java", "backend", "rest", "jpa"]`.

## Mutator contract

Any Smith skill that writes `.smith/architecture.json` MUST :

1. **Read the canonical template** from
   `templates/architecture.template.json` first to know the full shape
   — even when re-detecting one section. Missing keys must not be
   dropped.
2. **Atomic write** : write to `<file>.tmp`, fsync, then `mv` over the
   final path. Never leave a half-written JSON.
3. **Preserve unknown keys** : if a future Smith version adds a key the
   current code doesn't understand, the mutator must round-trip it
   unchanged.
4. **Update `generated_at`** on every successful write.

Today the only writer is `/smith-init`. Every other Smith skill treats
`architecture.json` as read-only.

## Skills that read this skill

| Skill | What it does with `architecture.json` |
|---|---|
| `/smith-init`             | Reads `templates/architecture.template.json`, fills the placeholders from stack detection, atomic-writes the file. The ONLY writer. |
| `/smith-template-install` | Reads `project.frameworks[]` to pick the right framework template set (`angular/21`, `java-spring-boot/4`, …). Read-only. |
| `/smith-generate-docs`    | Reads the descriptor to seed the technical / functional specifications. Read-only. |
| `/smith-dashboard`        | Reads it to render the «Project» card of the HTML dashboard. Read-only. |
