---
name: smith-generate-docs
description: Generate the project's two narrative specs under .smith/ — FUNCTIONAL_SPECIFICATION.MD (what the system does) and TECHNICAL_SPECIFICATION.MD (architecture for a senior engineer). Dispatches the two doc-writer agents in parallel ; each fills a macro template from cli/.claude/skills/smith-generate-docs/template/. Idempotent — regenerates the docs on every run, even when they already exist. Does NOT touch project-config.json or smith-config.json. Trigger with `/smith-generate-docs`. Requires /smith-init to have run.
---

# Skill — `/smith-generate-docs`

Owns the narrative documentation pipeline for Smith. Dispatches two
doc-writer agents in parallel — each fills a macro template with content
derived from the project — and writes their outputs to `.smith/`.
Read-only on `.smith/project-config.json` (only consults it for project
name + detected stack) and `.smith/smith-config.json` (only consults
`provider`) ; never writes to either.

## Pre-conditions

- `.smith/project-config.json` AND `.smith/smith-config.json` must both
  exist (markers that `/smith-init` has run). If either is missing,
  halt with one line :
  ```
  /smith-generate-docs requires /smith-init to have run first. Run :
    /smith-init "<one-line description>"
  ```

## How to invoke

```
/smith-generate-docs [--force]
```

- `--force` (optional) — if omitted and the three doc files already
  exist, **ask the user** (`AskUserQuestion`) before regenerating. If
  passed, regenerate without asking. Existing files are always
  **overwritten** — never merged.

## What you do

1. **Read `.smith/project-config.json`** for project name + detected
   stack (languages / runtimes / frameworks / build / test / infra
   tools / databases, each with tags). Read `.smith/smith-config.json`
   for `provider`. Do not write to either file.

2. **Scan the project source** to build a `ProjectSummary` :
   - top-level modules ;
   - entry points (`main` / `bin` / Spring `@SpringBootApplication` /
     CLI scripts) ;
   - signals (`has_tests`, `has_ci`, `has_docker`) ;
   - inbound interfaces (REST controllers, schedulers, webhooks).

3. **Dispatch the two doc-writer agents in parallel** (single message,
   two `Agent` tool calls). Each receives the project info + summary +
   the absolute path of its macro template :

   | Agent | Macro template | Output file |
   |---|---|---|
   | `smith-functional-doc-writer` | `${CLAUDE_SKILL_DIR}/template/functional-spec.template.md` | `.smith/FUNCTIONAL_SPECIFICATION.MD` |
   | `smith-technical-doc-writer`  | `${CLAUDE_SKILL_DIR}/template/technical-spec.template.md`  | `.smith/TECHNICAL_SPECIFICATION.MD`  |

   The **macro template** is a fill-in-the-blank skeleton with
   `{{placeholder}}` markers. Each agent reads its template, computes
   substitutions from the project, replaces every placeholder, strips
   the HTML-comment authoring hints, and writes the result atomically.
   Section headers in the template are fixed — agents never invent or
   remove top-level sections.

   Wait for **both**. If either fails, halt with
   `generate-docs.phase_failed` and surface the error verbatim — do
   NOT keep partial outputs.

4. **Atomic writes** : each agent writes its file via
   tempfile → fsync → rename so a crashed agent never leaves a
   half-written `.MD` on disk.

5. **Report back** :
   ```
   ✅ Docs generated in {{N}}s.
     .smith/FUNCTIONAL_SPECIFICATION.MD ({{nb_lines}} lines)
     .smith/TECHNICAL_SPECIFICATION.MD  ({{nb_lines}} lines)
   ```

## What you do NOT do

- **Don't** touch `.smith/project-config.json` or `.smith/smith-config.json`.
  The doc files are narrative ; the two JSONs hold structured state.
  They live separately.
- **Don't** modify `AGENTS.md`. That's `/smith-init`'s output and the
  user edits it manually after that.
- **Don't** adapt any skill template. The template→skill pipeline was
  removed.
- **Don't** produce a `.smith/TECHNICAL_index.yaml` — the structured
  stack data already lives in `project-config.json`. Don't duplicate.
- **Don't** dispatch the doc-writer agents serially. They were
  designed for parallelism — running them in sequence wastes wall-clock
  time without buying anything.
- **Don't** ask the user to confirm each agent individually. One
  pre-run prompt (when files exist and `--force` was omitted) is enough.

## Idempotency contract

Two runs against the same project with the same input MUST produce
byte-identical outputs (modulo timestamps, if any). The macro templates
guarantee stable section ordering ; agents are responsible for
deterministic phrasing within each section.

## Why this skill is separate from `/smith-init`

Doc regeneration is a recurring operation : as the project evolves
(new dependencies, refactors, renames), the specs need to be re-written.
Coupling it to bootstrap would make every regeneration require either
a re-init (clobbering `config.json`) or a complex idempotency dance.
Keeping them separate means : `/smith-init` runs once, `/smith-generate-docs`
runs whenever the project's narrative needs refreshing.
