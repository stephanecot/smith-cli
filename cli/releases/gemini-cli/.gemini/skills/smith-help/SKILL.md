---
name: smith-help
description: Reference for the Smith CLI consumer surface. Use this skill whenever the developer asks how Smith works, what `/smith-new-project` / `/smith-init` / `/smith-generate-docs` / `/smith-dashboard` / `/smith-bundle-list` do, what `.smith/architecture.json` + `.smith/config.json` + `.smith/smith.yaml` + `.smith/report.md` + `AGENTS.md` contain, what bundles + templates are, or how to get started. Covers ONLY the consumer-facing skills shipped under `cli/bin/skills/` — CLI-maintainer commands (`/smith-bundle-add`, `/smith-provider-add`, `/smith-template-add`, `/smith-build`, …) are out of scope. Auto-load on any question about Smith, smith-cli, smith bundles, smith templates, or `/smith-*` slash commands.
when_to_use: User says "how do I", "what does", "where is", "what is smith", "smith cli", "smith bundle", "smith template", "smith provider", or types any `/smith-*` slash command and asks what it does. Also fires when the user wants to discover what Smith can do, get an overview, or pick the right command for their goal.
---

# Smith CLI — quick reference

Smith CLI is a provider-agnostic command set for **bootstrapping AI
agent surfaces in any project**. The recommended entry point is
`/smith-new-project "<one-line description>"` — a 9-step agentic
workflow that takes a description and ends with a runnable
Smith-managed project (configs + bundles + adapted skills + AGENTS.md
+ source scaffold + report).

This skill is the canonical answer to "how do I use Smith". It
auto-loads on any Smith-related question.

## Mental model in 4 lines

1. **One command does it all.** `/smith-new-project "<desc>"` runs a
   9-step pipeline (init → discovery → configs → bundles →
   framework templates → AGENTS.md → verify → bootstrap scaffold →
   report) end-to-end.
2. **Release-tree model.** Every artefact is pre-built by
   `/smith-build` into `cli/releases/<provider>/`. The consumer-side
   skills + agents are byte-identical across providers ; everything
   provider-specific (install paths, frontmatter shape) lives in
   `<release>/.smith/paths.yaml`. No `@smith-include` resolution, no
   frontmatter composition at install time.
3. **Two template categories.** `framework/` ships N skills per
   (name, version) for project quality + conventions (standards,
   tests, design-system, i18n, …) ; `bootstrap/` ships exactly 1
   skill per (name, version) + optional `assets/` + `templates/` +
   `scripts/` sidecars and is the actual scaffolder that runs at
   Step 8.
4. **`.smith/smith.yaml` is the marker.** Every `/smith-*` command
   except `/smith-new-project`, `/smith-init` and `/smith-help`
   refuses to run if the marker is missing.

## Slash command map (8 user-invocable consumer commands)

| Command | Pre-marker required ? | Purpose |
|---|:---:|---|
| `/smith-new-project "<description>"` | no — runs `/smith-init` if needed | **The recommended entry point.** 9-step pipeline. Reads `<release>/.smith/paths.yaml` for the consumer-side install paths ; identical body across providers. |
| `/smith-init` | no — it IS the marker | Minimal init : creates `.smith/smith.yaml` (init datetime + provider + `enabled: true`). Does NOT write configs, AGENTS.md, or run discovery. Most users want `/smith-new-project` instead. |
| `/smith-help` | no | This skill. |
| `/smith-generate-docs` | yes | Writes `.smith/FUNCTIONAL_SPECIFICATION.MD` + `TECHNICAL_SPECIFICATION.MD` from `architecture.json`. Dispatches two doc-writer agents in parallel. |
| `/smith-dashboard` | yes | Renders `.smith/dashboard.html` from `architecture.json` + `config.json`. Read-only ; idempotent regeneration. |
| `/smith-bundle-list [--tag X[,Y]]` | yes | Read-only listing of `<release>/.smith/bundles/index.yaml`. Multiple `--tag` values are AND'd (intersection). |
| `/smith-bundle-install --name X [--consumer-dir <abs>]` | yes | Installs a single bundle from the release tree into the consumer project. Hooks fragments matching `*.hooks.json` merge into the provider's settings file (`_smith_source` marker for idempotent re-installs). Normally driven by `/smith-new-project`. |
| `/smith-template-install --framework <name> [--version <ver>] [--consumer-dir <abs>]` | yes | Installs a framework template set : filters skills by tag intersection with the project stack, dispatches `smith-single-template-adapter` per kept skill (placeholder resolution + stack-aware pruning). |

## Workflow detail — `/smith-new-project` 9 steps

1. **`/smith-init`** (conditional — skips if `.smith/smith.yaml`
   already exists).
2. **Stack discovery.** Sub-agent `smith-stack-discoverer` asks ≤ 2
   batched rounds of `AskUserQuestion` (≤ 6 questions total) to nail
   down framework / backend / database / build / test / infra
   anchors. Applies framework defaults for everything else and
   records them in `assumed_defaults[]`.
3. **Write `.smith/architecture.json` + `.smith/config.json`.**
   `architecture.json` = what the project IS (detected stack with
   kebab-case tags). `config.json` = what Smith DID (provider,
   installed bundles, adapted skills, spec paths).
4. **Bundle installs.** Read `<release>/.smith/bundles/index.yaml`,
   pick bundles whose `tags[]` intersect the project stack tags,
   copy `<bundle>/skills/<slug>/SKILL.md` + `hooks/...` into the
   consumer.
5. **Framework template installs.** Read
   `<release>/.smith/templates/framework/index.yaml`, pick (framework,
   version) matching the stack, filter each entry's `skills[]` by
   tag intersection, dispatch `smith-single-template-adapter` per
   kept skill in parallel (placeholders + stack-aware pruning), write
   adapted SKILL.md to the consumer.
6. **Write `AGENTS.md`** at the project root (≤ 100 lines,
   project-focused, no Smith branding).
7. **Verifier sub-agent.** Walks `.smith/` and confirms structural
   integrity. Failures surface in the run report but do NOT roll back.
8. **Bootstrap templates : install + scaffold the source.**
   - **8.a** : read
     `<release>/.smith/templates/bootstrap/index.yaml`, pick entries
     whose top-level `tags[]` intersect the project stack. For each,
     adapt + install the singleton skill, copy `assets/` / `templates/`
     / `scripts/` sidecars under
     `<consumer>/.smith/bootstraps/<name>/`.
   - **8.b** : dispatch `smith-new-project-scaffold-coordinator`,
     which runs every installed `smith-<name>-bootstrap` skill with
     zero interactive questions (defaults + hints from Step 2 cover
     every Phase 0 prompt).
9. **Write the single run report** at `.smith/report.md`
   (overwritten on every workflow run — no per-run history).

## Internal skills (called by orchestrators, rarely by hand)

| Skill | Purpose |
|---|---|
| `/smith-agents-md-write --payload <json>` | Writes `AGENTS.md`. Single canonical writer. Idempotent (skips if file exists). Enforces a 100-line cap. |
| `/smith-report-write --payload <json>`    | Writes the project's single `.smith/report.md`, overwritten on every run. |

## Auto-loaded format specs (`user-invocable: false`)

Format-only skills that auto-load when the assistant needs to know
the exact shape of a Smith file.

| Skill | Documents |
|---|---|
| `smith-architecture-format` | `.smith/architecture.json` — project identity (name + description + summary + detected stack with kebab-case `tags[]`). Includes the canonical tag taxonomy. |
| `smith-config-format`       | `.smith/config.json` — Smith state (provider + spec paths + adapted skills + installed bundles, with `_smith_source` merge marker). |

## What lands in the consumer project

Under `<consumer>/.smith/` (Smith metadata) :

| File | Created by |
|---|---|
| `smith.yaml`                  | `/smith-init` (delete to disable Smith on the project). |
| `architecture.json`           | `/smith-new-project` Step 3. |
| `config.json`                 | `/smith-new-project` Step 3 ; upserted by Steps 4 + 5 + 8.a. |
| `bootstraps/<name>/...`       | `/smith-new-project` Step 8.a (sidecar `assets` / `templates` / `scripts` from each installed bootstrap). |
| `FUNCTIONAL_SPECIFICATION.MD` | `/smith-generate-docs`. |
| `TECHNICAL_SPECIFICATION.MD`  | `/smith-generate-docs`. |
| `report.md`                   | `/smith-report-write` (overwritten each run). |

At the consumer project root :

| File | Created by | Notes |
|---|---|---|
| `AGENTS.md` | `/smith-agents-md-write` (driven by `/smith-new-project` Step 6) | Project-focused brief, ≤ 100 lines. Idempotent — skipped if already present. |

Under the provider runtime root (`<consumer>/.claude/` /
`.github/` / `.opencode/`) :

- `skills/` (or `prompts/` / `commands/`) — Smith bin skills +
  installed bundle / template skills.
- `agents/` — Smith sub-agents + installed bundle agents (when any).
- `hooks/<bundle>/` — bundle hook scripts (claude-code only ;
  settings fragments are auto-merged into the provider's live config
  with `_smith_source: <bundle>` marker).

## Template config shapes

### `framework/<name>/<version>/config.yaml`

```yaml
framework: <kebab>
version: "<ver>"
description: |
  Multi-line — what this template set covers.
skills:
  - name: <slug>
    version: 0.1.0
    tags: [<canonical-taxonomy-keywords>]   # required ; gates the install filter
adapter_placeholders:
  "{{language}}":          ...
  "{{framework}}":         ...
  "{{framework_version}}": ...
  ...
```

Each `skills/<slug>/` directory ships only 2 files : `<slug>.md`
(body, no frontmatter) + `metadata.yml` (generic `name` +
`description`, optional `model` + `user-invocable`). Provider-native
frontmatter is composed at release-build time. The consumer-side
adapter resolves `{{placeholder}}` markers and **prunes
absent-tech sections** against the project stack.

### `bootstrap/<name>/<version>/config.yaml`

```yaml
name: <kebab>
version: "<ver>"
description: |
  Multi-line — what this bootstrap scaffolds.
tags: [<canonical-taxonomy-keywords>]   # required ; gates the install filter
assets: []                              # files copied verbatim
templates: []                           # real templates with placeholders (HTML, …)
scripts: []                             # helper scripts
```

Exactly one skill under `skill/<slug>.md` + `metadata.yml`, plus the
3 optional sidecar buckets (`assets/`, `templates/`, `scripts/`).
The `skill/` directory implies the singleton — no per-skill `name`
inside `config.yaml`.

## Tag taxonomy

The canonical vocabulary used by **both bundles and templates** for
their `tags[]` lists :

- **role**     : `build`, `test`, `lint`, `format`, `deploy`, `observability`, `docs`, `scaffold`, `sdlc`, `release`, `security`.
- **language** : `java`, `kotlin`, `javascript`, `typescript`, `python`, `go`, `rust`, `csharp`, `ruby`, `php`, `shell`.
- **runtime**  : `jvm`, `nodejs`, `python3`, `dotnet`, `browser`.
- **tier**     : `frontend`, `backend`, `fullstack`, `infra`, `cli`, `library`.
- **integration** : `hooks`, `slash-command`, `mcp`.

Plus any framework / library name in kebab-case (`angular`,
`spring-boot`, `vitest`, `tailwindcss`, `transloco`, …) — these gate
fine-grained skills (e.g. an `i18n-transloco` skill carries
`tags: [transloco, i18n, frontend]` so it only installs when the
project actually uses Transloco).

Wire format is a flat `tags: [a, b, c]` list. Categories exist only
for authoring guidance.

## Where do I start ? (3 recipes)

### Recipe A — bootstrap a new project end-to-end (the usual flow)

```
cd <consumer-project>
/smith-new-project "<one-line description>"
# Runs the 9-step workflow. Reads .smith/paths.yaml from the release
# this skill ships inside. When done, .smith/report.md tells you
# what was installed + scaffolded.
```

### Recipe B — add one bundle on a Smith-managed project

```
# already inside an init'd project (.smith/smith.yaml present)
/smith-bundle-list --tag build
/smith-bundle-install --name mvn
# Copies the bundle's skill + hooks, auto-merges any hook fragment
# into the provider's settings file with _smith_source="mvn".
```

### Recipe C — auto agent / tool tracking (`IA_STATS.MD`)

```
/smith-bundle-install --name ia-stats
# Copies the /ia-stats skill + the Node-stdlib script,
# auto-merges the SubagentStop + PostToolUse hooks into the
# provider's settings file. After the first sub-agent dispatch or
# tool call, IA_STATS.MD appears at the project root.
```

## Pre-marker guard rail

Every `/smith-*` command except `/smith-new-project`, `/smith-init`
and `/smith-help` checks for `.smith/smith.yaml` at the consumer
project root and halts with a clear message if absent. Run
`/smith-new-project` or `/smith-init` first.

## What this skill does NOT do

- It does not execute any command for the user — it explains. If the
  user asks "run `/smith-bundle-list`", the assistant runs the
  corresponding skill, not this one.
- It does not list bundles or templates — that's `/smith-bundle-list`
  and the per-category `index.yaml` files in the release.
- It does not bootstrap a project — that's `/smith-new-project`.
- It does not cover CLI-maintainer commands (`/smith-bundle-add`,
  `/smith-provider-add`, `/smith-template-add`, `/smith-build`, …) —
  those live in the Smith CLI workspace and are out of scope.

## Reporting back

When the user asks an open question ("how does smith work ?"), reply
with the relevant section of this skill, NOT the entire body. Pick
the narrowest answer the question warrants, link to the relevant
slash command, and offer to run it if the user wants to act.
