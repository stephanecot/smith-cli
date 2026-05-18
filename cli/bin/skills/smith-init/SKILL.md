---
name: smith-init
description: Bootstrap a project for Smith CLI — creates the `.smith/` directory with a single `smith.yaml` marker file (init datetime, AI provider, `enabled: true`). Idempotent — if `.smith/smith.yaml` already exists, it stays untouched. Required marker for every other `/smith-*` skill. Trigger with `/smith-init [--provider claude-code|github-copilot]`. Other Smith config files (architecture.json, config.json, AGENTS.md, …) are owned by other skills and NOT created here.
---

# Skill — `/smith-init`

Bootstraps Smith on the consumer project. **One directory, one file** :

- `.smith/smith.yaml` — minimal init marker. Three fields :
  - `initialized_at` — ISO-8601 UTC timestamp of the init.
  - `provider` — AI tool Smith targets (`claude-code` or `github-copilot`).
  - `enabled` — always `true` at init time. Flip to `false` to disable
    Smith on this project without removing the directory.

That's it. **No architecture.json, no config.json, no AGENTS.md,
no doc generation, no template adaptation.** Those artefacts are owned
by other skills and created on demand.

The exact shape of `.smith/smith.yaml` comes from the template at
`${CLAUDE_SKILL_DIR}/template/smith.template.yaml`. Substitute every
`{{placeholder}}` before writing. Do NOT add or remove top-level keys —
the template is the contract.

## How to invoke

```
/smith-init [--provider claude-code|github-copilot]
```

- `--provider` — optional, defaults to `claude-code`. Selects the AI
  tool Smith targets. Recorded in `smith.yaml`.

No description argument, no `--name` flag. This skill is intentionally
minimal — project identity / stack detection / AI brief are handled by
sibling skills.

## What you do

### Step 1 — Idempotency check

If `.smith/smith.yaml` **already exists**, **do not touch it** — log
`SKIPPED .smith/smith.yaml (already present)` and jump straight to the
report.

### Step 2 — Create `.smith/smith.yaml`

1. Create the `.smith/` directory if missing.
2. Resolve the placeholders :
   - `{{initialized_at_iso8601}}` — current UTC time as
     `YYYY-MM-DDTHH:MM:SSZ`.
   - `{{provider}}` — `--provider` flag value, or `claude-code` by
     default.
3. Read `${CLAUDE_SKILL_DIR}/template/smith.template.yaml`, substitute,
   and atomic-write (tempfile → fsync → rename) to `.smith/smith.yaml`.

### Step 3 — Report back

```
✅ Smith initialised in {{N}}ms.
.smith/smith.yaml : <created|skipped>
provider          : <claude-code|github-copilot>
```

## What you do NOT do

- **Don't** create `architecture.json`, `config.json`, or
  `AGENTS.md`. Those are owned by other skills.
- **Don't** detect the project stack. Stack detection lives elsewhere.
- **Don't** generate any documentation. That's `/smith-generate-docs`.
- **Don't** adapt any template into a skill.
- **Don't** overwrite an existing `.smith/smith.yaml`. Re-running on a
  project that's already initialised is a safe no-op.
- **Don't** dispatch any sub-agent. This skill is filesystem-only.

## Why this skill is minimal

`/smith-init` is the marker that tells every other `/smith-*` skill
"Smith is on for this project". Keeping it to a single tiny YAML file
makes the marker cheap to create, cheap to inspect, and cheap to revoke
(delete `.smith/` and Smith is off). Heavier artefacts — project
identity, stack catalogue, AI brief, spec docs, bundle state — each have
their own skill and run on demand.
