---
name: smith-provider-add
description: Scaffolds a NEW AI provider folder under cli/providers/<slug>/ from the JSON Schemas at cli/providers/specs/. Produces a schema-valid provider.yaml + format-skill.yaml + format-agent.yaml + format-hook.yaml + 3 example placeholder files. Validates every generated file against its schema before reporting success. Trigger with `/smith-provider-add <slug> "<one-line description>"`. CLI-maintainer command.
---

# Skill — `/smith-provider-add`

Scaffolds a **new** AI provider (e.g. `gemini-cli`, `opencode`). To
modify an existing provider, use `/smith-provider-edit` instead.

The canonical layout, the JSON Schemas under `cli/providers/specs/`,
and the cross-reference rules between format files and examples are
documented in the sibling skill **`smith-provider-format`** — read it
first if not already in context. This skill only carries the
schema-driven scaffold-new procedure.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `<slug>` must be kebab-case and not already exist under
  `cli/providers/`.
- All 4 schemas under `cli/providers/specs/` must exist and be valid
  JSON Schema 2020-12.

## How to invoke

```
/smith-provider-add <slug> "<one-line description>"
```

Example :

```
/smith-provider-add gemini-cli "Google Gemini CLI provider — supports prompts, hooks via shell commands, no first-class sub-agent dispatch."
```

If args are missing, ask via `AskUserQuestion`.

## What you do

1. **Validate `<slug>`** — kebab-case (regex `^[a-z0-9-]+$`), no
   slashes, not already a sub-folder of `cli/providers/`.

2. **Load the 4 schemas** from `cli/providers/specs/` :
   - `provider.schema.json`
   - `format-agent.schema.json`
   - `format-skill.schema.json`
   - `format-hook.schema.json`
   These define the **required keys, types, patterns, and enums** for
   every YAML the skill is about to produce.

3. **Create the folder** `cli/providers/<slug>/` and its
   `example/` sub-folder.

4. **Scaffold `provider.yaml`** by emitting every required key from
   `provider.schema.json` with realistic placeholder values. Required
   (per the schema) :
   - `slug: <slug>`
   - `name: "<slug>"` (or a humanised form)
   - `description: <one-line passed in>`
   - `docs:` — at least one placeholder URL the maintainer rewrites
   - `kinds:` — `agent` / `skill` / `hook` entries (REQUIRED) pointing
     at the matching `format-*.yaml` + placeholder `consumer_path:`,
     `invocation:`, `example:` (the example path must match the
     `^example/example-<kind>[^/]*\.[^/]+$` pattern). Optionally add a
     `rules` entry (just `consumer_path` + `invocation`) when the
     provider has a rules / instructions surface (`CLAUDE.md`,
     `AGENTS.md`, etc.).
   - `build:` — **REQUIRED build-side configuration consumed by
     `/smith-build`.** Carries everything provider-specific the build
     script needs ; no business logic lives in `build.py`. Emit all
     of :
     - `consumer_paths.skill` — install template using `{slug}`
       (e.g. `.claude/skills/{slug}/SKILL.md` or
       `.github/prompts/{slug}.prompt.md`).
     - `consumer_paths.agent` — same shape for sub-agents.
     - `consumer_paths.hook_dir` — directory template using
       `{bundle}` (where bundle hook files land).
     - `consumer_paths.settings` — consumer settings file used for
       hook-fragment merges, OR `~` (null) when the provider has no
       merge model (e.g. opencode).
     - `agent_frontmatter.emit_name` — `true` to emit `name:` in
       agent frontmatter, `false` when filename carries the slug.
     - `agent_frontmatter.extra` — constant frontmatter keys to
       inject (e.g. `{ mode: subagent }` for opencode ; `{}` when
       nothing extra).
     - `tools_style` — one of `claude-string` (comma-separated
       `tools:`), `yaml-list` (`tools: [...]`), or
       `opencode-permission` (`permission: { name: allow }`).
     - `capability_map` — generic capability slug → native tool name
       for every value in : `read, glob, grep, bash, edit, write,
       skill, agent, ask-user, web-fetch`. Set the value to `~`
       (null) when a capability has no equivalent on this provider —
       the build silently drops it from the resolved list.

   Do NOT include optional sections (`discovery`,
   `cross_kind_interactions`, `naming_conventions`, `when_to_pick`,
   `gaps_vs_claude_code`, `smith_mapping`) unless the maintainer asks
   — keep the file minimal. They can be added later via
   `/smith-provider-edit --edit-provider`. No YAML comments.

5. **Scaffold each `format-<kind>.yaml`** by emitting every required
   key from the matching `format-<kind>.schema.json` with placeholder
   values :
   - Header keys (`kind` set to the correct const, `provider: <slug>`,
     `title`, `consumer_path`, `example`).
   - `frontmatter:` — list with at least one placeholder field entry
     containing all 5 required sub-keys (`field`, `required`,
     `default`, `allowed`, `meaning`).
   - `body_conventions:` — at least one bullet.
   - For `format-agent.yaml` — also `builtin_tools:` (at least one
     placeholder entry).
   - For `format-hook.yaml` — also `events:` (at least one entry with
     `name` / `fires` / `can_block`), `handler_types:` (at least one
     entry with `type` / `fields`), `conventions:` (at least one
     bullet).

6. **Scaffold the 3 companion example files** under `<slug>/example/`
   with placeholder content the maintainer rewrites :
   - `example/example-agent.<ext>`
   - `example/example-skill.<ext>`
   - `example/example-hook.<ext>`
   Pick a sensible `<ext>` (e.g. `.md` for prompt-based providers,
   `.json` for hooks). The example path declared in the YAMLs MUST
   match these filenames.

7. **Validate every produced YAML against its schema** (use
   `python3 -m jsonschema -i <file>.yaml <schema>.json` after
   yaml→json conversion, or any equivalent JSON Schema validator).
   If ANY file fails validation, halt immediately, delete the
   `<slug>/` folder, and surface the validator errors. Never report
   success on partially-valid scaffold.

8. **Tell the user** the 4 YAML files + 3 examples are
   schema-compliant **placeholders** — they must be rewritten by hand
   to match the new provider's syntax. This skill does NOT
   auto-translate; the schemas only guarantee structural validity.

## What you do NOT do

- Don't re-document the provider folder layout, the schema contract,
  or the example cross-reference rules — those live in
  `smith-provider-format` + the 4 `.json` schemas under
  `cli/providers/specs/`. Keep this skill focused on the
  schema-driven scaffold procedure.
- Don't copy from `cli/providers/claude-code/` blindly. The schemas
  are the source of truth for what to emit; claude-code is just one
  valid instance of the contract.
- Don't translate the format bodies automatically — adapting them to
  a new provider's API is a manual job that requires reading that
  provider's documentation.
- Don't touch `cli/.claude/`, `cli/templates/`, or `cli/bundles/`.
- Don't register the new provider in any global index ; providers
  are discovered by directory walking under `cli/providers/`. No
  catalogue file exists at the provider level.
- Don't write any `rule-*.MD` or `RULES.MD` file — the old 5-`.MD`
  layout is gone. The canonical surface is 4 YAML files + 4 JSON
  Schemas.
- Don't add a 4th `format-*.yaml` — the 3 kinds (agent / skill / hook)
  are hardcoded in `provider.schema.json` via the `kinds` `required`
  list. Extra concepts live inline in `provider.yaml`.
- Don't add YAML comments inside any of the 4 YAML files.
- Don't modify an EXISTING provider — that's `/smith-provider-edit`'s
  job.

## Reporting back

```
✅ Provider `<slug>` scaffolded under cli/providers/<slug>/.
   provider.yaml + 3 format-*.yaml + 3 examples produced from the
   JSON Schemas at cli/providers/specs/. All 4 YAMLs validated.

Next steps :
  - Rewrite `<slug>/format-agent.yaml` to match the provider's sub-agent format (re-validate against format-agent.schema.json).
  - Rewrite `<slug>/format-skill.yaml` to match its slash-command / skill format.
  - Rewrite `<slug>/format-hook.yaml` (or describe host-driven mechanisms if the provider has no in-process hooks).
  - Rewrite the 3 `<slug>/example/example-*` files with provider-idiomatic content.
  - **Fill `<slug>/provider.yaml::build`** : real `consumer_paths`, `agent_frontmatter`, `tools_style`, and the per-capability native tool names in `capability_map`. `/smith-build` reads ONLY this section — no fallbacks in the build script.
  - Enrich `<slug>/provider.yaml` (docs URLs, discovery scopes, cross_kind_interactions, when_to_pick).
```

## Validation failure mode

```
❌ Provider `<slug>` NOT scaffolded — schema validation failed.
   Files that failed :
     - <path> : <validator error>
     - <path> : <validator error>
   Folder removed; nothing left on disk. Re-run the skill or fix the
   schemas under cli/providers/specs/ if the contract itself is wrong.
```
