# Smith CLI

A provider-agnostic command set for **bootstrapping AI agent surfaces
in any project**. Smith stands up a complete, project-tailored AI
workspace in one command : interactive stack discovery, auto-installed
bundles (`mvn`, `npm`, `pip`, `ia-stats`, …), per-framework skill
templates adapted to the consumer's exact versions, an always-on
`AGENTS.md` brief, a verified metadata layer under `.smith/`, then
the actual source tree scaffold — all in one agentic workflow.

Ships per-provider releases (`claude-code` / `github-copilot` /
`opencode` / `gemini-cli`) built ahead of time by `/smith-build`. The
consumer-side skills + agents are **identical across providers** ;
everything that depends on the provider lives in the release tree
itself (`<release>/.smith/paths.yaml`).

No server. No database. Markdown files + a couple of zero-dependency
Node.js scripts where automation is needed. No Python in the consumer
project. No `npm install`, no `package.json` requirement.

## Quick start

```
cd <your-project>                       # where you want Smith to land
# Drop a release tree (claude-code / github-copilot / opencode /
# gemini-cli) into your project — typically via clone, submodule, or
# release archive.
# Then, in your AI tool of choice :
/smith-new-project "<one-line description of the project>"
```

`/smith-new-project` runs a **9-step agentic workflow** end-to-end :

1. `/smith-init` (idempotent — writes `.smith/smith.yaml`).
2. Stack discovery (interactive — asks only the structuring questions
   not pinned down by your description).
3. Writes `.smith/architecture.json` + `.smith/config.json`.
4. Bundle installs — filter the release catalogue by stack tags + copy
   pre-built bundle artefacts into the consumer's provider-native
   skill / hook paths.
5. **Framework template installs** — read
   `<release>/.smith/templates/framework/index.yaml`, filter by stack
   frameworks, dispatch one `smith-single-template-adapter` per kept
   skill (placeholder resolution + stack-aware pruning, parallel).
   Adds N quality / convention skills to the consumer (standards,
   tests-coverage, design-system, i18n, …) — no execution.
6. Writes `AGENTS.md` at the project root (project-focused, ≤100 lines).
7. Verifier sub-agent (structural checks).
8. **Bootstrap templates : install + scaffold the source tree.**
   - 8.a — Read `<release>/.smith/templates/bootstrap/index.yaml`,
     pick `(name, version)` matching the project's frameworks. For
     each, adapt + install the singleton skill, copy `assets/` +
     `templates/` + `scripts/` sidecars under
     `<consumer>/.smith/bootstraps/<name>/`.
   - 8.b — Dispatch `smith-new-project-scaffold-coordinator` which
     runs every installed `smith-<name>-bootstrap` skill (zero
     interactive questions — defaults + hints from Step 2 cover every
     Phase 0 prompt).
9. Writes the single run report at `.smith/report.md`.

For a minimal init (marker only, no workflow) :

```
/smith-init
```

This just creates `.smith/smith.yaml` (datetime + provider + `enabled`).
Every other `/smith-*` skill checks for this marker before running.

Need help ? Run `/smith-help` — it auto-loads on any Smith question.

## Release model

Smith ships releases as **drop-in trees per AI provider**, produced by
`/smith-build`. The build resolves every provider-specific concern
(consumer install paths, frontmatter format, hook conventions) ahead
of time, so the consumer-side skills + agents are byte-identical
across providers.

```
<release>/
├── .smith/
│   ├── paths.yaml               ← consumer-side install paths (resolved)
│   ├── release.yaml             ← build manifest
│   ├── bundles/
│   │   ├── index.yaml           ← catalogue (filtered for this provider, no `providers` field)
│   │   └── <bundle>/
│   │       ├── config.yaml      ← bundle metadata (no `providers` field)
│   │       ├── skills/<slug>/SKILL.md   ← real skill, frontmatter included
│   │       └── hooks/...                ← flat hook files for this release
│   └── templates/
│       ├── framework/                          ← category : N skills per (name, version)
│       │   ├── index.yaml
│       │   └── <name>/<version>/
│       │       ├── config.yaml
│       │       └── skills/<installed-name>/SKILL.md   ← dir = metadata.yml::name
│       │                                              ; body still has {{placeholder}} +
│       │                                              stack-gated sections
│       └── bootstrap/                          ← category : exactly 1 skill + sidecars
│           ├── index.yaml
│           └── <name>/<version>/
│               ├── config.yaml
│               ├── skill/<installed-name>/SKILL.md    ← dir = metadata.yml::name
│               ├── assets/...                         ← optional, copied verbatim
│               ├── templates/...                      ← optional, real templates (HTML, …)
│               └── scripts/...                        ← optional, helper scripts
└── .claude/                     ← provider runtime root (claude-code release)
    ├── skills/                  ← 12 Smith skills (smith-init, smith-new-project, …)
    └── agents/                  ← 8 Smith sub-agents
```

For `github-copilot` releases the runtime root is `.github/` with
`prompts/` (skills) + `agents/`. For `opencode` it's `.opencode/`
with `commands/` (skills) + `agents/`. For `gemini-cli` it's
`.gemini/` with `skills/<slug>/SKILL.md` + `agents/`. Bundle + template
trees are structurally identical across providers — only the assembled
SKILL.md frontmatter differs.

`.smith/paths.yaml` is the **single source of truth** for consumer-side
install paths used by `/smith-new-project` and its sub-agents :

```yaml
skill:    ".claude/skills/{slug}/SKILL.md"          # claude-code example
agent:    ".claude/agents/{slug}.md"
hook_dir: ".claude/hooks/{bundle}"
settings: ".claude/settings.json"                    # null for providers without a merge model
```

## What lands in the consumer project

Under `.smith/` :
- `smith.yaml` — init marker (provider + enabled flag).
- `architecture.json` — **what the project IS**. Detected languages,
  runtimes, frameworks, build / test / infra / database tools, each
  with `name`, `version`, `tags`. Spec : `smith-architecture-format`.
- `config.json` — **what Smith DID**. Provider, spec paths, adapted
  skills, installed bundles (with `files[]` and `merged_into[]`).
  Spec : `smith-config-format`.
- `FUNCTIONAL_SPECIFICATION.MD` — what the system does (PO / QA).
- `TECHNICAL_SPECIFICATION.MD` — architecture for a senior engineer.
- `report.md` — single run report (overwritten on every workflow run —
  no per-run numbering, git is the history).

At the project root :
- `AGENTS.md` — project-focused brief (≤100 lines) loaded by Claude
  Code / Copilot / OpenCode on every turn. No Smith branding inside.

Under the provider runtime root (`.claude/` / `.github/` /
`.opencode/`) :
- `skills/` (or `prompts/` / `commands/`) — adapted framework skills +
  installed bundle skills.
- `agents/` — Smith + bundle sub-agents.
- `hooks/` — bundle hook scripts (claude-code only ; settings
  fragments are auto-merged into the provider's live config with a
  `_smith_source` marker).

## Slash commands

### Consumer-facing (shipped under `bin/skills/`)

| Command | Pre-marker required ? | What it does |
|---|:---:|---|
| `/smith-new-project "<description>"` | no — it runs `/smith-init` if needed | **The recommended entry point.** 9-step agentic workflow taking a one-line description and ending with a runnable Smith-managed project (configs + bundles + adapted skills + AGENTS.md + scaffold + report). Reads `<release>/.smith/paths.yaml` for install paths ; provider-agnostic body. |
| `/smith-init` | no — it IS the marker | Minimal init : creates `.smith/smith.yaml`. Does NOT write configs, AGENTS.md, or run discovery. Use `/smith-new-project` for the full pipeline. |
| `/smith-help` | no | Reference — auto-loads on Smith questions. |
| `/smith-generate-docs` | yes | Writes `.smith/FUNCTIONAL_SPECIFICATION.MD` + `TECHNICAL_SPECIFICATION.MD` from architecture.json. Dispatches two doc-writer agents in parallel. |
| `/dashboard-ai` | yes | **Optional bundle.** Builds `.smith/dashboard.json` from `architecture.json` + `config.json` + every installed skill/agent (invocation command resolved per the active provider), then launches a zero-deps Node + React-via-CDN web UI. Install via `/smith-bundle-install --name dashboard-ai`. |
| `/smith-bundle-list [--tag X[,Y]]` | yes | Lists the release bundle catalogue, optionally filtered (intersection). |
| `/smith-bundle-install --name X [--consumer-dir <abs>]` | yes | Installs a single bundle from the release tree into the consumer project. Auto-merges hook fragments into the provider's settings file with `_smith_source` marker. Normally driven by `/smith-new-project` ; rarely invoked manually. |
| `/smith-template-install --framework <name> [--version <ver>] [--consumer-dir <abs>]` | yes | Installs + adapts a framework template set. Stack-aware pruning removes mentions of techs not in `architecture.json`. |

### Orchestrator-internal (callable but normally driven by `/smith-new-project`)

| Command | What it does |
|---|---|
| `/smith-agents-md-write --payload <json>` | Writes `AGENTS.md` from a structured payload. Single canonical writer for the brief. Idempotent (skip if present). |
| `/smith-report-write --payload <json>` | Writes `.smith/report.md` ; overwritten on every run, no per-run numbering. |

### Auto-loaded format specs (`user-invocable: false`)

| Skill | Documents |
|---|---|
| `smith-architecture-format` | `.smith/architecture.json` shape + tag taxonomy. |
| `smith-config-format` | `.smith/config.json` shape + `bundles[]` / `skills[]` entry shapes + `_smith_source` merge marker. |

### CLI-maintainer (under `.claude/skills/` at the workspace root — NOT shipped in releases)

| Command | What it does |
|---|---|
| `/smith-build [--provider <slug>] [--clean]` | **Deterministic Python script** (`build.py` sibling). Walks `bin/`, `bundles/`, `templates/`, `providers/` and produces one runnable release per provider under `releases/<provider>/`. Resolves frontmatter + inlines `@smith-include` directives at build time. Writes `<release>/.smith/paths.yaml` + `<release>/.smith/release.yaml`. |
| `/smith-bundle-add <name> "<desc>" --tag t1,t2 [--ia provider]` | Scaffold a new bundle. Validates tags against the canonical taxonomy. Regenerates `bundles/index.yaml`. |
| `/smith-bundle-edit <name> [--add-skill ...] [...]` | Modify an existing bundle. |
| `/smith-provider-add <slug> "<desc>"` | Scaffold a new AI provider format set under `providers/<slug>/`. |
| `/smith-provider-edit <slug> [...]` | Modify an existing provider format set. |
| `/smith-template-add --framework <name> --version <ver> "<desc>"` | Scaffold a new framework/version template set. Regenerates `templates/index.yaml`. |
| `smith-bundle-format` / `smith-provider-format` | Auto-loaded format specs for maintainer skills. |

All `/smith-*` commands except `/smith-init`, `/smith-new-project` and
`/smith-help` check for the `.smith/smith.yaml` marker at the project
root and refuse to run if it is missing.

## Sub-agents shipped (`bin/agents/`)

Driven by `/smith-new-project` and `/smith-generate-docs` — not invoked
by users directly. Each agent ships in split-folder layout (`<slug>.md`
body + `metadata.yml`) ; no per-provider frontmatter overrides — model
+ tool selection inherit from the running provider's defaults.

| Agent | Used by |
|---|---|
| `smith-stack-discoverer`                | `/smith-new-project` Step 2 (interactive Q&A, ≤2 rounds, ≤6 questions) |
| `smith-single-template-adapter`         | `/smith-new-project` Step 5 (one per template skill, parallel ; preserves frontmatter, rewrites body) |
| `smith-project-agents-writer`           | `/smith-new-project` Step 6 + `/smith-convert-project` (assembles payload + invokes `/smith-agents-md-write`) |
| `smith-project-verifier`                | `/smith-new-project` Step 7 + `/smith-convert-project` (structural checks) |
| `smith-new-project-scaffold-coordinator`| `/smith-new-project` Step 8 (conflict guard + dispatches bootstrappers) |
| `smith-new-project-bootstrapper`        | scaffold-coordinator (one per framework, parallel ; runs the framework's `bootstrap` skill) |
| `smith-functional-doc-writer`           | `/smith-generate-docs` |
| `smith-technical-doc-writer`            | `/smith-generate-docs` |

All sub-agents are **provider-agnostic** : they never branch on the
provider name, and they read consumer-side install paths from
`<release>/.smith/paths.yaml` when they need to write to the
filesystem.

## Layout (CLI repo)

```
smith-cli/                        # workspace root
├── README.MD                     # this file
├── .claude/                      # CLI-MAINTAINER surface (NOT shipped in releases)
│   └── skills/                   # /smith-build, /smith-bundle-{add,edit,format},
│                                 # /smith-provider-{add,edit,format}, /smith-template-add
└── cli/
    ├── bin/                      # SHIPPABLE surface — packaged into releases
    │   ├── skills/               # 12 consumer skills (see "Slash commands")
    │   └── agents/               # 8 sub-agents in split-folder layout
    ├── bundles/                  # opt-in libraries
    │   ├── index.yaml            # catalogue, written by /smith-bundle-add
    │   ├── ia-stats/ | mvn/ | npm/ | pip/
    │   └── <bundle>/
    │       ├── config.yaml
    │       ├── skills/<slug>/    # body + metadata.yml (generic props ; mapped at build time)
    │       └── hooks/<provider>/...
    ├── templates/                # skill template sets, split by category
    │   ├── framework/            # N skills per (name, version) — quality / conventions
    │   │   ├── index.yaml        # per-category catalogue, written by /smith-template-add
    │   │   └── <name>/<version>/
    │   │       ├── config.yaml
    │   │       ├── README.md + CHANGELOG.md
    │   │       └── skills/<slug>/    # <slug>.md body + metadata.yml (generic props)
    │   └── bootstrap/            # exactly 1 skill per (name, version) — scaffolders
    │       ├── index.yaml
    │       └── <name>/<version>/
    │           ├── config.yaml
    │           ├── README.md + CHANGELOG.md
    │           ├── skill/<slug>.md + metadata.yml
    │           ├── assets/...    # optional, verbatim files for the scaffold
    │           ├── templates/... # optional, real templates with placeholders
    │           └── scripts/...   # optional, helper scripts
    ├── providers/                # per-AI-tool format reference
    │   ├── claude-code/          # format-{skill,agent,hook}.yaml + provider.yaml + example/
    │   ├── github-copilot/
    │   ├── opencode/
    │   ├── gemini-cli/
    │   └── specs/                # JSON Schemas validating every provider folder
    ├── releases/                 # output of /smith-build
    │   └── <provider>/           # drop-in release tree (see "Release model")
    └── samples/                  # showcase consumer projects (angular-app, acme-todo)
```

## Bundles shipped (v0.1)

| Bundle | Tags | What it gives you |
|---|---|---|
| `ia-stats` | `observability`, `hooks` | Automatic `IA_STATS.MD` tracker. Two Claude Code hooks (`SubagentStop`, `PostToolUse`) auto-merged into `.claude/settings.json`. OpenCode plugin variant. GitHub Copilot ships the read-only `/ia-stats` skill only (VS Code tasks cannot carry per-event payloads). Cross-platform Node.js script, zero dependencies. |
| `mvn`      | `build`, `java`, `backend` | `/mvn <goals>` slash command. Runs Maven and returns a one-line verdict + test counters + failure cause. Keeps the parent context clean. |
| `npm`      | `build`, `nodejs`, `frontend` | `/npm <args>` slash command. Same offload pattern for the project's Node tooling. |
| `pip`      | `build`, `python`, `python3` | `/pip <args>` slash command. Same offload pattern for Python projects. |

`/smith-new-project` selects matching bundles automatically by tag.

## Templates shipped (v0.1)

### `framework/` category — quality + conventions

Installed at Step 5 of `/smith-new-project` ; not executed. Each
(name, version) ships N skills the AI uses later.

| Framework | Version | Skills |
|---|---|---|
| `angular`          | `21` | 5 skills — coding standards, tests + coverage (Vitest), design system (Tailwind v4), i18n (Transloco), HTTP client layer from OpenAPI. Adapter prunes optional techs (Tailwind, Transloco, OpenAPI) when absent from the project stack. |
| `python`           | `3`  | 5 language-level skills — standards, tests + coverage, typing (mypy), packaging (PEP 621 / pyproject), linting (ruff). Apply to any Python 3.12+ project regardless of downstream web framework. |
| `django`           | `5`  | 4 skills — standards, ORM patterns, tests (pytest-django), Django REST Framework. Pairs with `framework/python/3` for language-level conventions. |
| `fastapi`          | `0`  | 4 skills — standards, Pydantic schemas, async patterns (SQLAlchemy ext.asyncio), JWT auth. Pairs with `framework/python/3`. |
| `java-spring-boot` | `4`  | 1 skill — bootstrap (interactive scaffold). To migrate to the `bootstrap/` category in a follow-up. |

### `bootstrap/` category — scaffolders

Installed AND executed at Step 8 of `/smith-new-project`. Each
(name, version) ships **exactly 1 skill** + optional `assets/` +
`templates/` + `scripts/` sidecars.

| Name         | Version | What it does |
|---|---|---|
| `angular`    | `21`    | Interactive scaffold of a new Angular 21 SPA — package, routing, optional Tailwind v4 / Transloco / OpenAPI ; runs `npm run build` as a smoke check. |
| `fastapi`    | `0`     | Interactive scaffold of a new FastAPI 0.115+ service — package, database (none / sqlite / postgres), auth (none / JWT), optional Docker + GitHub Actions CI ; runs `uv sync` + `uv run pytest` as a smoke check. |
| `python-lib` | `1`     | Interactive scaffold of a new pip-installable Python library — package, license, PEP 561 `py.typed` marker, CI provider ; generates pyproject.toml (PEP 621 + hatchling) + src/ layout + tests + CHANGELOG + LICENSE. Runs `uv sync` + `uv run pytest` as a smoke check. |

Templates ship as real skills (frontmatter composed at build time).
The release-side body still carries `{{placeholder}}` markers and
stack-gated sections ; `smith-single-template-adapter` resolves them
at consumer-install time against the project's stack.

## Providers shipped (v0.1)

| Provider | Runtime root | Skills path | Agents path |
|---|---|---|---|
| `claude-code`    | `.claude/`    | `skills/<slug>/SKILL.md`        | `agents/<slug>.md`         |
| `github-copilot` | `.github/`    | `prompts/<slug>.prompt.md`      | `agents/<slug>.agent.md`   |
| `opencode`       | `.opencode/`  | `commands/<slug>.md`            | `agents/<slug>.md`         |
| `gemini-cli`     | `.gemini/`    | `skills/<slug>/SKILL.md`        | `agents/<slug>.md`         |

Each `providers/<slug>/` ships 4 format YAMLs (`provider.yaml` +
`format-skill.yaml` + `format-agent.yaml` + `format-hook.yaml`) + a
3-file `example/` directory + JSON-schema validation under
`providers/specs/`.

## Conventions

- **Provider-agnostic skills + agents.** Every artefact under
  `bin/skills/` and `bin/agents/` is identical regardless of
  the provider it ends up running on. Provider-specific knowledge is
  baked into the release tree by `/smith-build`.
- **Split-folder layout.** Agents and bundle / template skills follow
  a canonical 2-file shape : `<slug>.md` body + `metadata.yml`
  (generic, provider-agnostic). For agents, generic capabilities
  (`read`, `glob`, `ask-user`, …) are mapped to provider-native tools
  via `provider.yaml::build.capability_map`. For bundle / template
  skills, generic properties (`model`, `user-invocable`) are mapped
  to provider-native frontmatter keys via
  `provider.yaml::build.skill_property_map`. Properties unsupported
  by a given provider are silently dropped at build time.
- **Indexes.** `bundles/index.yaml` and `templates/index.yaml` are
  regenerated from disk by `/smith-bundle-add` / `/smith-template-add`.
  Never patched by hand. The release-side copies are filtered to
  whatever was built for the target provider, with the `providers:`
  field dropped.
- **Idempotency.** Every `/smith-*` install / write skill is safe to
  re-run : files copied or written are not overwritten unless flagged,
  hooks merges are scoped by `_smith_source`, config upserts are keyed
  by name.
- **Zero install in consumer projects.** Adapted skills are markdown.
  The only Smith-managed runtime script is `ia-stats`' `.js` running
  on Node stdlib — no `package.json` required, no `npm install`, no
  transitive dependencies.
- **Single-file run report.** `.smith/report.md` is overwritten by
  every workflow run. Older runs are not preserved (use git).

## Recent updates

- **Release-tree model.** Every artefact for a project bootstrap is
  pre-built at release time. `/smith-new-project` no longer resolves
  `@smith-include` directives or composes frontmatter at consumer time
  ; it reads `<release>/.smith/paths.yaml` and copies / adapts files
  straight from the release tree.
- **Provider-agnostic skill + agent bodies.** No more branching on
  `claude-code` / `github-copilot` / `opencode` inside any consumer-
  side skill. The 3 obsolete planner agents (bundle-installer,
  template-installer, template-customizer) are removed.
- **Gemini CLI provider** — fourth supported AI tool. Runtime root
  `.gemini/`, skills under `.gemini/skills/<slug>/SKILL.md`, hooks
  declared inside `.gemini/extensions/<slug>/extension.json` manifests.
- **OpenCode provider** — third supported AI tool alongside Claude Code
  and GitHub Copilot.
- **Python template line-up.** `framework/python/3` (5 language-level
  skills) plus framework-specific sets `framework/django/5` and
  `framework/fastapi/0`, and two new bootstrap scaffolders
  `bootstrap/fastapi/0` (service) + `bootstrap/python-lib/1` (library,
  PEP 621 + hatchling).
- **Deterministic `/smith-build`** — Python script (`build.py`) walks
  the source tree and writes provider releases in milliseconds. No
  LLM reasoning at build time.
- **Two template categories** — `framework/` (N skills per (name,
  version), installed but not executed) and `bootstrap/` (exactly 1
  skill + optional assets / templates / scripts buckets, installed
  AND executed by Step 8 to scaffold the source tree). Per-category
  index.json under `templates/<category>/`. Iso-name rule applied
  at build time : every skill directory in the release matches the
  installed slug declared in `metadata.yml::name`.
- **Generic skill properties.** Bundle + template metadata.yml carry
  the provider-agnostic `model` and `user-invocable` properties. The
  build maps them to the provider's native frontmatter keys via
  `provider.yaml::build.skill_property_map` — unsupported on a
  provider → silently dropped.

## Detailed reference

Each kind of artefact (skills, agents, hooks, providers) has
comprehensive documentation in its template under
`providers/<provider>/`. Each format YAML lists every supported
frontmatter field with type, default, allowed values, and meaning.

For interactive exploration : run `/smith-help` in your AI tool — it
auto-loads on Smith-related questions and indexes everything above.

## Status

v0.1 — first release. See `PLAN.md` for the rolling plan and open
questions.
