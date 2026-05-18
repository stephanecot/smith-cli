---
kind: rules
provider: claude-code
title: Memory (CLAUDE.md, .claude/rules/<n>.md)
path: CLAUDE.md OR .claude/rules/<n>.md
example: example/example-rules.md
---

# Rules — Claude Code memory (`CLAUDE.md`, `.claude/rules/<n>.md`)

Project-level instructions injected into the assistant's system context on
every session. There is no slash command to invoke them — they are always
on (or scoped by a glob).

## File path & discovery

| File                                    | Scope                       | Loaded |
|-----------------------------------------|-----------------------------|--------|
| `<repo>/CLAUDE.md`                       | Project (everyone)          | Every session in this repo. |
| `<repo>/.claude/rules/<n>.md`            | Project (rule files)        | Every session ; can be glob-scoped via frontmatter `paths:`. |
| `~/.claude/CLAUDE.md`                    | User (personal, all repos)  | Every session, every project. |
| `<plugin>/rules/<n>.md`                  | Plugin                      | When the plugin is enabled. |
| `AGENTS.md`, `GEMINI.md` at repo root    | Cross-tool conventions      | Recognised in compatibility mode by other tools too. |

`.claude/rules/<n>.md` files can carry **frontmatter** ; `CLAUDE.md`
typically does NOT (the convention is plain markdown for the top-level
file).

## Frontmatter — `.claude/rules/<n>.md` only

| Field   | Required | Default | Allowed values            | Meaning |
|---------|----------|---------|---------------------------|---------|
| `paths` | No       | —       | YAML list of glob patterns | Load this rule only when working with files matching the glob. Same syntax as skill `paths:`. |
| `name`  | No       | filename| string                    | Display name in `/doctor` output. |
| `description` | No | —       | string                    | Short description, shown on hover. |

If `paths:` is omitted, the rule loads on every session.

## Body conventions

- Plain markdown. Loaded **verbatim** into the system context.
- Every line costs tokens on every turn — keep it tight.
- Imperative > advisory : "Use camelCase for variables" beats "camelCase
  is preferred".
- Cite paths the assistant can verify (`backend/pom.xml`, not "the build
  file").
- When a rule has a non-obvious reason, add a one-line `Why:` so the
  assistant can generalise to edge cases.
- Order entries from most-broken-when-missed to least.

## Recommended sections for `CLAUDE.md`

```markdown
# {{Project}} — Claude Code rules

## Working agreements
- {{rule}}
- {{rule}}

## Conventions
- Branch naming : {{pattern}}
- Commit subject : {{pattern}}
- {{file path / naming convention}}

## Tools to prefer
- {{situation}} → {{tool}}

## Tools to avoid
- {{tool or pattern}} — {{Why:}}

## Glossary
- {{term}} — {{definition for the assistant}}
```

## Path-scoped rule example (`.claude/rules/angular.md`)

```markdown
---
paths: ["frontend/src/**/*.{ts,html}"]
name: Angular rules
description: Strict Angular 21 patterns — zoneless, signals, OnPush.
---

# Angular rules

- Standalone components only ; no NgModules.
- OnPush change detection is the default ; do not switch off.
- `input.required()` / `input()` / `output()` over `@Input` / `@Output`.
- Signal stores live under `features/<feature>/<feature>.store.ts`.
- All text via Transloco — no hard-coded strings in templates.
```

## CLAUDE.md vs Skill — when to pick which

| Need | Use |
|---|---|
| Standing constraint that applies to every turn | **Rule** |
| Multi-step procedure the user invokes by name | **Skill** |
| Reference material Claude consults only when relevant | **Skill** with informative `description` and `disable-model-invocation: false` |
| Heavy reference (large API docs, examples) | **Skill** with supporting files, not CLAUDE.md (rules cost tokens every turn). |

## Interactions

- Rules cannot be overridden by skills or agents.
- A sub-agent does NOT inherit the parent's `CLAUDE.md` — write the rule
  into the agent's body if it must apply there.
- `--add-dir` does NOT load extra `CLAUDE.md` files by default. Set
  `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD=1` to opt in.
- `InstructionsLoaded` hook fires when a rule loads — useful for audit.

## Skeleton

```markdown
# {{Project name}} — Claude Code rules

## Working agreements
- {{imperative rule}}

## Conventions
- {{convention}}

## Tools to prefer
- {{situation}} → {{tool}}

## Glossary
- {{term}} — {{definition}}
```
