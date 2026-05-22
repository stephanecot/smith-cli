---
name: smith-bundle-add
description: Scaffolds a NEW bundle under bundles/<name>/ following the canonical layout documented in the sibling skill `smith-bundle-format`. Defaults to scaffolding for **every supported provider** (claude-code + github-copilot) — pass `--ia` only to restrict. Validates every tag against the canonical taxonomy; regenerates bundles/index.yaml. Pass `--core` to mark the bundle as a base bundle (auto-installed on every project). Trigger with `/smith-bundle-add <name> "<description>" --tag t1,t2,t3 [--ia claude-code|github-copilot|both] [--core]`. CLI-maintainer command (operates on cli/, not on a consumer project).
---

# Skill — `/smith-bundle-add`

Scaffolds a **new** bundle. To modify an existing bundle, use
`/smith-bundle-edit` instead.

The canonical layout, the per-skill 2-file shape, the `config.yaml`
shape, and the tag taxonomy are documented in the sibling skill
**`smith-bundle-format`** — read it first if you don't already have it
in context. This skill only carries the scaffold-new-bundle procedure.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `<name>` must be kebab-case and not already a sub-folder of
  `bundles/`.
- Each `<tag>` must be in the **canonical taxonomy** documented in
  `smith-bundle-format`.

## How to invoke

```
/smith-bundle-add <name> "<description>" --tag t1,t2,t3 [--ia claude-code|github-copilot|both] [--core]
```

`--core` marks the bundle as a **base bundle** : it will be
auto-installed on every consumer project regardless of stack
tags. Default is non-core. See `smith-bundle-format::Core bundles`.

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

3. **Scaffold the folder** `bundles/<name>/` per the canonical
   layout in `smith-bundle-format` :
   - `config.yaml` with `name`, `description` (passed in), `version:
     0.1.0`, `core:` (write `true` only when `--core` was passed ;
     omit otherwise — absent ≡ false), `tags`, `providers` (= the
     resolved `--ia` set), `skills:` (a `{name, version: 0.1.0}`
     entry per declared skill), and `hooks:` (a `{name, version:
     0.1.0}` entry per declared hook — empty `[]` if no hook ; the
     providers shipping the hook are inferred from disk under
     `hooks/<provider>/`). No `files:` map — the structure is
     self-describing.
   - `README.MD` (sections : Why, Installation, Usage, Tags).
   - `RELEASES.MD` (header + initial `0.1.0` entry stub).
   - For each declared skill `<slug>` :
     - `skills/<slug>/<slug>.md` — body-only markdown stub instructing
       the maintainer to fill in the skill body (no frontmatter).
     - `skills/<slug>/metadata.yml` :
       ```yaml
       name: <slug>
       description: <one-line placeholder — maintainer rewrites>
       # Optional generic properties (resolved per provider at build time
       # via provider.yaml::build.skill_property_map) :
       # model: small | medium | large
       # user-invocable: true | false
       ```
       **No `version:`** — the per-skill version lives in
       `config.yaml::skills[].version`. **No per-provider yml** :
       provider-specific frontmatter is composed at build time from
       these generic properties — when `user-invocable` is unsupported
       on a provider (e.g. github-copilot / opencode), the build
       silently drops it.
       **Reminder** : when setting `model:`, use the abstract tier
       (`small` / `medium` / `large`) — never a concrete model
       identifier (`haiku`, `Claude Sonnet 4.5`, …). See
       `smith-bundle-format`'s "Model tier abstraction" section.
   - For each declared hook `<n>` and each provider it targets :
     - `hooks/claude-code/<n>.hooks.json` (Claude Code) with a stub
       fragment for `.claude/settings.json`.
     - `hooks/github-copilot/<n>.tasks.json` (Copilot) with a stub
       VS Code tasks fragment.
     - `hooks/opencode/<n>.ts` (OpenCode) with a stub plugin module.
     - Optional sidecar scripts go next to the fragment in the same
       `hooks/<provider>/` folder.

4. **Regenerate `bundles/index.yaml`** :
   - Walk every `bundles/*/config.yaml`.
   - Build the new `bundles[]` array : `{name, description,
     directory, version, core, tags, providers, skills, hooks}`.
     Include `core` only when the source `config.yaml` carries it
     (absent ≡ false — omit from the index entry too, to keep the
     catalog tidy). Sort by `name` for deterministic output.
   - Atomic write (tempfile → fsync → rename).

5. **Print** the post-add checklist :
   ```
   ✅ Bundle `<name>` scaffolded under bundles/<name>/.
   Tags: <t1>, <t2>, <t3> (all valid).
   Providers: <list>.
   Skills:    <slug1>, <slug2>, ...
   Hooks:     <list>, or "(none)".
   bundles/index.yaml regenerated ({{N}} bundles total).

   Next steps :
     - Fill the body of bundles/<name>/skills/<slug>/<slug>.md.
     - Refine bundles/<name>/skills/<slug>/metadata.yml (name + description ; optional model / user-invocable).
     - Fill bundles/<name>/README.MD (Why + Usage sections).
   ```

## What you do NOT do

- Don't re-document the layout, the per-skill 2-file shape, the
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
- Don't scaffold any `skills/<slug>/<provider>.yml` files — those are
  gone in this layout. Provider-specific frontmatter is composed at
  build time from generic properties in `metadata.yml`.
- Don't install the new bundle anywhere; that's the release-build's
  job.
- Don't modify an EXISTING bundle — that's `/smith-bundle-edit`'s job.
- Don't touch `cli/.claude/` or `templates/`.
- Don't patch `bundles/index.yaml` line-by-line — always
  regenerate from disk to avoid drift.
