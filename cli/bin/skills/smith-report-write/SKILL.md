---
name: smith-report-write
description: Writes a markdown run report for any Smith workflow into `.smith/report/<NNN>-<slug>.md`. Auto-increments the numeric prefix by scanning the existing report directory. Atomic write, idempotent on the numbering scheme — same `<slug>` re-run always gets a fresh `<NNN>`. Trigger with `/smith-report-write --slug <slug> --payload <json-or-path>` ; consumed by orchestrators (e.g. `/smith-new-project`) rather than end users directly.
---

# Skill — `/smith-report-write`

Persists a run report under `.smith/report/` from a structured payload.
Caller-agnostic — any orchestrator skill can hand off its trace log.

The numbering scheme is `NNN-<slug>.md` where `NNN` is a 3-digit
zero-padded counter unique to the `.smith/report/` directory. New
reports always get the next available `NNN`, so re-running the same
workflow never overwrites an earlier report — the directory is an
append-only audit trail.

## How to invoke

```
/smith-report-write --slug <slug> --payload <json-file-or-inline-json>
```

- `--slug` — required. Kebab-case identifier of the workflow (e.g.
  `new-project`, `convert-project`, `bundle-install`). Lands in the
  filename and the report's heading.
- `--payload` — required. Either a path to a JSON file or a raw JSON
  blob describing the run. Shape is workflow-specific ; the only
  required top-level keys are documented below.

The report contents come entirely from the payload + the template at
`${CLAUDE_SKILL_DIR}/template/report.template.md` — this skill does not
re-detect or recompute anything.

## Payload contract

```json
{
  "workflow":     "smith-new-project",
  "started_at":   "<ISO-8601 UTC>",
  "ended_at":     "<ISO-8601 UTC>",
  "duration_ms":  12345,
  "arguments":    { "<flag>": "<value>", ... },
  "steps":        [
    { "n": 1, "name": "smith-init", "status": "ok|skipped|failed",
      "duration_ms": 42, "summary": "<one-liner>", "details": "<optional md>" }
  ],
  "artefacts":    {
    "created":    ["<path>", ...],
    "skipped":    ["<path>", ...],
    "updated":    ["<path>", ...]
  },
  "verifier":     {
    "passed":     N,
    "failed":     N,
    "warned":     N,
    "checks":     [{ "name": "<check>", "status": "pass|fail|warn",
                     "detail": "<one-liner>" }]
  },
  "next_steps":   ["<command or note>", ...],
  "warnings":     ["<text>", ...]
}
```

All top-level keys are required ; arrays may be empty. Caller must
ensure the payload is consistent — this skill writes whatever it gets.

## What you do

### Step 1 — Resolve the report path

1. Ensure `.smith/report/` exists (create it if missing).
2. List files matching `[0-9][0-9][0-9]-*.md` in that directory.
3. Find the largest `NNN` already used. The new report's number is
   `max + 1`, zero-padded to 3 digits. If the directory is empty,
   start at `001`.
4. Final filename : `.smith/report/<NNN>-<slug>.md`. If by chance
   that path already exists (race condition or manual file), bump
   `NNN` again until the path is free.

### Step 2 — Materialise the template

Read `${CLAUDE_SKILL_DIR}/template/report.template.md` and substitute
every `{{placeholder}}` from the payload :

- `{{workflow}}`, `{{slug}}`, `{{nnn}}`
- `{{started_at}}`, `{{ended_at}}`, `{{duration_ms}}`,
  `{{duration_human}}` (e.g. `12.345s`)
- `{{arguments_table}}` — markdown table built from `arguments`.
- `{{steps_table}}` — markdown table over `steps[]`
  (`n | name | status | duration | summary`).
- `{{step_details}}` — concatenation of every step's `details` (when
  non-empty), each prefixed by a `### <name>` heading. Omit the
  section entirely if no step has details.
- `{{artefacts_created}}`, `{{artefacts_skipped}}`, `{{artefacts_updated}}`
  — bullet lists. Render `_None_` when empty.
- `{{verifier_summary}}` — `{{passed}} pass · {{failed}} fail · {{warned}} warn`.
- `{{verifier_table}}` — markdown table over `verifier.checks[]`.
- `{{next_steps_list}}` — bullet list. Render `_None_` when empty.
- `{{warnings_list}}` — bullet list. Render `_None_` when empty.

Use `_None_` (not an empty bullet) for empty lists, so the rendered
report reads naturally.

### Step 3 — Atomic write

Atomic write (tempfile → fsync → rename) to the resolved path. Never
leave a half-written report — orchestrators reuse the file path in
their final user-facing summary.

### Step 4 — Report back

```
✅ Report written : .smith/report/<NNN>-<slug>.md  ({{bytes}} bytes)
```

## What you do NOT do

- **Don't** mutate `.smith/config.json` or any other Smith file.
  This skill is write-only on its own report path.
- **Don't** infer or recompute steps / verifier results. Garbage in,
  garbage out — the caller owns the payload.
- **Don't** delete or rewrite older reports. The directory is
  append-only.
- **Don't** trim the payload — even verbose `details` should be
  preserved verbatim in the rendered markdown.

## Why a dedicated skill

Run reports follow a stable shape across every Smith workflow
(`/smith-new-project`, future `/smith-convert-project`, etc.). Keeping
the templating + numbering in one place means every orchestrator can
hand off a payload and get an audit-quality report for free, and the
report format evolves in a single file (this skill's template).
