---
name: smith-init
description: Bootstrap a project for Smith CLI — creates the `.smith/` directory with a single `smith.yaml` marker file (init datetime, AI provider, model-tier mapping, `enabled: true`). Idempotent — if `.smith/smith.yaml` already exists, it stays untouched. Required marker for every other `/smith-*` skill. Trigger with `/smith-init [--provider claude-code|github-copilot|opencode]`. Other Smith config files (architecture.json, config.json, AGENTS.md, …) are owned by other skills and NOT created here.
---

# Skill — `/smith-init`

Bootstraps Smith on the consumer project. **One directory, one file** :

- `.smith/smith.yaml` — minimal init marker. Four blocks :
  - `initialized_at` — ISO-8601 UTC timestamp of the init.
  - `provider` — AI tool Smith targets (`claude-code` / `github-copilot`
    / `opencode`).
  - `enabled` — always `true` at init time. Flip to `false` to disable
    Smith on this project without removing the directory.
  - `model_tiers` — a `{small, medium, large}` map of model identifiers
    in the provider's native format. Bundles and templates declare
    `model: small|medium|large`; the install skills replace the tier
    with the matching identifier from this block at write-time. Defaults
    are picked from a built-in table keyed by `provider` (see "Model
    tier defaults" below).

That's it. **No architecture.json, no config.json, no AGENTS.md, no
doc generation, no template adaptation.** Those artefacts are owned
by other skills and created on demand.

The exact shape of `.smith/smith.yaml` comes from the template at
`${CLAUDE_SKILL_DIR}/template/smith.template.yaml`. Substitute every
`{{placeholder}}` before writing. Do NOT add or remove top-level keys —
the template is the contract.

## How to invoke

```
/smith-init [--provider claude-code|github-copilot|opencode]
```

- `--provider` — optional, defaults to `claude-code`. Selects the AI
  tool Smith targets. Recorded in `smith.yaml` AND drives the default
  `model_tiers` block (see table below).

No description argument, no `--name` flag. This skill is intentionally
minimal — project identity / stack detection / AI brief are handled by
sibling skills.

## Model tier defaults

The `model_tiers` block is filled at init time with the **current
best fit** per provider. The maintainer can edit `.smith/smith.yaml`
later to pin a specific snapshot.

| Tier   | claude-code | github-copilot         | opencode                            |
|--------|-------------|------------------------|-------------------------------------|
| small  | `haiku`     | `Claude Haiku 4.5`     | `anthropic/claude-haiku-4-5`        |
| medium | `sonnet`    | `Claude Sonnet 4.5`    | `anthropic/claude-sonnet-4-6`       |
| large  | `opus`      | `Claude Opus 4.7`      | `anthropic/claude-opus-4-7`         |

These defaults intentionally lag behind release announcements until a
new family proves stable — bump them in this skill when the next
generation is ready. The same table is duplicated in
`/smith-bundle-install` and `/smith-template-install` as a fallback
when `.smith/smith.yaml` is missing the tier; both copies MUST stay
in sync.

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
   - `{{model_small}}` / `{{model_medium}}` / `{{model_large}}` — pick
     the row from the "Model tier defaults" table above that matches
     `{{provider}}`. Always quote the value in the output YAML (the
     template already wraps each placeholder in `"…"`) so identifiers
     containing spaces or slashes (e.g. `Claude Haiku 4.5`,
     `anthropic/claude-haiku-4-5`) round-trip cleanly.
3. Read `${CLAUDE_SKILL_DIR}/template/smith.template.yaml`, substitute,
   and atomic-write (tempfile → fsync → rename) to `.smith/smith.yaml`.

### Step 3 — Report back

```
✅ Smith initialised in {{N}}ms.
.smith/smith.yaml : <created|skipped>
provider          : <claude-code|github-copilot|opencode>
model_tiers       : small=<id> medium=<id> large=<id>
```

## What you do NOT do

- **Don't** create `architecture.json`, `config.json`, or
  `AGENTS.md`. Those are owned by other skills.
- **Don't** detect the project stack. Stack detection lives elsewhere.
- **Don't** generate any documentation. That's `/smith-generate-docs`.
- **Don't** adapt any template into a skill.
- **Don't** overwrite an existing `.smith/smith.yaml`. Re-running on a
  project that's already initialised is a safe no-op — even if the
  model defaults in this skill have moved on since the init. The
  maintainer edits `model_tiers` by hand to update.
- **Don't** dispatch any sub-agent. This skill is filesystem-only.

## Why this skill is minimal

`/smith-init` is the marker that tells every other `/smith-*` skill
"Smith is on for this project". Keeping it to a single tiny YAML file
makes the marker cheap to create, cheap to inspect, and cheap to revoke
(delete `.smith/` and Smith is off). Heavier artefacts — project
identity, stack catalogue, AI brief, spec docs, bundle state — each have
their own skill and run on demand.
