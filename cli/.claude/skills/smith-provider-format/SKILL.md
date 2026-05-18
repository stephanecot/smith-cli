---
name: smith-provider-format
description: Source of truth for the layout of a Smith AI-provider reference folder under `cli/providers/<slug>/`. Documents the canonical 5-file rule set (RULES.MD router + 4 rule-*.MD per-kind docs), the companion `example/` directory (4 worked-out example files), the frontmatter contract on every rule-*.MD (`kind`, `provider`, `path`, `example`), and the cross-references between rule files and examples. Auto-load whenever the user asks how a provider folder is laid out, what each rule file documents, or which file owns what. Consumed by `/smith-provider-add` (new provider) and `/smith-provider-edit` (modify existing provider).
when_to_use: User asks about provider folder structure, RULES.MD vs rule-*.MD vs example/, the rule-*.MD frontmatter shape, or how examples are linked back to rules. Also fires when an author / mutator skill needs the canonical layout before scaffolding or editing.
user-invocable: false
---

# Smith providers — format reference

This skill is the **single source of truth** for the layout of an AI
provider's reference folder under `cli/providers/<slug>/`. Two other
Smith skills depend on it :

- `/smith-provider-add`  — scaffolds a new provider following this layout.
- `/smith-provider-edit` — modifies an existing provider while preserving
  this layout.

Providers documented by Smith today : `claude-code`, `github-copilot`.
Each provider folder is a self-contained reference that explains how
its AI tool packages agents, skills, hooks, and rules — so any Smith
mutator (e.g. `/smith-bundle-add`) can read one file per kind and know
the exact frontmatter to emit.

## Canonical provider layout

Every provider folder MUST follow this layout :

```
cli/providers/<slug>/
├── RULES.MD                          # ROUTER — provider-level overview
├── rule-agent.MD                     # per-kind doc : how this provider models sub-agents
├── rule-skill.MD                     # per-kind doc : how this provider models slash commands / skills
├── rule-hook.MD                      # per-kind doc : how this provider models event hooks (may be "N/A" for some)
├── rule-rules.MD                     # per-kind doc : how this provider models project-wide instructions
└── example/
    ├── example-agent.<ext>           # CONCRETE worked-out artefact (real frontmatter + body)
    ├── example-skill.<ext>           # CONCRETE worked-out skill / prompt file
    ├── example-hook.<ext>            # CONCRETE worked-out hook fragment (or task fragment for hookless providers)
    └── example-rules.<ext>           # CONCRETE worked-out rules artefact
```

The 4 example file extensions depend on the provider :
- Claude Code : `.md`, `.md`, `.json`, `.md`.
- GitHub Copilot : `.agent.md`, `.prompt.md`, `-tasks.json`,
  `.instructions.md`.

## `RULES.MD` — the router

Provider-level overview, NOT a per-kind doc. Required sections :

| Section | Purpose |
|---|---|
| **Artefact map** | Table : `kind | rule file | consumer-project path | invocation`. |
| **Discovery + precedence** | Where the provider looks for artefacts, in what order. |
| **Cross-kind interactions** | How skills dispatch agents, how hooks fire on events, etc. |
| **Gaps vs Claude Code** | Comparison table for non-Claude-Code providers — features missing / replaced. |
| **When to pick which kind** | Decision matrix for authors choosing between skill / agent / hook / rules. |

Bullet list links to the four sources of truth on the web for the
provider (sub-agents doc, skills doc, hooks doc, rules doc).

## `rule-<kind>.MD` — per-kind doc

One per artefact kind (agent / skill / hook / rules). MUST start with
YAML frontmatter :

| Field      | Required | Meaning |
|---|:---:|---|
| `kind`     | yes      | One of `agent`, `skill`, `hook`, `rules`. Matches the filename. |
| `provider` | yes      | Provider slug (matches the parent dir name). |
| `title`    | yes      | Human-readable title (used in the dashboard / listings). |
| `path`     | yes      | Where this kind lives in a consumer project (e.g. `.claude/agents/<slug>.md`). |
| `example`  | yes      | Relative path to the companion file under `example/`. |

After the frontmatter, the body must cover :
- File path & discovery (where consumers put this kind).
- Frontmatter spec — every supported field (name, required y/n,
  default, allowed values, meaning).
- Body conventions.
- Cross-kind interactions (only if relevant to this kind).
- A `## Skeleton` section with a fill-in-the-blank example fenced
  block (NOT a complete artefact — the worked-out one lives in
  `example/`).

## `example/example-<kind>.<ext>` — worked-out examples

The companion file referenced by the rule file's `example:` frontmatter.
A FULLY functional artefact a user could drop into a real project, not
a skeleton. Showcases :
- Real frontmatter (every relevant field filled with realistic values).
- Realistic body that demonstrates the kind's idiomatic usage.
- Comments / `<!-- -->` blocks explaining non-obvious choices.

## Cross-references

- Every `rule-<kind>.MD` MUST reference its companion `example/` file
  via the `example:` frontmatter field.
- Every `rule-<kind>.MD` SHOULD reference the other rule files in
  prose when interactions are relevant (e.g. `rule-skill.MD` mentions
  `rule-hook.MD` when documenting `hooks:` frontmatter on a skill).
- `RULES.MD` MUST reference all 4 rule-*.MD files in its artefact-map
  table.

## Discovery

Providers are discovered by **directory walking** under
`cli/providers/`. There is **no `cli/providers/config.json`** — the
filesystem is the truth. To list providers, walk the directory and
read each `<slug>/RULES.MD` for the metadata.

## Mutator contract

Any Smith skill that creates or modifies a provider folder MUST :

1. **Read this skill** to know the canonical layout.
2. **Preserve unknown frontmatter keys** in any rule file — round-trip
   anything the current code doesn't recognise.
3. **Keep the 5-file core** (`RULES.MD` + 4 `rule-*.MD`) intact.
   Adding a 5th rule kind (e.g. `rule-mcp.MD`) is allowed but counts
   as an extension and SHOULD be documented in `RULES.MD`'s
   artefact-map table.
4. **Keep every `example/example-<kind>.<ext>` in sync** with its
   companion rule file — if a rule's `path:` or `example:` changes,
   the example file must move accordingly.
5. **NEVER write a provider-level index** at `cli/providers/config.json`
   — providers are filesystem-discovered. Mutators that look for "the
   list of providers" must walk the directory.
