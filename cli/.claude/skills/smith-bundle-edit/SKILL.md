---
name: smith-bundle-edit
description: Modify an EXISTING bundle under cli/bundles/<name>/ — add or remove a skill / agent / hook / task / script, bump version, edit description or tags. Respects the canonical layout + `@smith-include` factorisation contract documented in `smith-bundle-format`. Regenerates cli/bundles/config.json after the change. Trigger with `/smith-bundle-edit <name> [--add-skill <slug>] [--add-agent <slug>] [--add-hook <n>] [--add-task <n>] [--add-script <file>] [--rm-skill <slug>] [--rm-agent <slug>] [--rm-hook <n>] [--rm-task <n>] [--rm-script <file>] [--add-tag <t>] [--rm-tag <t>] [--ia claude-code|github-copilot|both] [--bump-version major|minor|patch] [--description "<new>"]`. CLI-maintainer command.
---

# Skill — `/smith-bundle-edit`

Modify an **existing** bundle while preserving the canonical layout
documented in `smith-bundle-format`. To create a new bundle, use
`/smith-bundle-add` instead.

The layout, the `@smith-include` contract, the `config.yaml` shape,
and the tag taxonomy are documented in the sibling skill
**`smith-bundle-format`** — read it first if not already in context.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `<name>` must be an existing sub-folder of `cli/bundles/` with a
  valid `config.yaml`.

## How to invoke

```
/smith-bundle-edit <name> <one-or-more-flags>
```

Supported flags (combinable in a single invocation) :

| Flag | Effect |
|---|---|
| `--add-skill <slug>`     | Create `common/skills/<slug>.md` + per-provider wrappers. |
| `--rm-skill <slug>`      | Delete `common/skills/<slug>.md` + every per-provider wrapper that includes it. |
| `--add-agent <slug>`     | Create `common/agents/<slug>.md` + per-provider wrappers. |
| `--rm-agent <slug>`      | Delete `common/agents/<slug>.md` + every per-provider wrapper. |
| `--add-hook <name>`      | Create `claude-code/hooks/<name>.hooks.json` (Claude Code only). |
| `--rm-hook <name>`       | Delete `claude-code/hooks/<name>.hooks.json`. |
| `--add-task <name>`      | Create `github-copilot/tasks/<name>.tasks.json` (Copilot only). |
| `--rm-task <name>`       | Delete `github-copilot/tasks/<name>.tasks.json`. |
| `--add-script <file>`    | Create `common/scripts/<file>` (byte-identical across providers). |
| `--rm-script <file>`     | Delete `common/scripts/<file>`. |
| `--add-tag <tag>`        | Add a tag (validated against the taxonomy in `smith-bundle-format`). |
| `--rm-tag <tag>`         | Remove a tag. |
| `--ia <provider>`        | Restrict the scope of the change to a single provider (or `both`). Default : every provider listed in the bundle's `providers:`. |
| `--bump-version <kind>`  | Bump `version` in `config.yaml`. `kind` ∈ `major` / `minor` / `patch`. |
| `--description "<new>"`  | Replace the bundle's `description` in `config.yaml`. |

If no flag is given, halt and tell the user what `--add-*` / `--rm-*`
options exist.

## What you do

1. **Validate inputs.**
   - `<name>` exists under `cli/bundles/` and has a valid `config.yaml`.
   - For every `--add-*` flag : the target file MUST NOT exist yet.
   - For every `--rm-*` flag : the target file MUST exist.
   - For tag flags : the tag is in the canonical taxonomy
     (`smith-bundle-format`) ; for `--rm-tag`, the tag is currently
     present.
   - `--ia` restricts the scope of `--add-skill` / `--add-agent` /
     `--rm-skill` / `--rm-agent` etc. — if omitted, apply to every
     provider in the bundle's `providers:` list.

2. **Apply each requested change** (in order, atomic per file) :
   - **Add a skill** :
     - Create `common/skills/<slug>.md` with a body-only stub.
     - For each provider in scope : create the wrapper file
       (`claude-code/skills/<slug>/SKILL.md` or
       `github-copilot/skills/<slug>/SKILL.md`) with the provider's
       frontmatter + a single `<!-- @smith-include: <relative-path> -->`
       body line. Frontmatter comes from `cli/providers/<provider>/rule-skill.MD`.
   - **Remove a skill** :
     - Delete `common/skills/<slug>.md`.
     - Delete every per-provider wrapper that includes it.
     - Refuse if another skill / artefact references the same common
       file (defensive — should not happen, but check).
   - **Add an agent** : same pattern, but `common/agents/<slug>.md`
     and per-provider agent wrappers (`claude-code/agents/<slug>.md` or
     `github-copilot/agents/<slug>.agent.md`).
   - **Remove an agent** : symmetric of add.
   - **Add a hook** : create `claude-code/hooks/<name>.hooks.json` with
     a stub.
   - **Remove a hook** : delete the file.
   - **Add a task** : create `github-copilot/tasks/<name>.tasks.json`
     with a stub.
   - **Remove a task** : delete the file.
   - **Add a script** : create `common/scripts/<file>` with an empty
     stub + executable bit if its extension suggests it (`.sh`, `.js`).
   - **Remove a script** : delete the file.
   - **Add/remove a tag** : update `config.yaml` `tags:` list.
   - **Bump version** : update `version:` in `config.yaml` (semver).
   - **Replace description** : update `description:` in `config.yaml`.

3. **Update `config.yaml`'s `files:` map** to reflect every add/remove
   exactly. Preserve unknown keys.

4. **Update `generated_at`-style timestamps** if present (none in v0.1
   bundle configs, but the rule applies if added later).

5. **Regenerate `cli/bundles/config.json`** :
   - Walk every `cli/bundles/*/config.yaml`.
   - Build the `bundles[]` array, sort by `name`.
   - Atomic write.

6. **Print** the change summary :
   ```
   ✅ Bundle `<name>` updated.
   Added :   <list of added files>
   Removed : <list of removed files>
   Tags :    <new tag list>
   Version : <new version>
   cli/bundles/config.json regenerated.
   ```

## What you do NOT do

- Don't re-document the layout, the `@smith-include` mechanism, the
  config.yaml shape, or the tag taxonomy — they live in
  `smith-bundle-format`.
- Don't create a brand-new bundle ; route the user to
  `/smith-bundle-add` if `<name>` does not exist.
- Don't touch the body of an existing skill / agent / script — that's
  the maintainer's job, by hand. This skill only handles
  add / remove / rename of structural artefacts and metadata fields.
- Don't install the bundle anywhere ; `/smith-bundle-install` does
  that.
- Don't patch `cli/bundles/config.json` line-by-line — always
  regenerate from disk.
- Don't bump version automatically when changing files. The maintainer
  decides when to bump via `--bump-version`.
