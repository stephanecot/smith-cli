---
kind: rules
provider: github-copilot
title: Custom instructions (.github/copilot-instructions.md, .github/instructions/<n>.instructions.md)
path: .github/copilot-instructions.md OR .github/instructions/<n>.instructions.md
example: example/example-rules.instructions.md
---

# Rules — Copilot custom instructions

Copilot reads repo-level guidance from two file kinds :

1. **Repo-wide** — `.github/copilot-instructions.md` (no frontmatter,
   loads on every turn).
2. **Path-scoped** — `.github/instructions/<n>.instructions.md` (with
   YAML frontmatter ; loads only when `applyTo` matches the working file).

## File paths & discovery

| Scope               | Path                                                                 | Loaded |
|---------------------|----------------------------------------------------------------------|--------|
| Repo-wide           | `.github/copilot-instructions.md`                                    | Every Copilot Chat turn in the repo. |
| Path-scoped (repo)  | `.github/instructions/<n>.instructions.md`                           | When `applyTo:` matches the active file. |
| User-level          | `~/.copilot/instructions/<n>.instructions.md` (recursive)            | Every project (personal). |
| Personal (GH.com)   | GitHub.com Copilot Chat settings popup                               | GitHub.com Chat only. |
| Cross-tool          | `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` at repo root                 | Recognised by multiple AI tools in compatibility mode. |

## Frontmatter — repo-wide (`copilot-instructions.md`)

None. Plain markdown.

## Frontmatter — path-scoped (`.github/instructions/<n>.instructions.md`)

| Field         | Required | Default      | Allowed values        | Meaning |
|---------------|----------|--------------|-----------------------|---------|
| `name`        | No       | filename     | string                | Display name in the Chat UI. |
| `description` | No       | —            | string                | Short description shown on hover. |
| `applyTo`     | No       | always-on    | YAML list of globs    | Globs (workspace-relative) that gate when this rule loads. |

### `applyTo` glob syntax

- Workspace-root-relative.
- `**` — every file.
- `**/*.py` — all Python files.
- `**/*.ts,**/*.tsx` — TS + TSX (comma-separated).
- `docs/**/*.md` — markdown under `docs/`.
- Multiple patterns can be listed as a YAML array :
  `applyTo: ["src/**/*.ts", "test/**/*.spec.ts"]`.

## Body conventions

- Plain markdown. Loaded verbatim into Copilot's system context for every
  matching turn.
- Imperative > advisory : "Use camelCase for variables" beats "camelCase
  is recommended".
- Short, self-contained statements. Copilot's context window is smaller
  than Claude Code's — keep it tight.
- Don't duplicate across repo-wide + path-scoped ; Copilot concatenates
  matching instructions.

## Hard limits

- **Copilot code review** reads only the **first 4 000 characters** of
  any custom instruction file. Front-load the critical rules.
- PR reviews use instructions from the base branch, not the head.

## Precedence (top wins)

1. Personal instructions (GitHub.com Chat settings).
2. Path-specific instructions (`.github/instructions/<n>.instructions.md`).
3. Repo-wide (`.github/copilot-instructions.md`).
4. Agent instructions (`AGENTS.md` / `CLAUDE.md` / `GEMINI.md`).
5. Organization-wide.

## Skeleton — repo-wide

```markdown
# {{Project}} — Copilot instructions

## Working agreements
- Use {{language}} {{version}}.
- Run {{test command}} before pushing.

## Conventions
- Branch naming : {{pattern}}
- Commit subject : {{pattern}}

## Tools and scripts
- {{script name}} — {{purpose}}
```

## Skeleton — path-scoped

```markdown
---
name: Backend Java rules
description: Java 24 + Spring Boot 4 patterns enforced on backend code.
applyTo:
  - "backend/**/*.java"
  - "backend/**/pom.xml"
---

# Backend Java rules

- Lombok for boilerplate ; MapStruct for DTO mapping.
- Liquibase YAML changesets only — no Flyway.
- UUID v7 dual-id (internal long + public UUID).
- OpenAPI-first : controllers implement generated interfaces.
```
