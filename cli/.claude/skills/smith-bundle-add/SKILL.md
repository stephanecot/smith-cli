---
name: smith-bundle-add
description: Scaffolds a NEW bundle under cli/bundles/<name>/ following the canonical layout documented in the sibling skill `smith-bundle-format`. Defaults to scaffolding for **every supported provider** (claude-code + github-copilot) — pass `--ia` only to restrict. Validates every tag against the canonical taxonomy ; regenerates cli/bundles/config.json. Trigger with `/smith-bundle-add <name> "<description>" --tag t1,t2,t3 [--ia claude-code|github-copilot|both]`. CLI-maintainer command (operates on cli/, not on a consumer project).
---

# Skill — `/smith-bundle-add`

Scaffolds a **new** bundle. To modify an existing bundle, use
`/smith-bundle-edit` instead.

The canonical layout, the `@smith-include` factorisation contract, the
`config.yaml` shape, and the tag taxonomy are documented in the sibling
skill **`smith-bundle-format`** — read it first if you don't already
have it in context. This skill only carries the scaffold-new-bundle
procedure.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `<name>` must be kebab-case and not already a sub-folder of
  `cli/bundles/`.
- Each `<tag>` must be in the **canonical taxonomy** documented in
  `smith-bundle-format`.

## How to invoke

```
/smith-bundle-add <name> "<description>" --tag t1,t2,t3 [--ia claude-code|github-copilot|both]
```

Example :

```
/smith-bundle-add lint "ESLint Haiku-offload for the frontend workspace." \
  --tag lint,nodejs,frontend
```

If args are missing or `<tag>` validation fails, ask via
`AskUserQuestion` or stop with the closest suggestion (Levenshtein
distance ≤ 2).

## What you do

1. **Validate inputs.** `<name>` kebab-case + not taken ; every `<tag>`
   in the taxonomy from `smith-bundle-format`. **`--ia` defaults to
   all supported providers** (`claude-code` + `github-copilot`) —
   announce the defaults in your one-line preamble. `--ia <provider>`
   restricts to one ; `--ia both` is a no-op alias.

2. **Ask the user** (via `AskUserQuestion`) which artefacts the bundle
   ships :
   - 0 or more skills (each gets a slug).
   - 0 or more agents (each gets a slug).
   - 0 or more hook fragments (Claude Code) / task fragments (Copilot).
   - 0 or more scripts in `common/scripts/`.
   Default for a brand-new bundle : 1 skill, no agent, no hook, no
   script. The user can extend later via `/smith-bundle-edit`.

3. **Scaffold the folder** `cli/bundles/<name>/` per the canonical
   layout in `smith-bundle-format` :
   - `config.yaml` filled with `name`, `description`, `version: 0.1.0`,
     `tags`, `providers`, and a `files:` map listing every scaffolded
     file (see `smith-bundle-format` for the exact shape).
   - `README.MD` (sections : Why, Installation, Usage, Files, Tags).
   - `RELEASES.MD` (header + initial `0.1.0` entry stub).
   - `common/skills/<slug>.md` per declared skill — body-only markdown,
     scaffold stub instructing the user to fill the body.
   - `common/agents/<slug>.md` per declared agent — body-only markdown
     stub.
   - `common/scripts/<file>` if declared — empty stub.
   - For each provider in scope :
     - `claude-code/skills/<slug>/SKILL.md` — frontmatter (derived from
       `cli/providers/claude-code/rule-skill.MD`) + a body of exactly
       `<!-- @smith-include: ../../../common/skills/<slug>.md -->`.
     - `claude-code/agents/<slug>.md` — frontmatter (derived from
       `rule-agent.MD`) + `<!-- @smith-include: ../../common/agents/<slug>.md -->`.
     - `claude-code/hooks/<n>.hooks.json` for any declared hook.
     - `github-copilot/skills/<slug>/SKILL.md` — frontmatter (derived
       from `cli/providers/github-copilot/rule-skill.MD`) + the same
       `@smith-include` body shape.
     - `github-copilot/agents/<slug>.agent.md` — frontmatter (derived
       from `rule-agent.MD`) + `@smith-include` body.
     - `github-copilot/tasks/<n>.tasks.json` if the Claude Code variant
       ships a hook (Copilot has no in-process hooks ; tasks are the
       substitute).

4. **Regenerate `cli/bundles/config.json`** :
   - Walk every `cli/bundles/*/config.yaml`.
   - Build the new `bundles[]` array, sort by `name` for deterministic
     output.
   - Each entry carries `providers: [...]` reflecting the actual
     scaffolded folders.
   - Atomic write (tempfile → fsync → rename).

5. **Print** the post-add checklist :
   ```
   ✅ Bundle `<name>` scaffolded under cli/bundles/<name>/.
   Tags: <t1>, <t2>, <t3> (all valid).
   Providers: <list>.
   cli/bundles/config.json regenerated ({{N}} bundles total).

   Next steps :
     - Fill the body of cli/bundles/<name>/common/skills/<slug>.md (the canonical body).
     - Fill the body of cli/bundles/<name>/common/agents/<slug>.md if your bundle ships an agent.
     - Tune the per-provider frontmatter under claude-code/ + github-copilot/.
     - Fill cli/bundles/<name>/README.MD (Why + Usage sections).
   ```

## What you do NOT do

- Don't re-document the layout, the `@smith-include` mechanism, the
  config.yaml shape, or the tag taxonomy here. Those live in
  `smith-bundle-format` — keep this skill focused on the
  scaffold-new-bundle procedure.
- Don't extend the tag taxonomy without explicit user buy-in —
  taxonomy changes are a deliberate edit of `smith-bundle-format`.
- Don't install the new bundle anywhere ; that's `/smith-bundle-install`'s
  job.
- Don't modify an EXISTING bundle — that's `/smith-bundle-edit`'s job.
- Don't touch `cli/.claude/` or `cli/templates/`.
- Don't patch `cli/bundles/config.json` line-by-line — always
  regenerate from disk to avoid drift.
