---
name: smith-template-add
description: Scaffolds a new framework template folder under cli/templates/<framework>/<version>/ with config.yaml + initial placeholder skills/ dir. Regenerates cli/templates/index.json. Trigger with `/smith-template-add --framework <name> --version <ver> "<description>"`. Requires /smith-init to have run on the Smith CLI workspace (this skill operates on `cli/templates/`, not on a consumer project).
---

# Skill — `/smith-template-add`

Scaffolds a new framework / version template directory under
`cli/templates/`. Is the **sole writer** of `cli/templates/index.json`
(regenerated from disk, never patched).

## Pre-conditions

- The Smith CLI workspace must itself be initialised (`.smith/architecture.json`
  exists at the workspace root — `/smith-init` was run on the cli/ project).
- `<framework>/<version>` must not already exist under `cli/templates/`.

## How to invoke

```
/smith-template-add --framework <name> --version <ver> "<description>"
```

Examples :

```
/smith-template-add --framework java        --version 17 "Java 17 skill templates."
/smith-template-add --framework spring-boot --version 4  "Spring Boot 4 skill templates."
/smith-template-add --framework nextjs      --version 15 "Next.js 15 (App Router) skill templates."
```

If any arg is missing, ask via `AskUserQuestion`.

## What you do

1. **Validate inputs.** Both `<framework>` and `<version>` are
   kebab-case ; the pair must not already exist on disk.
2. **Create the folder** `cli/templates/<framework>/<version>/skills/`.
3. **Write `config.yaml`** following the canonical shape (see
   `cli/templates/angular/21/config.yaml` for the reference) :
   - `framework`, `version`, `description` from the user input.
   - `files:` — empty list ; the user fills it after authoring SKILL files.
     Each entry has `kind`, `path` (relative to the template dir),
     `description`.
   - `adapter_placeholders:` — empty map. The user fills with the
     standard placeholders (`{{language}}`, `{{runtime}}`, `{{framework}}`,
     `{{framework_version}}`, `{{root_package}}`).
4. **Regenerate `cli/templates/index.json`** :
   - Walk every `cli/templates/<framework>/<version>/config.yaml`.
   - Build the new `templates[]` array, sort by `framework` asc then
     `version` desc so the most recent version appears first per
     framework.
   - Atomic write (tempfile → fsync → rename).
5. **Print the post-add checklist** : « Now author your SKILL body files
   under `cli/templates/<framework>/<version>/skills/<slug>.SKILL.md`
   (body-only markdown, no YAML frontmatter — the customizer adds it on
   adaptation). Add their paths to the `files:` list in `config.yaml`. »

## What you do NOT do

- Don't auto-author any SKILL body. The skill author has the domain
  knowledge — Smith only scaffolds the directory shell.
- Don't touch other framework folders.
- Don't modify `cli/bundles/` or `cli/.claude/`.
- Don't patch `templates/index.json` — always regenerate from disk so
  the index stays in sync with the on-disk truth.

## Reporting back

```
✅ Template folder `<framework>/<version>` scaffolded under cli/templates/.
cli/templates/index.json regenerated ({{N}} (framework, version) pairs total).

Next steps :
  - Author <framework>-<slug>.SKILL.md body files under cli/templates/<framework>/<version>/skills/.
  - Add their paths to config.yaml `files:` list.
```
