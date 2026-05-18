---
name: smith-report-write
description: Writes the **single** markdown run report for the project at `.smith/report.md` (fixed path, overwritten on every run). Caller-agnostic ; consumed by orchestrators (e.g. `/smith-new-project`) rather than end users. Trigger with `/smith-report-write --payload <json-or-path>`. There is no per-run numbering — the latest workflow run replaces the previous report.
---

# Skill — `/smith-report-write`

Persists **the** run report at `.smith/report.md` from a structured
payload. Caller-agnostic — any orchestrator skill can hand off its
trace log.

**Single-file policy** : there is exactly one report per project. The
file lives at the fixed path `.smith/report.md` and is overwritten on
every workflow run. No numeric prefix, no per-workflow slug suffix —
the latest run is the only one that matters. Older runs are not
preserved ; check git history if you need to compare runs.

## How to invoke

```
/smith-report-write --payload <json-file-or-inline-json>
```

- `--payload` — required. Either a path to a JSON file or a raw JSON
  blob describing the run. Shape is workflow-specific ; the only
  required top-level keys are documented below. The workflow name is
  read from `payload.workflow` and used in the report's heading only
  (not in the filename — the filename is always `.smith/report.md`).

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
  }
}
```

All top-level keys are required ; arrays may be empty. Caller must
ensure the payload is consistent — this skill writes whatever it gets.

`steps[].duration_ms` is **required for every step** — the rendered
table surfaces it so the user can see where time was spent. If the
caller did not measure a step (e.g. early-skip), pass `0` rather than
omitting the key.

**No `warnings` / `next_steps` keys** : the report is a factual run
record. Open issues belong in `steps[].details` (per-step,
contextual) ; suggested follow-ups belong in the orchestrator's
final user-facing summary (which is NOT this report's job).

## What you do

### Step 1 — Resolve the report path

The path is fixed : `<consumer_project_dir>/.smith/report.md`. Ensure
the `.smith/` directory exists (it must — `/smith-init` created it ;
otherwise refuse the operation with `smith-not-initialised`).

If `.smith/report.md` already exists, **overwrite it** on this run
(no refusal, no numeric backup). The previous report is gone — that
is the explicit contract.

### Step 2 — Materialise the template

Read `${CLAUDE_SKILL_DIR}/template/report.template.md` and substitute
every `{{placeholder}}` from the payload :

- `{{workflow}}` ← `payload.workflow`
- `{{started_at}}`, `{{ended_at}}`, `{{duration_ms}}`,
  `{{duration_human}}` (e.g. `12.345s`)
- `{{arguments_table}}` — markdown table built from `arguments`.
- `{{steps_table}}` — markdown table over `steps[]`. **Required
  columns, in this exact order :**
  `# | Step | Status | Duration | Summary`. The Duration column is
  not optional — render `{{step.duration_ms}} ms` (or
  `{{duration_human}}` when ≥1 s) so the reader can see per-step
  timing at a glance.
- `{{step_details}}` — concatenation of every step's `details` (when
  non-empty), each prefixed by a `### <step name>` heading. Omit the
  section entirely if no step has details.
- `{{artefacts_created}}`, `{{artefacts_skipped}}`, `{{artefacts_updated}}`
  — bullet lists. Render `_None_` when empty.
- `{{verifier_summary}}` — `{{passed}} pass · {{failed}} fail · {{warned}} warn`.
- `{{verifier_table}}` — markdown table over `verifier.checks[]`.

Use `_None_` (not an empty bullet) for empty lists, so the rendered
report reads naturally. The template carries no `## Warnings` /
`## Next steps` / `## Known issues` sections — do not invent them.

### Step 3 — Atomic write

Atomic write (tempfile → fsync → rename) to the resolved path. Never
leave a half-written report — orchestrators reuse the file path in
their final user-facing summary.

### Step 4 — Report back

```
✅ Report written : .smith/report.md  ({{bytes}} bytes)
```

## What you do NOT do

- **Don't** mutate `.smith/config.json` or any other Smith file.
  This skill is write-only on its own report path (`.smith/report.md`).
- **Don't** infer or recompute steps / verifier results. Garbage in,
  garbage out — the caller owns the payload.
- **Don't** create per-run numbered backups
  (`.smith/report.001.md` etc.). The contract is one file, latest run
  wins — historical snapshots are git's job.
- **Don't** trim the payload — even verbose `details` should be
  preserved verbatim in the rendered markdown.

## Why a dedicated skill

Run reports follow a stable shape across every Smith workflow
(`/smith-new-project`, future `/smith-convert-project`, etc.). Keeping
the templating + numbering in one place means every orchestrator can
hand off a payload and get an audit-quality report for free, and the
report format evolves in a single file (this skill's template).
