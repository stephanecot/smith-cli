---
name: smith-template-install
description: Builds adapted SKILL artefacts for a consumer project from a framework template set under cli/templates/framework/<framework>/<version>/. For each skills/<slug>/ directory in the template, assembles the destination file by composing frontmatter from metadata.yml + <provider>.yml (validated against cli/providers/<provider>/format-skill.yaml), substitutes adapter_placeholders, and prepends to the body. Writes the result to the provider's consumer_path. Upserts into .smith/config.json `skills[]`. Trigger with `/smith-template-install --framework <name> [--version <ver>] --ai <provider>`. Requires /smith-init.
---

# Skill — `/smith-template-install`

Read-only on `cli/templates/`. Produces adapted SKILL files in the
consumer project at the per-provider `consumer_path` declared by
`cli/providers/<provider>/provider.yaml`. Upserts entries into
`<consumer>/.smith/config.json` `skills[]`.

## Pre-conditions

- `<consumer>/.smith/architecture.json` AND
  `<consumer>/.smith/config.json` must exist (`/smith-init` markers).
- `cli/templates/index.yaml` must list at least one entry for the
  requested `<framework>`.
- The resolved `<provider>` MUST appear in
  `cli/templates/framework/<framework>/<version>/config.yaml` `providers:`.

## How to invoke

```
/smith-template-install --framework <name> [--version <ver>] --ai <provider> [--consumer-dir <path>] [--no-config-write]
```

- `--consumer-dir <path>` — absolute path of the consumer project
  root. Defaults to the directory containing `.smith/smith.yaml`
  walking up from CWD ; orchestrators MUST pass it explicitly to
  avoid writing into a parent repo's `.claude/`.
- `--no-config-write` — when set, adapts every template skill and
  writes the resulting files as usual, but does **NOT** mutate
  `<consumer>/.smith/config.json`. Instead emits every `skills[]`
  entry as a JSON object on stdout prefixed by `SKILL_ENTRY:` so the
  orchestrator can collect them and upsert serially in one final
  pass — avoids parallel-write races.

Examples :

```
/smith-template-install --framework angular --version 21 --ai claude-code
/smith-template-install --framework java-spring-boot       --ai opencode   # version inferred
```

If `--framework` or `--ai` is missing, ask via `AskUserQuestion`.

## Version resolution (when `--version` is omitted)

1. Read `cli/templates/index.yaml`. Filter entries with the requested
   `framework`.
2. If only one version exists for that framework → use it.
3. If multiple versions exist :
   - Read `<consumer>/.smith/architecture.json` to find the project's
     actual version for that framework (e.g. `angular: 21.2.0`).
   - Pick the largest template version `≤` the project version
     (downward match). If none, pick the smallest available template
     version and emit a `version_drift_upward` flag.
4. Tell the user which version was selected and why, in one line.

## What you do

1. **Validate inputs** and resolve the version as described above.

2. **Load the template config** at
   `cli/templates/framework/<framework>/<version>/config.yaml`. Confirm
   `<provider>` is in `providers:`. Bail if not. Load the
   `adapter_placeholders` map and the `skills[]` listing (the version
   index).

3. **Load the provider's format spec** :
   - `cli/providers/<provider>/provider.yaml` →
     `kinds.skill.consumer_path` (where to write — e.g.
     `.claude/skills/<slug>/SKILL.md`).
   - `cli/providers/<provider>/format-skill.yaml` →
     `frontmatter[].field` (the set of valid frontmatter keys).

4. **Walk `skills/`** in the template directory. For each
   `skills/<slug>/` :

   ### Skill assembly — MANDATORY procedure

   1. **`Read`** `skills/<slug>/<slug>.md` → `body` (body-only, no
      frontmatter to strip).
   2. **Substitute `adapter_placeholders`** in `body`. Each key in
      the map is a literal token (e.g. `{{root_package}}`) and the
      value is either a literal replacement OR a description of what
      to pull from `<consumer>/.smith/architecture.json`. The
      installer resolves the latter at runtime ; unresolved
      placeholders that remain in `body` after substitution emit a
      warning (the maintainer's description was too vague).
   3. **`Read`** `skills/<slug>/metadata.yml` → `meta` dict. Required
      keys : `name`, `description`. `name` is the **final installed
      slug** verbatim (e.g. `smith-angular-bootstrap`) — no further
      prefixing.
   4. **`Read`** `skills/<slug>/<provider>.yml` → `override` dict.
      May be an empty file → treat as `{}`.
   5. **Compose the frontmatter dict** :
      - Start from `meta`.
      - Overlay every key from `override`. `override` wins on
        collisions.
      - **Filename-encoded identity exception** : if `name` is
        present but the provider's `format-skill.yaml` does NOT
        declare `name` as a frontmatter field (e.g. OpenCode encodes
        the slug in the filename, not the frontmatter), DROP `name`
        from the composed dict silently. `name` is still used to
        compute the destination path; it just doesn't appear in the
        YAML header.
      - **Resolve the model tier** : if `model` is present and its
        value is one of `small` / `medium` / `large`, replace it
        with the provider-native identifier from
        `<consumer>/.smith/smith.yaml` `model_tiers:` (written by
        `/smith-init`). Fall back to the built-in defaults table
        documented in `/smith-bundle-install`'s "Model tier
        resolution" section when `smith.yaml` is absent or the tier
        is missing. Legacy templates with concrete model identifiers
        are left untouched and emit `model-tier-skipped`.
      - **Validate every remaining key** against the provider's
        frontmatter spec. A key is valid iff it appears in
        `format-skill.yaml` `frontmatter[].field`. Reject any
        unknown key with `unknown-frontmatter-field` naming the
        framework, version, slug, provider, and the offending key.
        Abort the install.
   6. **Serialise** the frontmatter to YAML between `---` fences.
      Stable key ordering : `name` first, `description` second, then
      every other key alphabetically.
   7. **Resolve the destination path** by substituting the final
      installed slug (`meta.name`) into the provider's
      `kinds.skill.consumer_path`. Example for `claude-code` and
      slug `smith-angular-bootstrap` :
      `<consumer>/.claude/skills/smith-angular-bootstrap/SKILL.md`.
   8. **`Write`** the assembled content (`<frontmatter>\n\n<body>`).
      Atomic via the `Write` tool. Refuse to overwrite an existing
      destination unless `--force` is later added (no `--force` in
      v0.2).
   9. **Post-condition (MANDATORY)** : re-read the destination and
      verify :
      - Starts with `---` and contains a closing `---` on its own
        line.
      - Frontmatter parses as YAML and contains at minimum
        `description:` (and `name:` for providers that declare it).
      - The body matches the substituted source byte-for-byte.

      If ANY check fails, abort the bundle install with a clear
      diagnostic naming the failing check + the destination path.

5. **Record the install in `<consumer>/.smith/config.json`** :

   - **Without `--no-config-write`** : upsert in-place.
   - **With `--no-config-write`** : emit each `skills[]` entry on
     stdout prefixed `SKILL_ENTRY:`. Do NOT touch the file.

   Entry shape (per `smith-config-format`) :
   ```json
   {
     "name": "smith-<framework>-<slug>",
     "from_template": "<framework>/<version>/skills/<slug>",
     "version": "<config.yaml skills[name=<slug>].version>",
     "path": "<consumer-relative path to the adapted SKILL.md>",
     "adapted_at": "<ISO-8601 UTC>"
   }
   ```

   - `version` comes from `cli/templates/framework/<framework>/<version>/config.yaml`
     `skills[name=<slug>].version` (NEVER from `metadata.yml`, which
     no longer carries a version).
   - Re-running with a newer template version replaces entries with
     the same `name` — never duplicates.
   - **Preserve unknown keys** in `config.json`.
   - **Update `generated_at`** to the current ISO-8601 UTC time.
   - Atomic write.

6. **Relay** a generation report :
   ```
   ✅ Built {{N}} skills from template `<framework>/<version>` for provider `<ai>`.
   {{Y}} kept, {{Z}} rejected.
   .smith/config.json updated — skills[] now lists {{T}} entries.
   ```

## What you do NOT do

- Don't author or modify any template skill body yourself. The
  template maintainer is the author ; this skill only assembles.
- Don't write to `cli/templates/` — read-only on the catalogue.
- Don't run `/smith-init` automatically. If `.smith/*-config.json` is
  missing, refuse and tell the user to run `/smith-init` first.
- Don't accept unknown frontmatter keys in `<provider>.yml`. Every
  key must be in the provider's
  `cli/providers/<provider>/format-skill.yaml` `frontmatter[].field`
  list. Unknown keys mean the template author made a mistake —
  abort.
- Don't prefix `metadata.yml` `name` further. The template author
  writes the final installed slug verbatim
  (`smith-<framework>-<slug>`); the installer uses it as-is.
- Don't fall back to the old `files:` map — that key is gone in the
  v0.2 layout. Walk `skills/<slug>/` directories from disk.
