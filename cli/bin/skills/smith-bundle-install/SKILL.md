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
4. **Copy each file atomically — and resolve every `@smith-include`
   directive in the process.** Most files copy byte-for-byte
   (scripts, hooks JSON, tasks JSON, README, …). The exception is
   any file with `kind: skill` or `kind: agent` in the bundle's
   `files.<provider>:` list — these are **wrapper files** whose body
   is a single line of the shape :

   ```
   <!-- @smith-include: <relative-path-to-common-body> -->
   ```

   For every such wrapper :

   a. **Parse the wrapper** : split into YAML frontmatter (the leading
      `---` … `---` block) + body. Locate the `<!-- @smith-include: <p> -->`
      line in the body. There MUST be exactly one ; refuse with a
      clear error if zero or more than one (the bundle is malformed).
   b. **Resolve the path** : `<p>` is relative to the wrapper file's
      **own directory** under `cli/bundles/<bundle>/`, NOT to the
      consumer project. The path always points into the bundle's
      `common/` tree (e.g. `../../../common/skills/<slug>.md` from
      `claude-code/skills/<slug>/SKILL.md`).
   c. **Read the common body** at the resolved path. Refuse with a
      clear error if the file does not exist.
   d. **Assemble** : the destination file is the wrapper's frontmatter
      block, then a single blank line, then the common body verbatim.
      The `<!-- @smith-include: ... -->` directive line MUST NOT
      appear in the destination — strip it completely.
   e. **Post-condition** : after writing, re-read the destination and
      confirm `@smith-include` does not appear anywhere. If it does,
      abort the install and report a bug — the contract is "zero
      `@smith-include` traces in the installed file".

   Atomic write (tempfile → fsync → rename) for every copy, resolved
   or byte-for-byte. Refuse to overwrite an existing destination file
   unless `--force` is passed (a future flag, not part of v0.1 — for
   now, refuse and ask the user to remove the file manually).

   **`common/` files themselves are NEVER copied to the consumer
   project.** They are a build-time concept (single-source factorised
   bodies). Only their content lands in the consumer — inlined into
   the wrappers above.

5. **Set the executable bit** on any `.py` / `.sh` script that lands under
   `.claude/scripts/`.
6. **Update `.smith/config.json`** at the consumer project root :
   - The canonical shape of the file + the `bundles[]` entry shape are
     documented in the sibling skill **`smith-config-format`** ; consult
     its body and use the template at
     `${CLAUDE_SKILL_DIR}/../smith-config-format/template/config.template.json`
     as the source of truth for any key you might touch.
   - Read the current `.smith/config.json` (it must exist —
     `/smith-init` created it). In the `bundles[]` array, **upsert** an
     entry keyed by `name`, matching the shape in `smith-config-format`
     (kind / source / destination / installed_at). Re-installing the
     same bundle replaces the existing entry in place — never duplicates.
   - **Preserve unknown keys** : round-trip anything in
     `config.json` that you don't explicitly touch.
   - **Update `generated_at`** to the current ISO-8601 UTC time on every
     successful write.
   - Atomic write (tempfile → fsync → rename).
   - **Do not touch `.smith/architecture.json`** — that file describes
     the project's tech stack, not what Smith installed. Format spec
     lives in the sibling skill `smith-architecture-format`.
7. **Print the post-install snippet** for hooks (if any) so the user knows
   what to paste into `.claude/settings.json`.

## What you do NOT do

- **Don't leave any `@smith-include` directive in the installed
  files.** Every wrapper's directive MUST be resolved (the common body
  inlined) before the destination is written. The directive is a
  build-time mechanism — its presence in the consumer's `.claude/` or
  `.github/` tree is a bug. The step-4 post-condition above exists
  precisely to catch this.
- **Don't copy `common/` files** to the consumer project. Their
  content lands inlined into the wrappers ; the `common/` tree itself
  stays inside `cli/bundles/<bundle>/`.
- Don't merge `settings.json` automatically — that's the user's call, and
  the JSON merge logic is non-trivial enough to defer.
- Don't modify `cli/bundles/config.json` (that's `/smith-bundle-add`'s job —
  it lists the catalogue). This skill only writes the consumer-side
  `.smith/config.json` (which lists what's installed in the consumer).
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
