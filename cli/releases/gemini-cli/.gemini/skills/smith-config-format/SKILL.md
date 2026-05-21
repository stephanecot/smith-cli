---
name: smith-config-format
description: Source of truth for the format of `.smith/config.json` — the Smith state file (provider + spec paths + AGENTS.md pointer + adapted skills + installed bundles). Documents every field, its type, allowed values, defaults, and who is allowed to write it. Ships the canonical macro template under `templates/config.template.json`. Auto-load whenever the user asks how `config.json` is laid out, what a field means, or which skill upserts which list. Sister skill `smith-architecture-format` covers the OTHER file (`.smith/architecture.json`, the project identity file) — keep the scope separate.
when_to_use: User asks about `.smith/config.json`, the Smith state file, the `skills[]` or `bundles[]` lists, the provider field, the `specifications.*` paths, or the mutator contract used by `/smith-bundle-install` / `/smith-template-install`. Also fires when a skill needs to compose or upsert into this JSON.
user-invocable: false
---

# `.smith/config.json` — format reference

This skill is the **single source of truth** for `.smith/config.json`,
the Smith state file. It tracks what Smith has done to the consumer
project : which provider runs the show, where the narrative
specifications live, which skills have been adapted from templates,
which bundles have been installed. Every field, type, default and
ownership rule is documented below. The macro template under
`templates/config.template.json` is the canonical fill-in-the-blank
skeleton that `/smith-init` and the install mutators read.

The sister skill `smith-architecture-format` covers the OTHER managed
file (`.smith/architecture.json` — the project identity file). Their
scopes never overlap : one file describes what the project IS, the other
describes what Smith has DONE to it.

`AGENTS.md` at the project root is **out of scope** here — it is owned
by `/smith-init` and never re-written by other Smith skills.

## File summary

| Field | Value |
|---|---|
| Path                  | `.smith/config.json` |
| Purpose               | What Smith has DONE — provider, spec paths, AGENTS.md pointer, adapted skills, installed bundles. |
| Template              | `templates/config.template.json` |
| Created by            | `/smith-init` (idempotent — if file exists, do not touch). |
| Updated by            | `/smith-bundle-install` (upserts `bundles[]`), `/smith-template-install` (upserts `skills[]`). |
| Read by               | `/smith-dashboard`, `/smith-bundle-install`, `/smith-template-install`, `/smith-generate-docs`. |

## Top-level keys

| Key | Type | Required | Meaning |
|---|---|:---:|---|
| `version`            | number         | yes | Schema version (`1` today). |
| `smith_cli_version`  | string         | yes | Version of the Smith CLI that wrote the file. |
| `generated_at`       | string         | yes | ISO-8601 UTC write timestamp (refreshed on every upsert). |
| `git_sha`            | string \| null | yes | Project `HEAD` at init time. |
| `provider`           | string         | yes | `"claude-code"` or `"github-copilot"`. |
| `specifications`     | object         | yes | Paths to the narrative spec files (filled by `/smith-generate-docs`). |
| `ai_memory_file`     | string         | yes | Always `"AGENTS.md"` in v0.1. |
| `skills`             | array          | yes | Adapted skills — starts empty, `/smith-template-install` upserts. |
| `bundles`            | array          | yes | Installed bundles — starts empty, `/smith-bundle-install` upserts. |

## `specifications.*` keys

```json
"specifications": {
  "functional": ".smith/FUNCTIONAL_SPECIFICATION.MD",
  "technical":  ".smith/TECHNICAL_SPECIFICATION.MD"
}
```

These paths point at files that may not exist yet — they are written by
`/smith-generate-docs`. The paths themselves are stable.

## `skills[]` entry shape

```json
{
  "name": "smith-<framework>-<slug>",
  "from_template": "<framework>/<version>/skills/<slug>",
  "version": "<from template config.yaml skills[name=<slug>].version>",
  "path": "<consumer-relative path to the adapted SKILL.md>",
  "adapted_at": "<ISO-8601 UTC>"
}
```

- `from_template` is the **directory** under the template that owns the
  skill (`<framework>/<version>/skills/<slug>/`), not a file path. The
  directory contains `<slug>.md` (body), `metadata.yml`, and one
  `<provider>.yml` per supported provider.
- `version` comes from the template's `config.yaml` `skills[].version`
  (never from `metadata.yml`, which no longer carries a version).
- Upsert keyed by `name` — re-running `/smith-template-install` with a
  newer template version replaces the existing entry, never
  duplicates.

## `bundles[]` entry shape

```json
{
  "name": "<bundle-slug>",
  "version": "<bundle-level version from config.yaml>",
  "tags": ["<from taxonomy>"],
  "provider": "<--ia value passed to install>",
  "skills": [
    { "name": "<slug>", "version": "<from bundle config.yaml skills[].version>" }
  ],
  "hooks": [
    { "name": "<hook-name>", "version": "<from bundle config.yaml hooks[].version>" }
  ],
  "merged_into": [
    "<consumer-relative path of a provider config file the install merged into>"
  ],
  "installed_at": "<ISO-8601 UTC>"
}
```

- `skills[]` and `hooks[]` mirror the bundle's `config.yaml`
  listings for the slice actually installed for this provider — every
  entry the bundle ships gets recorded with its per-skill /
  per-hook version.
- `hooks[]` is empty (`[]`) for skill-only bundles.
- `merged_into[]` lists every consumer-side file the install merged
  hook / task fragments into (typically `.claude/settings.json` for
  Claude Code, `.vscode/tasks.json` for Copilot). Empty when the
  bundle ships no hooks.
- **No more `files[]` array.** The v0.2 install records WHAT was
  installed (`skills[]` + `hooks[]`) by name and version. Source ↔
  destination path mapping is derivable from the provider's
  `consumer_path` (in `cli/providers/<provider>/provider.yaml`) — the
  catalogue does not duplicate it.
- Upsert keyed by `name` — re-installing replaces the existing
  entry, never duplicates.

### `merged_into[]` and the `_smith_source` marker

Hook fragments (Claude Code `claude-code/hooks/<n>.hooks.json`) and
task fragments (Copilot `github-copilot/tasks/<n>.tasks.json`) are
**not** copied as standalone files — they are **merged** into the
provider's live config (`.claude/settings.json` for Claude Code,
`.vscode/tasks.json` for Copilot) by `/smith-bundle-install`. The
merge is idempotent and reversible because every Smith-injected
entry carries a marker :

```json
{ "matcher": "*",
  "hooks": [{ "type": "command", "command": "node ..." }],
  "_smith_source": "<bundle-slug>" }
```

- The marker is added by `/smith-bundle-install` step 4-bis.
- `bundles[].merged_into[]` lists every consumer-side file the merge
  touched (so the future `/smith-bundle-uninstall` knows where to
  scrub entries with the matching `_smith_source`).
- Empty array (`merged_into: []`) when the bundle ships no hooks /
  tasks — most bundles fall in that category.
- Entries WITHOUT a `_smith_source` field (hand-written or from
  another tool) are always preserved untouched by Smith.

## Mutator contract

Any Smith skill that mutates `.smith/config.json` MUST :

1. **Read the canonical template** from
   `templates/config.template.json` first to know the full shape —
   even when only upserting one section. Missing keys must not be
   dropped.
2. **Atomic write** : write to `<file>.tmp`, fsync, then `mv` over the
   final path. Never leave a half-written JSON.
3. **Preserve unknown keys** : if a future Smith version adds a key the
   current code doesn't understand, the mutator must round-trip it
   unchanged.
4. **Update `generated_at`** on every successful write.

## Skills that read this skill

| Skill | What it does with `config.json` |
|---|---|
| `/smith-init`             | Reads `templates/config.template.json`, fills the placeholders, atomic-writes the empty shell. |
| `/smith-bundle-install`   | Reads the bundle entry shape, upserts the `bundles[]` array keyed by `name`. |
| `/smith-template-install` | Reads the skill entry shape, upserts the `skills[]` array keyed by `name`. |
| `/smith-generate-docs`    | Reads `specifications.*` to know where to write the spec files. Read-only on this skill's shape. |
| `/smith-dashboard`        | Reads the written JSON to render the dashboard. Doesn't read `templates/` directly. |
