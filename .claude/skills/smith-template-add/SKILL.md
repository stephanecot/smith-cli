---
name: smith-template-add
description: Scaffolds a new framework template folder under cli/templates/<framework>/<version>/ with config.yaml + an initial placeholder skill directory under skills/<slug>/ following the canonical 7-file shape (template.md + metadata.yml + claude-code.yml + github-copilot.yml + opencode.yml + README.md + CHANGELOG.md). Regenerates cli/templates/index.json. Trigger with `/smith-template-add --framework <name> --version <ver> "<description>" [--skill <slug>]`. Requires /smith-init to have run on the Smith CLI workspace.
---

# Skill — `/smith-template-add`

Scaffolds a new framework / version template directory under
`cli/templates/`. Is the **sole writer** of `cli/templates/index.json`
(regenerated from disk, never patched).

## Pre-conditions

- The Smith CLI workspace must itself be initialised
  (`.smith/architecture.json` exists at the workspace root —
  `/smith-init` was run on the cli/ project).
- `<framework>/<version>` must not already exist under
  `cli/templates/`.

## How to invoke

```
/smith-template-add --framework <name> --version <ver> "<description>" [--skill <slug>]
```

Examples :

```
/smith-template-add --framework java        --version 17 "Java 17 skill templates."
/smith-template-add --framework spring-boot --version 4  "Spring Boot 4 skill templates." --skill bootstrap
/smith-template-add --framework nextjs      --version 15 "Next.js 15 (App Router) skill templates."
```

`--skill` is optional ; defaults to `bootstrap`. If any other arg is
missing, ask via `AskUserQuestion`.

## What you do

1. **Validate inputs.** Both `<framework>` and `<version>` are
   kebab-case ; the pair must not already exist on disk. `<skill>` is
   kebab-case.

2. **Create the folder tree** :
   - `cli/templates/<framework>/<version>/`
   - `cli/templates/<framework>/<version>/skills/<skill>/`

3. **Write `config.yaml`** :
   ```yaml
   framework: <framework>
   version: "<version>"
   description: |
     <description from user input>
   providers: [claude-code, github-copilot, opencode]
   skills:
     - name: <skill>
       version: 0.1.0
   adapter_placeholders:
     "{{language}}": ""
     "{{runtime}}": ""
     "{{framework}}": "<framework>"
     "{{framework_version}}": "<version>"
     "{{root_package}}": ""
   ```
   `adapter_placeholders` start empty (except `framework` /
   `framework_version` which are deterministic) — the maintainer
   fills the rest when authoring skill bodies that reference them.

4. **Scaffold the skill directory** `skills/<skill>/` with the 7
   canonical files (see `smith-bundle-format`-equivalent contract
   for templates) :
   - `template.md` — body-only markdown stub instructing the
     maintainer to fill in the skill body. **No frontmatter.**
   - `metadata.yml` :
     ```yaml
     name: smith-<framework>-<skill>
     description: <one-line placeholder — maintainer rewrites>
     ```
     The `name` is the **final installed slug** (with the
     `smith-<framework>-` prefix). The install procedure uses it
     verbatim — no further prefixing.
   - `claude-code.yml` — empty file (0 bytes). Provider-specific
     frontmatter overrides go here, by hand.
   - `github-copilot.yml` — empty file.
   - `opencode.yml` — empty file.

   **Reminder for the maintainer** : when setting `model:` in any
   `<provider>.yml`, use the abstract tier (`small` / `medium` /
   `large`) — NEVER a concrete model identifier like `haiku` or
   `Claude Sonnet 4.5`. The installer resolves the tier at
   write-time. Same convention as bundles (see `smith-bundle-format`'s
   "Model tier abstraction" section).
   - `README.md` — human-readable doc stub (sections : What the
     adapted skill does, Per-provider overrides, Placeholders).
   - `CHANGELOG.md` — header + initial `0.1.0` entry stub.

5. **Regenerate `cli/templates/index.json`** :
   - Walk every `cli/templates/<framework>/<version>/config.yaml`.
   - Build the new `templates[]` array : `{framework, version,
     directory, config, description, providers, skills}`. Sort by
     `framework` asc then `version` desc so the most recent version
     appears first per framework.
   - Atomic write (tempfile → fsync → rename).

6. **Print the post-add checklist** :
   ```
   ✅ Template folder `<framework>/<version>` scaffolded under cli/templates/.
   Initial skill : <skill> (smith-<framework>-<skill>).
   Providers     : claude-code, github-copilot, opencode.
   cli/templates/index.json regenerated ({{N}} (framework, version) pairs total).

   Next steps :
     - Fill the body of cli/templates/<framework>/<version>/skills/<skill>/template.md.
     - Refine metadata.yml (name + description).
     - Add provider-specific frontmatter overrides to <provider>.yml when needed.
     - Fill README.md + CHANGELOG.md.
   ```

## What you do NOT do

- Don't auto-author the body of `template.md`. The skill author has
  the domain knowledge — Smith only scaffolds the directory shell.
- Don't touch other framework folders.
- Don't modify `cli/bundles/` or `cli/.claude/`.
- Don't patch `templates/index.json` line-by-line — always regenerate
  from disk so the index stays in sync with the on-disk truth.
- Don't pre-fill any `<provider>.yml` with placeholder frontmatter —
  the file MUST start empty so the maintainer's intent (no override)
  is clear. Adding values is a deliberate manual step.
- Don't ship a `providers:` field on the per-skill `metadata.yml` —
  providers are bundle-level in `config.yaml`. Each skill ships one
  `<provider>.yml` per provider in `config.yaml` `providers:`.
