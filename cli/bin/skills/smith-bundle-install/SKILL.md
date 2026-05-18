---
name: smith-bundle-install
description: Installs a bundle from cli/bundles/<name>/ into the consumer project's .claude/ (or .github/ for Copilot). Copies files declared in the bundle's config.yaml for the target provider. Trigger with `/smith-bundle-install --name <bundle> --ia <provider>`. Requires /smith-init to have run.
---

# Skill — `/smith-bundle-install`

Copies a bundle from the Smith CLI catalogue into the consumer project, in
the layout the target provider expects.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `--name <bundle>` must be a key listed in `cli/bundles/config.json`.
- `--ia <provider>` must be in the bundle's `config.yaml` `providers:` list.

## How to invoke

```
/smith-bundle-install --name <bundle> --ia <provider>
```

Example :

```
/smith-bundle-install --name mvn --ia claude-code
/smith-bundle-install --name ia-stats --ia claude-code
```

If either flag is missing, ask via `AskUserQuestion`.

## What you do

1. **Look up the bundle** in `cli/bundles/config.json` (read-only). Bail if the
   name is unknown ; suggest the closest match by string distance.
2. **Read the bundle's `config.yaml`** to find the `files.<provider>:` list.
   Bail if the bundle does not declare support for the requested provider.
3. **Map source → destination paths** :
   - `claude-code/skills/<slug>/SKILL.md` → `.claude/skills/<slug>/SKILL.md`
   - `claude-code/agents/<slug>.md`       → `.claude/agents/<slug>.md`
   - `claude-code/scripts/<name>.py`      → `.claude/scripts/<name>.py`
   - `claude-code/hooks/<name>.hooks.json` → print as a snippet for the user
     to merge into `.claude/settings.json` (do NOT overwrite the user's
     settings — hooks are merge-required).
   - For Copilot : `.github/prompts/` / `.github/chatmodes/` /
     `.github/instructions/` per the provider's convention.
4. **Copy each file atomically** (tempfile → fsync → rename). Refuse to
   overwrite an existing file unless `--force` is passed (a future flag,
   not part of v0.1 — for now, refuse and ask the user to remove the file
   manually).
5. **Set the executable bit** on any `.py` / `.sh` script that lands under
   `.claude/scripts/`.
6. **Update `.smith/smith-config.json`** at the consumer project root :
   - The canonical shape of the file + the `bundles[]` entry shape are
     documented in the sibling skill **`smith-config-format`** ; consult
     its body and use the template at
     `${CLAUDE_SKILL_DIR}/../smith-config-format/template/smith-config.template.json`
     as the source of truth for any key you might touch.
   - Read the current `.smith/smith-config.json` (it must exist —
     `/smith-init` created it). In the `bundles[]` array, **upsert** an
     entry keyed by `name`, matching the shape in `smith-config-format`
     (kind / source / destination / installed_at). Re-installing the
     same bundle replaces the existing entry in place — never duplicates.
   - **Preserve unknown keys** : round-trip anything in
     `smith-config.json` that you don't explicitly touch.
   - **Update `generated_at`** to the current ISO-8601 UTC time on every
     successful write.
   - Atomic write (tempfile → fsync → rename).
   - **Do not touch `.smith/project-config.json`** — that file describes
     the project's tech stack, not what Smith installed. Format spec
     lives in the sibling skill `smith-project-config-format`.
7. **Print the post-install snippet** for hooks (if any) so the user knows
   what to paste into `.claude/settings.json`.

## What you do NOT do

- Don't merge `settings.json` automatically — that's the user's call, and
  the JSON merge logic is non-trivial enough to defer.
- Don't modify `cli/bundles/config.json` (that's `/smith-bundle-add`'s job —
  it lists the catalogue). This skill only writes the consumer-side
  `.smith/smith-config.json` (which lists what's installed in the consumer).
- Don't install transitive bundles. If a bundle depends on another, the
  user installs each one explicitly. Dependencies are reported in the
  bundle's README.

## Reporting back

```
✅ Bundle `<name>` installed for provider `<ia>`.
Files copied :
  - <source> → <destination>
  - ...
{{Optional hooks snippet block for the user to paste into settings.json}}
```
