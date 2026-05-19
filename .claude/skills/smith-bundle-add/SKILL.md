---
name: smith-bundle-add
description: Scaffolds a NEW bundle under cli/bundles/<name>/ following the canonical layout documented in the sibling skill `smith-bundle-format`. Defaults to scaffolding for **every supported provider** (claude-code + github-copilot) — pass `--ia` only to restrict. Validates every tag against the canonical taxonomy; regenerates cli/bundles/config.json. Trigger with `/smith-bundle-add <name> "<description>" --tag t1,t2,t3 [--ia claude-code|github-copilot|both]`. CLI-maintainer command (operates on cli/, not on a consumer project).
---

# Skill — `/smith-bundle-add`

Scaffolds a **new** bundle. To modify an existing bundle, use
`/smith-bundle-edit` instead.

The canonical layout, the per-skill 4-file shape, the `config.yaml`
shape, and the tag taxonomy are documented in the sibling skill
**`smith-bundle-format`** — read it first if you don't already have it
in context. This skill only carries the scaffold-new-bundle procedure.

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
/smith-bundle-add lint "ESLint runner for the frontend workspace." \
  --tag lint,nodejs,frontend
```

If args are missing or a `<tag>` fails validation, ask via
`AskUserQuestion` or stop with the closest suggestion (Levenshtein
distance ≤ 2).

## What you do

1. **Validate inputs.** `<name>` kebab-case + not taken; every `<tag>`
   in the taxonomy from `smith-bundle-format`. **`--ia` defaults to
   all supported providers** (`claude-code` + `github-copilot`) —
   announce the defaults in your one-line preamble. `--ia <provider>`
   restricts to one; `--ia both` is a no-op alias.

2. **Ask the user** (via `AskUserQuestion`) which artefacts the bundle
   ships :
   - 1 or more skills (each gets a slug). Default : 1 skill named
     `<name>`.
   - 0 or more hook fragments. For each, ask which provider(s) it
     targets — hooks are provider-specific from the start.
   This v0.2 bundle layout does NOT support agents — skills delegate
   to the provider's built-in agents (Agent tool / chat-mode agents)
   inline when needed.

3. **Scaffold the folder** `cli/bundles/<name>/` per the canonical
   layout in `smith-bundle-format` :
   - `config.yaml` with `name`, `description` (passed in), `version:
     0.1.0`, `tags`, `providers` (= the resolved `--ia` set),
     `skills:` (a `{name, version: 0.1.0}` entry per declared skill),
     and `hooks:` (a `{name, version: 0.1.0}` entry per declared
     hook — empty `[]` if no hook; the providers shipping the hook
     are inferred from disk under `hooks/<provider>/`). No `files:`
     map — the structure is self-describing.
   - `README.MD` (sections : Why, Installation, Usage, Tags).
   - `RELEASES.MD` (header + initial `0.1.0` entry stub).
   - For each declared skill `<slug>` :
     - `skills/<slug>/<slug>.md` — body-only markdown stub instructing
       the maintainer to fill in the skill body (no frontmatter).
     - `skills/<slug>/metadata.yml` :
       ```yaml
       name: <slug>
       description: <one-line placeholder — maintainer rewrites>
       ```
       **No `version:`** — the per-skill version lives in
       `config.yaml` `skills[].version`.
     - `skills/<slug>/<provider>.yml` per provider in scope. **Empty
       file** (0 bytes or a single comment-free blank document). The
       maintainer adds provider-specific frontmatter overrides by hand
       when needed.
       **Reminder for the maintainer** : when setting `model:` in a
       `<provider>.yml`, use the abstract tier (`small` / `medium` /
       `large`) — NEVER a concrete model identifier like `haiku` or
       `Claude Sonnet 4.5`. The installer resolves the tier at
       write-time. See `smith-bundle-format`'s "Model tier
       abstraction" section.
   - For each declared hook `<n>` and each provider it targets :
     - `hooks/claude-code/<n>.hooks.json` (Claude Code) with a stub
       fragment for `.claude/settings.json`.
     - `hooks/github-copilot/<n>.tasks.json` (Copilot) with a stub
       VS Code tasks fragment.
     - `hooks/opencode/<n>.ts` (OpenCode) with a stub plugin module.
     - Optional sidecar scripts go next to the fragment in the same
       `hooks/<provider>/` folder.

4. **Regenerate `cli/bundles/config.json`** :
   - Walk every `cli/bundles/*/config.yaml`.
   - Build the new `bundles[]` array : `{name, description,
     directory, version, tags, providers}`. Sort by `name` for
     deterministic output.
   - Atomic write (tempfile → fsync → rename).

5. **Print** the post-add checklist :
   ```
   ✅ Bundle `<name>` scaffolded under cli/bundles/<name>/.
   Tags: <t1>, <t2>, <t3> (all valid).
   Providers: <list>.
   Skills:    <slug1>, <slug2>, ...
   Hooks:     <list>, or "(none)".
   cli/bundles/config.json regenerated ({{N}} bundles total).

   Next steps :
     - Fill the body of cli/bundles/<name>/skills/<slug>/<slug>.md.
     - Refine cli/bundles/<name>/skills/<slug>/metadata.yml (name + description + version).
     - Add provider-specific frontmatter overrides to cli/bundles/<name>/skills/<slug>/<provider>.yml when needed (valid keys = those declared in cli/providers/<provider>/format-skill.yaml).
     - Fill cli/bundles/<name>/README.MD (Why + Usage sections).
   ```

## What you do NOT do

- Don't re-document the layout, the per-skill 4-file shape, the
  config.yaml shape, or the tag taxonomy here. Those live in
  `smith-bundle-format` — keep this skill focused on the
  scaffold-new-bundle procedure.
- Don't extend the tag taxonomy without explicit user buy-in —
  taxonomy changes are a deliberate edit of `smith-bundle-format`.
- Don't ship an `agents/` folder — bundles do not carry their own
  agents in the v0.2 layout. If the user asks for an agent, point
  them at the provider's built-in agents (Agent tool /
  general-purpose / Explore for Claude Code; chat-mode agents for
  Copilot).
- Don't pre-fill `<provider>.yml` with placeholder frontmatter — the
  file MUST start empty so the maintainer's intent (no override) is
  clear. Adding values is a deliberate manual step.
- Don't install the new bundle anywhere; that's
  `/smith-bundle-install`'s job.
- Don't modify an EXISTING bundle — that's `/smith-bundle-edit`'s job.
- Don't touch `cli/.claude/` or `cli/templates/`.
- Don't patch `cli/bundles/config.json` line-by-line — always
  regenerate from disk to avoid drift.
