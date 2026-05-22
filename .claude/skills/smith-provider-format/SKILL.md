---
name: smith-provider-format
description: Source of truth for the layout of a Smith AI-provider reference folder under `providers/<slug>/`. Documents the canonical 4-file YAML set (provider.yaml + format-skill.yaml + format-agent.yaml + format-hook.yaml), the companion `example/` directory (3 worked-out example files), the top-level fields contract on every format-*.yaml (`kind`, `provider`, `title`, `consumer_path`, `example`), and the cross-references between format files and examples. Auto-load whenever the user asks how a provider folder is laid out, what each YAML documents, or which file owns what. Consumed by `/smith-provider-add` (new provider) and `/smith-provider-edit` (modify existing provider).
when_to_use: User asks about provider folder structure, provider.yaml vs format-*.yaml vs example/, the format-*.yaml field shape, or how examples are linked back to format files. Also fires when an author / mutator skill needs the canonical layout before scaffolding or editing.
user-invocable: false
---

# Smith providers — format reference

This skill is the **single source of truth** for the layout of an AI
provider's reference folder under `providers/<slug>/`. Two other
Smith skills depend on it :

- `/smith-provider-add`  — scaffolds a new provider following this layout.
- `/smith-provider-edit` — modifies an existing provider while preserving
  this layout.

Providers documented by Smith today : `claude-code`, `github-copilot`.
Each provider folder is a self-contained YAML reference that explains
how its AI tool packages agents, skills, and hooks — so any Smith
mutator (e.g. `/smith-bundle-add`) can read one YAML per kind and know
the exact frontmatter to emit.

## Canonical provider layout

Every provider folder MUST follow this layout :

```
providers/<slug>/
├── provider.yaml                        # ROUTER — provider-level overview (capabilities + kinds map)
├── format-agent.yaml                    # per-kind doc : agent frontmatter spec
├── format-skill.yaml                    # per-kind doc : skill / prompt frontmatter spec
├── format-hook.yaml                     # per-kind doc : hook spec (may describe host-driven mechanisms for providers without first-class hooks)
└── example/
    ├── example-agent[.suffix].<ext>     # CONCRETE worked-out agent artefact (real frontmatter + body)
    ├── example-skill[.suffix].<ext>     # CONCRETE worked-out skill / prompt file
    └── example-hook[.suffix].<ext>      # CONCRETE worked-out hook fragment (or host-task fragment)
```

The 4 YAML files MUST validate against the JSON Schemas at
`providers/specs/` :

- `providers/specs/provider.schema.json`
- `providers/specs/format-agent.schema.json`
- `providers/specs/format-skill.schema.json`
- `providers/specs/format-hook.schema.json`

These schemas are the **authoritative** contract. The English prose
below is a human-friendly summary — if the two ever disagree, the
schema wins. Every mutator (`/smith-provider-add` /
`/smith-provider-edit`) MUST validate the resulting files against the
matching schema before reporting success.

Minimum viable `provider.yaml` (per `provider.schema.json`) :
`slug`, `name`, `description`, `docs`, `kinds` (with `agent` + `skill`
+ `hook` required, `rules` optional). Sections like `discovery`,
`cross_kind_interactions`, `naming_conventions`, `when_to_pick`, and
`smith_mapping` are OPTIONAL — add them when the provider warrants it,
leave them out otherwise.

The 3 example file extensions depend on the provider :
- Claude Code : `.md`, `.md`, `.json`.
- GitHub Copilot : `.agent.md`, `.prompt.md`, `-tasks.json`.

The `rules` kind is intentionally NOT modelled as a dedicated file —
rules surfaces (`CLAUDE.md`, `.claude/rules/*.md`,
`.github/copilot-instructions.md`, etc.) carry minimal or no
frontmatter and don't need a per-kind YAML.

## `provider.yaml` — the router

Provider-level overview, NOT a per-kind doc. Required top-level keys :

| Key | Purpose |
|---|---|
| `slug` | Provider slug (must match the parent directory name). |
| `name` | Human-readable name. |
| `description` | One-paragraph capability summary. |
| `docs` | Map of named links to the provider's official documentation pages. |
| `kinds` | Map. `agent` / `skill` / `hook` REQUIRED, each with `format` (path to the matching format-*.yaml), `consumer_path`, `invocation`, `example`. `rules` is OPTIONAL with a smaller shape — just `consumer_path` + `invocation` (no format file, no worked-out example). |

Optional :

| Key | Purpose |
|---|---|
| `discovery` | Where the provider looks for artefacts, with `precedence` (priority-ordered list) and `identity_rules`. |
| `cross_kind_interactions` | Bullet list — how skills dispatch agents, how hooks fire on events, etc. |
| `naming_conventions` | Bullet list — slug rules, Smith prefix conventions, etc. |
| `when_to_pick` | Decision matrix for authors choosing between skill / agent / hook. |
| `gaps_vs_claude_code` | Comparison table for non-Claude-Code providers — features missing / replaced. |
| `smith_mapping` | How Smith itself uses this provider (bundle paths, install behaviour). |

## `format-<kind>.yaml` — per-kind doc

One per artefact kind (`agent` / `skill` / `hook`). Required top-level
keys :

| Key | Required | Meaning |
|---|:---:|---|
| `kind` | yes | One of `agent`, `skill`, `hook`. Matches the filename. |
| `provider` | yes | Provider slug (matches the parent dir name). |
| `title` | yes | Human-readable title (used in the dashboard / listings). |
| `consumer_path` | yes | Where this kind lives in a consumer project (e.g. `.claude/agents/<slug>.md`). |
| `example` | yes | Relative path to the companion file under `example/`. |

After the header, the body of each YAML describes the kind in
structured form. Conventional sections (none are mandatory — pick what
the kind actually needs) :

- `frontmatter` — list of `{field, required, default, allowed, meaning}` entries (the per-field spec).
- `body_conventions` — bullet list of body authoring rules.
- `substitutions` — list of `{var, expands_to}` placeholders.
- Kind-specific sections — e.g. `events` + `handler_types` for `format-hook.yaml`, `handoff_entry_shape` + `known_tool_sets` for Copilot's `format-agent.yaml`, `tool_priority_order` + `invocation` for Copilot's `format-skill.yaml`.

YAML files MUST NOT contain comments — keep the structure as data.

## `example/example-<kind>.<ext>` — worked-out examples

The companion file referenced by the format file's `example:` field. A
FULLY functional artefact a user could drop into a real project, not a
skeleton. Showcases :
- Real frontmatter (every relevant field filled with realistic values).
- Realistic body that demonstrates the kind's idiomatic usage.
- Inline comments / `<!-- -->` blocks explaining non-obvious choices
  are allowed in the example body (it's the user-facing artefact, not
  a config file).

## Cross-references

- Every `format-<kind>.yaml` MUST reference its companion `example/`
  file via the top-level `example:` field.
- Every `format-<kind>.yaml` MAY reference the other format files in
  prose when interactions are relevant (e.g. `format-skill.yaml`
  mentions `format-hook.yaml` when documenting a `hooks:` frontmatter
  field on a skill).
- `provider.yaml`'s `kinds` map MUST reference every existing
  `format-*.yaml` in the folder via its `format:` field.

## Discovery

Providers are discovered by **directory walking** under
`providers/`. There is **no `providers/config.json`** — the
filesystem is the truth. To list providers, walk the directory and
read each `<slug>/provider.yaml` for the metadata.

## Mutator contract

Any Smith skill that creates or modifies a provider folder MUST :

1. **Read this skill** to know the canonical layout.
2. **Validate every changed YAML against its schema** under
   `providers/specs/` before reporting success. A YAML that fails
   schema validation MUST be rejected — never write a partial result.
3. **Preserve unknown top-level keys** in any YAML file — round-trip
   anything the current code doesn't recognise (the schemas use
   `additionalProperties: false` only on tightly-typed sub-shapes,
   not at the top level of every doc, to leave room for evolution).
4. **Keep the 4-file core** (`provider.yaml` + 3 `format-*.yaml`)
   intact. The 3 kinds (`agent`, `skill`, `hook`) are hardcoded — do
   NOT add a 4th `format-*.yaml`. If a provider has an extra concept
   worth documenting (e.g. MCP servers), describe it inline in
   `provider.yaml` rather than spawning a new format file.
5. **Keep every `example/example-<kind>[.suffix].<ext>` in sync** with
   its companion format file — if a format's `consumer_path:` or
   `example:` changes, the example file must move accordingly.
6. **NEVER write a provider-level index** at `providers/config.json`
   — providers are filesystem-discovered. Mutators that look for "the
   list of providers" must walk the directory.
7. **NEVER add YAML comments** (`#` at the YAML level) inside any
   `provider.yaml` or `format-*.yaml`. Comments inside an example
   block (literal `|` strings rendering a skeleton) are allowed
   because they are content, not metadata.
