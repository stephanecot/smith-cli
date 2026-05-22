---
name: smith-bundle-edit
description: Modify an EXISTING bundle under bundles/<name>/ — add or remove a skill, add or remove a hook, add or remove a sidecar script, bump the bundle / per-skill / per-hook version, edit description or tags. Respects the canonical layout documented in `smith-bundle-format`. Regenerates bundles/index.yaml after the change. Trigger with `/smith-bundle-edit <name> [--add-skill <slug>] [--rm-skill <slug>] [--add-hook <n> --ia <provider>] [--rm-hook <n> --ia <provider>] [--add-script <file> --ia <provider>] [--rm-script <file> --ia <provider>] [--add-tag <t>] [--rm-tag <t>] [--add-provider <p>] [--rm-provider <p>] [--bump-version major|minor|patch] [--bump-skill <slug> major|minor|patch] [--bump-hook <n> major|minor|patch] [--description "<new>"]`. CLI-maintainer command.
---

# Skill — `/smith-bundle-edit`

Modify an **existing** bundle while preserving the canonical layout
documented in `smith-bundle-format`. To create a new bundle, use
`/smith-bundle-add` instead.

The layout, the per-skill 2-file shape, the `config.yaml` shape, and
the tag taxonomy are documented in the sibling skill
**`smith-bundle-format`** — read it first if not already in context.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `<name>` must be an existing sub-folder of `bundles/` with a
  valid `config.yaml`.

## How to invoke

```
/smith-bundle-edit <name> <one-or-more-flags>
```

Supported flags (combinable in a single invocation) :

| Flag | Effect |
|---|---|
| `--add-skill <slug>`                | Create `skills/<slug>/` with the 2 canonical files (`<slug>.md` body stub + `metadata.yml`). |
| `--rm-skill <slug>`                 | Delete `skills/<slug>/` entirely (body + metadata). |
| `--add-hook <n> --ia <provider>`    | Create `hooks/<provider>/<n>.<ext>` with a stub fragment. `<ext>` = `hooks.json` for `claude-code`, `tasks.json` for `github-copilot`. `--ia` is REQUIRED — hooks are always provider-specific. |
| `--rm-hook <n> --ia <provider>`     | Delete `hooks/<provider>/<n>.<ext>`. |
| `--add-script <file> --ia <provider>` | Create `hooks/<provider>/<file>` with an empty stub + executable bit if its extension suggests it (`.sh`, `.js`, `.py`). |
| `--rm-script <file> --ia <provider>` | Delete `hooks/<provider>/<file>`. |
| `--add-tag <tag>`                   | Add a tag (validated against the taxonomy in `smith-bundle-format`). |
| `--rm-tag <tag>`                    | Remove a tag. |
| `--add-provider <p>`                | Add `<p>` to `config.yaml` `providers:` AND create the matching `<p>.yml` (empty) under every existing `skills/<slug>/`. |
| `--rm-provider <p>`                 | Remove `<p>` from `providers:` AND delete every `skills/<slug>/<p>.yml` + `hooks/<p>/` folder. |
| `--bump-version <kind>`             | Bump bundle-level `version:` in `config.yaml`. `kind` ∈ `major` / `minor` / `patch`. |
| `--bump-skill <slug> <kind>`        | Bump `config.yaml` `skills[name=<slug>].version`. `<slug>` MUST be in `skills[]`. |
| `--bump-hook <n> <kind>`            | Bump `config.yaml` `hooks[name=<n>].version`. `<n>` MUST be in `hooks[]`. |
| `--description "<new>"`             | Replace `description:` in `config.yaml`. |

If no flag is given, halt and tell the user what `--add-*` / `--rm-*`
options exist.

## What you do

1. **Validate inputs.**
   - `<name>` exists under `bundles/` and has a valid `config.yaml`.
   - For every `--add-*` flag : the target file / directory MUST NOT
     exist yet.
   - For every `--rm-*` flag : the target file / directory MUST exist.
   - For `--add-hook` / `--rm-hook` / `--add-script` / `--rm-script` :
     `--ia <provider>` is REQUIRED and MUST be one of the bundle's
     `providers:`.
   - For tag flags : the tag is in the canonical taxonomy
     (`smith-bundle-format`); for `--rm-tag`, the tag is currently
     present.
   - For `--add-provider` / `--rm-provider` : `<p>` MUST be a known
     Smith provider (a folder under `providers/`).

2. **Apply each requested change** (in order, atomic per file) :
   - **Add a skill** :
     - Create `skills/<slug>/<slug>.md` with a body-only stub.
     - Create `skills/<slug>/metadata.yml` :
       ```yaml
       name: <slug>
       description: <one-line placeholder — maintainer rewrites>
       ```
       (No `version:` — that field lives in `config.yaml`
       `skills[].version`.)
     - For each provider in `config.yaml` `providers:`, create
       `skills/<slug>/<provider>.yml` as an empty file.
     - Append `{name: <slug>, version: 0.1.0}` to `config.yaml`
       `skills[]`.
   - **Remove a skill** :
     - Delete `skills/<slug>/` recursively.
     - Drop the matching entry from `config.yaml` `skills[]`.
     - Refuse if any hook fragment under `hooks/<provider>/`
       references it by name (defensive).
   - **Add a hook** : create `hooks/<provider>/<n>.<ext>` with a
     stub. For `claude-code` :
     ```json
     { "hooks": { "PostToolUse": [] } }
     ```
     For `github-copilot` :
     ```json
     { "version": "2.0.0", "tasks": [] }
     ```
     For `opencode` : a TypeScript plugin stub exporting an
     `async function ({ project }) { return { /* event handlers */ } }`.

     Then ensure `config.yaml` `hooks[]` has an entry
     `{name: <n>, version: 0.1.0}` — append it if missing. The set of
     providers shipping this hook is inferred from disk
     (`hooks/<provider>/<n>.<ext>`), so the entry has no
     `providers:` sub-field.
   - **Remove a hook** : delete `hooks/<provider>/<n>.<ext>`. After
     the delete, walk every `hooks/<other-provider>/` to see if
     `<n>.<ext>` still exists somewhere. If no provider folder still
     ships the hook, drop the matching entry from `config.yaml`
     `hooks[]`. Otherwise leave the `hooks[]` entry untouched (the
     hook still exists for the other providers).
   - **Add a script** : create `hooks/<provider>/<file>` with an
     empty stub + executable bit if its extension suggests it.
   - **Remove a script** : delete `hooks/<provider>/<file>`.
   - **Add a tag** : append to `config.yaml` `tags:` (validate first).
   - **Remove a tag** : drop from `tags:`.
   - **Add a provider** : append to `config.yaml` `providers:`,
     create `<p>.yml` (empty) under every `skills/<slug>/`.
   - **Remove a provider** : remove from `providers:`, delete every
     `skills/<slug>/<p>.yml` and `hooks/<p>/` folder.
   - **Bump version** : update bundle-level `version:` in
     `config.yaml` (semver).
   - **Bump skill version** : update
     `config.yaml.skills[name=<slug>].version` (semver). Refuse if
     `<slug>` is not listed.
   - **Bump hook version** : update
     `config.yaml.hooks[name=<n>].version` (semver). Refuse if `<n>`
     is not listed.
   - **Replace description** : update `description:` in `config.yaml`.

3. **Validate the resulting layout** :
   - Every `skills/<slug>/` directory has `<slug>.md` +
     `metadata.yml` + one `<provider>.yml` per provider in
     `config.yaml` `providers:` (no more, no less).
   - Every `<provider>.yml` parses as valid YAML.
   - Every `hooks/<provider>/<file>.json` parses as valid JSON.
   - No reference inside `hooks/<provider>/` points at a deleted
     skill.
   - Every `config.yaml` `skills[].name` corresponds to a real
     `skills/<slug>/` directory (and vice-versa — no orphan listing,
     no undeclared directory).
   - Every `config.yaml` `hooks[].name` + `providers:` combination
     corresponds to a real `hooks/<provider>/<name>.<ext>` file (and
     vice-versa).

4. **Regenerate `bundles/index.yaml`** :
   - Walk every `bundles/*/config.yaml`.
   - Build the `bundles[]` array : `{name, description, directory,
     version, tags, providers}`. Sort by `name`.
   - Atomic write.

5. **Print** the change summary :
   ```
   ✅ Bundle `<name>` updated.
   Added :   <list of added paths>
   Removed : <list of removed paths>
   Tags :    <new tag list>
   Providers: <new provider list>
   Version : <new version>
   bundles/index.yaml regenerated.
   ```

## What you do NOT do

- Don't re-document the layout, the per-skill 2-file shape, the
  config.yaml shape, or the tag taxonomy — they live in
  `smith-bundle-format`.
- Don't add an `agents/` folder or any agent artefact — bundles do
  not ship their own agents in the v0.2 layout. Refuse with a one-line
  message if the maintainer asks via a (non-existent) `--add-agent`
  flag.
- Don't touch the body of an existing skill (`<slug>/<slug>.md`) or
  the contents of an existing `<provider>.yml` — that's the
  maintainer's job, by hand. This skill only handles add / remove of
  structural artefacts and bundle-level metadata.
- Don't create a brand-new bundle ; route the user to
  `/smith-bundle-add` if `<name>` does not exist.
- Don't install the bundle anywhere ; `/smith-bundle-install` does
  that.
- Don't patch `bundles/index.yaml` line-by-line — always
  regenerate from disk.
- Don't bump version automatically when changing files. The maintainer
  decides when to bump via `--bump-version`.
