# Smith CLI

A provider-agnostic command set for **bootstrapping AI agent surfaces
in any project**. Smith stands up a complete, project-tailored AI
workspace in one command : interactive stack discovery, auto-installed
bundles (`mvn`, `npm`, `pip`, `ia-stats`, …), per-framework skill
templates adapted to the consumer's exact versions, an always-on
`AGENTS.md` brief, a verified metadata layer under `.smith/`, then
the actual source tree scaffold — all in one agentic workflow.

Ships per-provider releases (`claude-code` / `github-copilot` /
`opencode`) built ahead of time by `/smith-build`. The consumer-side
skills + agents are **identical across providers** ; everything that
depends on the provider lives in the release tree itself
(`<release>/.smith/paths.yaml`).

No server. No database. Markdown files + a couple of zero-dependency
Node.js scripts where automation is needed. No Python in the consumer
project. No `npm install`, no `package.json` requirement.

## Quick start

```
cd <your-project>                       # where you want Smith to land
# Drop a release tree (claude-code / github-copilot / opencode) into
# your project — typically via clone, submodule, or release archive.
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
5. Template installs — filter the release catalogue by stack frameworks
   + dispatch one `smith-single-template-adapter` per kept template
   skill (placeholder resolution + stack-aware pruning, parallel).
6. Writes `AGENTS.md` at the project root (project-focused, ≤100 lines).
7. Verifier sub-agent (structural checks).
8. **Scaffold the source tree** — runs each framework's `bootstrap`
   skill via a coordinator sub-agent (zero interactive questions —
   defaults + hints from Step 2 cover every Phase 0 prompt).
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
│   │   ├── config.json          ← catalogue (filtered for this provider, no `providers` field)
│   │   └── <bundle>/
│   │       ├── config.yaml      ← bundle metadata (no `providers` field)
│   │       ├── skills/<slug>/SKILL.md   ← real skill, frontmatter included
│   │       └── hooks/...                ← flat hook files for this release
│   └── templates/
│       ├── index.json           ← catalogue
│       └── <framework>/<version>/
│           ├── config.yaml
│           └── skills/<slug>/SKILL.md   ← real skill ; body still has {{placeholder}} +
│                                          stack-gated sections (consumer-side adapter
│                                          resolves them at Step 5)
└── .claude/                     ← provider runtime root (claude-code release)
    ├── skills/                  ← 12 Smith skills (smith-init, smith-new-project, …)
    └── agents/                  ← 8 Smith sub-agents
```

For `github-copilot` releases the runtime root is `.github/` with
`prompts/` (skills) + `agents/`. For `opencode` it's `.opencode/`
with `commands/` (skills) + `agents/`. Bundle + template trees are
structurally identical across providers — only the assembled SKILL.md
frontmatter differs.

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

### Consumer-facing (shipped under `cli/bin/skills/`)

| Command | Pre-marker required ? | What it does |
|---|:---:|---|
| `/smith-new-project "<description>"` | no — it runs `/smith-init` if needed | **The recommended entry point.** 9-step agentic workflow taking a one-line description and ending with a runnable Smith-managed project (configs + bundles + adapted skills + AGENTS.md + scaffold + report). Reads `<release>/.smith/paths.yaml` for install paths ; provider-agnostic body. |
| `/smith-init` | no — it IS the marker | Minimal init : creates `.smith/smith.yaml`. Does NOT write configs, AGENTS.md, or run discovery. Use `/smith-new-project` for the full pipeline. |
| `/smith-help` | no | Reference — auto-loads on Smith questions. |
| `/smith-generate-docs` | yes | Writes `.smith/FUNCTIONAL_SPECIFICATION.MD` + `TECHNICAL_SPECIFICATION.MD` from architecture.json. Dispatches two doc-writer agents in parallel. |
| `/smith-dashboard` | yes | Renders `.smith/dashboard.html` from `architecture.json` + `config.json`. |
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
| `/smith-build [--provider <slug>] [--clean]` | **Deterministic Python script** (`build.py` sibling). Walks `cli/bin/`, `cli/bundles/`, `cli/templates/`, `cli/providers/` and produces one runnable release per provider under `cli/releases/<provider>/`. Resolves frontmatter + inlines `@smith-include` directives at build time. Writes `<release>/.smith/paths.yaml` + `<release>/.smith/release.yaml`. |
| `/smith-bundle-add <name> "<desc>" --tag t1,t2 [--ia provider]` | Scaffold a new bundle. Validates tags against the canonical taxonomy. Regenerates `bundles/config.json`. |
| `/smith-bundle-edit <name> [--add-skill ...] [...]` | Modify an existing bundle. |
| `/smith-provider-add <slug> "<desc>"` | Scaffold a new AI provider format set under `cli/providers/<slug>/`. |
| `/smith-provider-edit <slug> [...]` | Modify an existing provider format set. |
| `/smith-template-add --framework <name> --version <ver> "<desc>"` | Scaffold a new framework/version template set. Regenerates `cli/templates/index.json`. |
| `smith-bundle-format` / `smith-provider-format` | Auto-loaded format specs for maintainer skills. |

All `/smith-*` commands except `/smith-init`, `/smith-new-project` and
`/smith-help` check for the `.smith/smith.yaml` marker at the project
root and refuse to run if it is missing.

## Sub-agents shipped (`cli/bin/agents/`)

Driven by `/smith-new-project` and `/smith-generate-docs` — not invoked
by users directly. Each agent ships in split-folder layout (`<slug>.md`
body + `metadata.yml`) ; no per-provider frontmatter overrides — model
+ tool selection inherit from the running provider's defaults.

| Agent | Used by |
|---|---|
| `smith-stack-discoverer`                | `/smith-new-project` Step 2 (interactive Q&A, ≤2 rounds, ≤6 questions) |
| `smith-single-template-adapter`         | `/smith-new-project` Step 5 (one per template skill, parallel ; preserves frontmatter, rewrites body) |
| `smith-new-project-agents-writer`       | `/smith-new-project` Step 6 (assembles payload + invokes `/smith-agents-md-write`) |
| `smith-new-project-verifier`            | `/smith-new-project` Step 7 (structural checks) |
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
    │   ├── config.json           # catalogue, written by /smith-bundle-add
    │   ├── ia-stats/ | mvn/ | npm/ | pip/
    │   └── <bundle>/
    │       ├── config.yaml
    │       ├── skills/<slug>/    # body + metadata.yml + <provider>.yml
    │       └── hooks/<provider>/...
    ├── templates/                # per framework/version skill template sets
    │   ├── index.json            # catalogue, written by /smith-template-add
    │   └── <framework>/<version>/
    │       ├── config.yaml
    │       └── skills/<slug>/    # template.md + metadata.yml + <provider>.yml
    ├── providers/                # per-AI-tool format reference
    │   ├── claude-code/          # format-{skill,agent,hook}.yaml + provider.yaml + example/
    │   ├── github-copilot/
    │   ├── opencode/
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

| Framework | Version | What it gives you |
|---|---|---|
| `angular`          | `21` | 6 skill bodies — bootstrap (interactive scaffold), coding standards, tests + coverage (Vitest), design system (Tailwind v4), i18n (Transloco), HTTP client layer from OpenAPI. Adapter prunes optional techs (Tailwind, Transloco, OpenAPI) when absent from the project stack. |
| `java-spring-boot` | `4`  | 1 bootstrap skill — interactive scaffold (`pom.xml`, application entry, optional REST controller, optional Liquibase changelog, `application.yaml`). `mvn -B verify` smoke check at the end. |

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

Each `cli/providers/<slug>/` ships 4 format YAMLs (`provider.yaml` +
`format-skill.yaml` + `format-agent.yaml` + `format-hook.yaml`) + a
3-file `example/` directory + JSON-schema validation under
`cli/providers/specs/`.

## Conventions

- **Provider-agnostic skills + agents.** Every artefact under
  `cli/bin/skills/` and `cli/bin/agents/` is identical regardless of
  the provider it ends up running on. Provider-specific knowledge is
  baked into the release tree by `/smith-build`.
- **Split-folder layout.** Agents and bundle / template skills follow
  a canonical 3-file shape : `<slug>.md` body + `metadata.yml` (common
  name + description) + `<provider>.yml` (per-provider frontmatter
  overrides ; may be empty). `/smith-build` composes the final
  frontmatter from those files.
- **Indexes.** `bundles/config.json` and `templates/index.json` are
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
- **OpenCode provider** — third supported AI tool alongside Claude Code
  and GitHub Copilot.
- **Deterministic `/smith-build`** — Python script (`build.py`) walks
  the source tree and writes provider releases in milliseconds. No
  LLM reasoning at build time.

## Detailed reference

Each kind of artefact (skills, agents, hooks, providers) has
comprehensive documentation in its template under
`cli/providers/<provider>/`. Each format YAML lists every supported
frontmatter field with type, default, allowed values, and meaning.

For interactive exploration : run `/smith-help` in your AI tool — it
auto-loads on Smith-related questions and indexes everything above.

## Status

v0.1 — first release. See `PLAN.md` for the rolling plan and open
questions.
