---
name: smith-template-add
description: Scaffolds a new template folder under `templates/<category>/<name>/<version>/`. Two categories supported — `framework` (N skills under skills/<slug>/) and `bootstrap` (exactly 1 skill under skill/, plus optional assets/ + templates/ + scripts/ buckets). Writes config.yaml + version-level README.md + CHANGELOG.md, scaffolds the canonical 2-file skill shape (<slug>.md body + metadata.yml), and regenerates the per-category `index.yaml`. Trigger with `/smith-template-add --category framework|bootstrap --name <name> --version <ver> "<description>" [--skill <slug>]`. Requires /smith-init to have run on the Smith CLI workspace.
---

# Skill — `/smith-template-add`

Scaffolds a new template directory under `templates/`. Is the
**sole writer** of `templates/<category>/index.yaml` for the
target category (regenerated from disk, never patched).

## Categories

| Category    | Layout                                              | Skills      | Sidecar buckets                        |
|-------------|-----------------------------------------------------|-------------|----------------------------------------|
| `framework` | `framework/<name>/<version>/skills/<slug>/`         | N (1+)      | none                                   |
| `bootstrap` | `bootstrap/<name>/<version>/skill/`                 | 1 (exactly) | `assets/`, `templates/`, `scripts/`    |

The category is **declared via `--category`** — defaults to
`framework` when omitted (backward compat). Per-category structure
rules are enforced at scaffold time.

## Pre-conditions

- The Smith CLI workspace must itself be initialised
  (`.smith/architecture.json` exists at the workspace root —
  `/smith-init` was run on the cli/ project).
- `<name>/<version>` must not already exist under
  `templates/<category>/`.

## How to invoke

```
/smith-template-add --category framework|bootstrap \
                    --name <name> \
                    --version <ver> \
                    "<description>" \
                    [--skill <slug>]
```

Examples :

```
# framework — multi-skill template set
/smith-template-add --category framework --name spring-boot --version 4 \
    "Spring Boot 4 skill templates." --skill bootstrap

# bootstrap — single-skill scaffold + sidecar buckets
/smith-template-add --category bootstrap --name angular --version 21 \
    "Bootstrap a new Angular 21 SPA — package, routing, optional Tailwind / Transloco / OpenAPI."
```

- `--category` — optional, defaults to `framework`. One of `framework`
  or `bootstrap`.
- `--skill` — optional. Only meaningful for `--category framework`
  (defaults to `bootstrap`). Ignored for `--category bootstrap` (the
  skill folder is always `skill/`, slug derived from the body
  filename + metadata).

If any required arg is missing, ask via `AskUserQuestion`.

## What you do

### Common steps (both categories)

1. **Validate inputs.** `<name>` + `<version>` are kebab-case ; the
   pair must not already exist under
   `templates/<category>/`. `<category>` ∈ `{framework, bootstrap}`.

2. **Create the folder tree** `templates/<category>/<name>/<version>/`.

3. **Write the version-level docs** :
   - `README.md` — human-readable doc stub (sections : What ships
     here, Stack targeted).
   - `CHANGELOG.md` — header + initial `0.1.0` entry stub.
   These live at the version level — ONE pair per (name, version)
   regardless of category. No per-skill README / CHANGELOG.

### Category-specific scaffold

#### `--category framework`

4a. **Write `config.yaml`** :
    ```yaml
    framework: <name>
    version: "<version>"
    description: |
      <description from user input>
    skills:
      - name: <skill>
        version: 0.1.0
        tags: [<name>]              # required ; gates the install filter
    adapter_placeholders:
      "{{language}}": ""
      "{{runtime}}": ""
      "{{framework}}": "<name>"
      "{{framework_version}}": "<version>"
      "{{root_package}}": ""
    ```
    `adapter_placeholders` start empty (except `framework` /
    `framework_version` which are deterministic). **No `providers:`
    field** — templates apply to every provider. **`tags[]` is
    required per skill** : the consumer-side `/smith-new-project`
    keeps a skill only when its tags intersect the project stack
    (union of `architecture.json::*[].tags[]`). Use the canonical
    bundle taxonomy (see `smith-bundle-format`) — `<name>` itself is
    a safe baseline, add the central tech the skill is gated on
    (e.g. `transloco` for an i18n skill, `tailwindcss` for a design
    skill).

5a. **Scaffold the initial skill** `skills/<skill>/` :
    - `<skill>.md` — body-only markdown stub (no frontmatter).
    - `metadata.yml` :
      ```yaml
      name: smith-<name>-<skill>
      description: <one-line placeholder — maintainer rewrites>
      # Optional generic properties (resolved per provider at build
      # time via provider.yaml::build.skill_property_map) :
      # model: small | medium | large
      # user-invocable: true | false
      ```
      The `name` is the **final installed slug** (with the
      `smith-<name>-` prefix). The install uses it verbatim — no
      further prefixing.

#### `--category bootstrap`

4b. **Write `config.yaml`** :
    ```yaml
    name: <name>
    version: "<version>"
    description: |
      <description from user input>
    tags: [<name>]                  # required ; gates the install filter
    assets: []
    templates: []
    scripts: []
    ```
    `tags[]` lives at the top level (bootstrap = singleton skill, so
    no per-skill tags) and gates the install filter in
    `/smith-new-project` Step 8.a. Use the canonical bundle taxonomy
    — `<name>` itself is a safe baseline, add the central tech the
    bootstrap scaffolds (e.g. `frontend`, `typescript`, `angular`).

    `assets[]`, `templates[]`, `scripts[]` start empty — the
    maintainer adds entries as they author the sidecar files. **No
    `skills:` array** : the `skill/` directory implies the singleton
    skill. **No `providers:` field**.

5b. **Scaffold the singleton skill** `skill/` :
    - `<name>.md` — body-only markdown stub (no frontmatter).
    - `metadata.yml` :
      ```yaml
      name: smith-<name>-bootstrap
      description: <one-line placeholder — maintainer rewrites>
      # Optional generic properties :
      # model: small | medium | large
      # user-invocable: true | false
      ```
      The `name` MUST follow the `smith-<name>-bootstrap` convention
      so the installed skill is easy to spot in `.claude/skills/`.

6b. **Scaffold empty sidecar buckets** (only when the user mentions
    they'll need them — otherwise omit) :
    `assets/`, `templates/`, `scripts/`. Empty dirs are valid ; the
    build copies whatever's present.

### Common — regenerate the index

7. **Regenerate `templates/<category>/index.yaml`** :
   - Walk every `templates/<category>/<name>/<version>/config.yaml`.
   - Build the entry list :
     - framework : `templates[]` with `{framework, version,
       directory, config, description, skills}`. Each `skills[]`
       entry copies `{name, version, tags}` from `config.yaml`
       verbatim — tags MUST land in the index so the consumer-side
       filter runs without opening any config.yaml.
     - bootstrap : `bootstraps[]` with `{name, version, directory,
       config, description, tags}` — the top-level `tags` from
       `config.yaml` is copied verbatim into the entry.
   - Sort by `name`/`framework` asc then `version` desc.
   - Atomic write (tempfile → fsync → rename).

8. **Print the post-add checklist** :
   ```
   ✅ Template `<category>/<name>/<version>` scaffolded.
   Skill : <name + suffix per category>.
   templates/<category>/index.yaml regenerated.

   Next steps :
     - Fill the body of templates/<category>/<name>/<version>/{skill|skills/<slug>}/<file>.md.
     - Refine metadata.yml (name + description ; optional model / user-invocable).
     - Fill README.md + CHANGELOG.md at the version level.
     - (bootstrap only) Add assets / templates / scripts files as needed.
   ```

## What you do NOT do

- Don't author the body of `<skill>.md`. The skill author has the
  domain knowledge — Smith only scaffolds the directory shell.
- Don't scaffold any `skills/<slug>/<provider>.yml` files — those
  are gone. Provider-specific frontmatter is composed at build time
  from generic properties in `metadata.yml`.
- Don't scaffold per-skill `README.md` / `CHANGELOG.md` — version
  level only.
- Don't ship a `providers:` field anywhere (templates apply to every
  provider ; the field is gone).
- Don't ship a `skills:` array on a `--category bootstrap` config —
  the singleton skill is implicit.
- Don't touch other template folders or other categories.
- Don't modify `bundles/` or `cli/.claude/`.
- Don't patch any `index.json` line-by-line — always regenerate from
  disk so the index stays in sync with the on-disk truth.
