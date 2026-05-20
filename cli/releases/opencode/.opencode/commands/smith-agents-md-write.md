---
name: smith-agents-md-write
description: Writes (or skips when present) the consumer project's `AGENTS.md` brief from a structured payload — project name, description, stack, provider, installed bundles + skills, optional bootstrap summary. Renders from `template/agents.template.md`, enforces the 100-line cap by truncating optional sections in a documented order, atomic write. Idempotent : if `AGENTS.md` already exists, the skill skips (no overwrite). Trigger with `/smith-agents-md-write --payload <json-or-path>` ; consumed by orchestrators (e.g. `/smith-new-project` via its dedicated sub-agent) rather than end users directly.
---

# Skill — `/smith-agents-md-write`

Produces the project-root `AGENTS.md` brief — the one-page entry point
that Smith-aware AI tools (Claude Code, Copilot) load on every turn.
Caller-agnostic : any orchestrator can hand off a payload and get a
well-formed, length-capped, atomic-written `AGENTS.md` for free.

The skill is **the canonical writer** for this file. Other Smith
skills (`/smith-init`, `/smith-bundle-install`, `/smith-template-install`,
`/smith-new-project`) never touch `AGENTS.md` directly — they invoke
this skill.

## How to invoke

```
/smith-agents-md-write --payload <json-file-or-inline-json>
```

- `--payload` — required. Either a path to a JSON file or a raw JSON
  blob describing the project. Shape documented below.

The skill takes no other flags. Behaviour is fully driven by the
payload + the template at
`${CLAUDE_SKILL_DIR}/template/agents.template.md`.

## Payload contract

```json
{
  "project_name": "<string>",
  "description":  "<verbatim one-liner from the original project description>",
  "summary":      "<optional tech one-liner, e.g. 'Angular 21 + Spring Boot 4'>",
  "stack": {
    "languages":   [{ "name": "<kebab>", "version": "<exact>" }, ...],
    "runtimes":    [...],
    "frameworks":  [...],
    "build_tools": [...],
    "test_tools":  [...],
    "infra_tools": [...],
    "databases":   [...]
  }
}
```

- All top-level keys are required ; arrays inside `stack` may be empty.
- The caller owns the payload — this skill does not re-detect or
  recompute anything from the consumer project.

**`AGENTS.md` is project-focused, not framework-focused.** The
template carries no mention of the tooling that bootstrapped the
project (no `Smith CLI`, no `.smith/` paths, no `/smith-*` commands,
no installed bundles / templates list). Those are infrastructure
concerns that don't belong in the brief an AI assistant reads on
every turn ; they live in the run report and in `.smith/` instead.
For the same reason there is no `provider`, `bundles_installed` or
`skills_installed` key in the payload.

## What you do

### Step 1 — Idempotency check

If `<consumer_project_dir>/AGENTS.md` **already exists**, do **not**
overwrite. Return `status=skipped, reason=already-present, path=AGENTS.md`
and stop. The consumer is treating the file as hand-managed past first
write ; the workflow that called you decides whether to surface this as
a warning.

### Step 2 — Materialise the template

Read `${CLAUDE_SKILL_DIR}/template/agents.template.md` and substitute
every `{{placeholder}}` from the payload :

- `{{project_name}}` ← `payload.project_name`
- `{{description_argument_verbatim}}` ← `payload.description`
- `{{project_summary_one_line}}` ← `payload.summary` (or
  `_unspecified_` if absent)
- `{{languages_inline}}`, `{{runtimes_inline}}`, `{{frameworks_inline}}`,
  `{{build_tools_inline}}`, `{{test_tools_inline}}`,
  `{{infra_tools_inline}}`, `{{databases_inline}}` ← comma-separated
  `name@version` from the corresponding `payload.stack.*` array, or
  `_none_` when empty.

### Step 3 — Enforce the 100-line cap

The rendered file MUST be **≤100 lines**. If it overflows, **truncate
optional sections in this exact order** until the file fits :

1. `- **Infra tools**` line under `## Stack` → drop entirely
2. `- **Test tools**` line under `## Stack` → drop entirely
3. `## Coding conventions` body → keep heading, replace body with
   `_(see framework-specific docs)_`

Never truncate the mission (project name + description), the stack
core (languages / runtimes / frameworks / databases / build tools),
the "How to work in this repo" section, or the "Don't" section.
These are load-bearing for every AI-assisted turn.

### Step 4 — Atomic write

Atomic write (tempfile → fsync → rename) to
`<consumer_project_dir>/AGENTS.md`. Never leave a half-written file —
orchestrators reuse the path in their final user-facing summary.

### Step 5 — Report back

```
✅ AGENTS.md written : {{lines}} lines, {{bytes}} bytes.
```

or

```
⏭ AGENTS.md skipped : already present at the project root.
```

Structured return for callers (orchestrators dispatch you via the
sibling sub-agent `smith-new-project-agents-writer`, which expects
this shape) :

```json
{
  "status":         "created | skipped",
  "reason":         "<short token or null>",
  "path":           "AGENTS.md",
  "lines":          <int or null>,
  "bytes":          <int or null>,
  "truncated":      ["bundles_list", "templates_list", ...]
}
```

## What you do NOT do

- **Don't** mutate any other Smith file. This skill is write-only on
  `AGENTS.md` at the project root.
- **Don't** re-detect the stack, re-read the installed bundles, or
  re-derive anything from `.smith/`. The caller assembles the payload.
- **Don't** overwrite an existing `AGENTS.md`. The user may have hand-
  edited it past the first Smith write — defer to them.
- **Don't** invent placeholders. If the template references a key the
  payload doesn't provide, fail loudly rather than substituting
  `_TBD_` or similar.

## Why a dedicated skill

`AGENTS.md` is loaded on every AI-assisted turn — its format and
length matter. Centralising the rendering + the 100-line cap + the
truncation rules in one skill means every Smith workflow that needs
to emit or refresh this brief gets the same well-formed output, and
the format evolves in a single file (this skill's template).
