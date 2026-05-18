# Smith CLI

A Claude Code-native command set for **bootstrapping AI agent surfaces in
any project**. Smith stands up a complete, project-tailored AI workspace
in one command : interactive stack discovery, auto-installed bundles
(`mvn`, `npm`, `ia-stats`, …), per-framework skill templates adapted to
the consumer's exact versions, an always-on `AGENTS.md` brief, a verified
metadata layer under `.smith/`, then the actual source tree scaffold —
all in one agentic workflow.

No server. No database. Markdown files + a couple of zero-dependency
Node.js scripts where automation is needed. No Python in the consumer
project. No `npm install`, no `package.json` requirement.

## Quick start

```
cd <your-project>                       # the project you want to agentify
# In Claude Code :
/smith-new-project "<one-line description of the project>"
```

`/smith-new-project` runs a **10-step agentic workflow** end-to-end :

1. `/smith-init` (idempotent — writes `.smith/smith.yaml`).
2. Stack discovery (interactive — asks only the structuring questions
   not pinned down by your description).
3. Writes `.smith/architecture.json` + `.smith/config.json`.
4. Bundle installs — one sub-agent per matching bundle, in parallel.
5. Template installs — one sub-agent per matching framework, in parallel.
6. Writes `AGENTS.md` at the project root (project-focused, ≤100 lines).
7. Refreshes `.smith/config.json`.
8. Verifier sub-agent (11 structural checks).
9. **Scaffold the source tree** — runs each framework's `bootstrap`
   skill via a coordinator sub-agent (no interactive questions during
   this step — defaults + hints from step 2 cover every Phase 0 prompt).
10. Writes the single run report at `.smith/report.md`.

For a minimal init (marker only, no workflow) :

```
/smith-init [--provider claude-code|github-copilot]
```

This just creates `.smith/smith.yaml` (datetime + provider + `enabled`).
Every other `/smith-*` skill checks for this marker before running.

Need help ? Run `/smith-help` — it auto-loads on any Smith question.

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
- `report.md` — **single** run report (overwritten on every workflow
  run — no per-run numbering, git is the history).

At the project root :
- `AGENTS.md` — project-focused brief (≤100 lines) loaded by Claude
  Code / Copilot on every turn. **No Smith branding inside** — talks
  about the project's stack and conventions, not about how it was
  generated.

Under `.claude/` (Claude Code) or `.github/` (Copilot) :
- `skills/` — adapted framework skills + installed bundle skills.
- `agents/` — installed bundle sub-agents.
- `scripts/` — Node-stdlib helper scripts shipped by bundles.
- `settings.json` — auto-merged hooks (Claude Code only). Smith-injected
  entries carry `_smith_source: "<bundle>"` so re-installs replace
  them in place without touching hand-written entries.

## Slash commands

### Consumer-facing (shipped under `cli/bin/skills/`)

| Command | Pre-marker required ? | What it does |
|---|:---:|---|
| `/smith-new-project "<description>"` | no — it runs `/smith-init` if needed | **The recommended entry point.** 10-step agentic workflow that takes a one-line description and ends with a runnable Smith-managed project (configs + bundles + adapted skills + AGENTS.md + scaffold + report). |
| `/smith-init [--provider claude-code\|github-copilot]` | no — it IS the marker | Minimal init : creates `.smith/smith.yaml`. Does NOT write configs, AGENTS.md, or run discovery. Use `/smith-new-project` for the full pipeline. |
| `/smith-help` | no | Reference — auto-loads on Smith questions. |
| `/smith-generate-docs` | yes | Writes `.smith/FUNCTIONAL_SPECIFICATION.MD` + `TECHNICAL_SPECIFICATION.MD` from architecture.json. Dispatches two doc-writer agents in parallel. |
| `/smith-dashboard` | yes | Renders `.smith/dashboard.html` from `architecture.json` + `config.json`. |
| `/smith-bundle-list [--tag X[,Y]]` | yes | Lists `cli/bundles/config.json`, optionally filtered (intersection). |
| `/smith-bundle-install --name X --ia <provider> [--consumer-dir <abs>] [--no-config-write]` | yes | Installs a bundle : copies files (resolving `@smith-include` directives via Read+Write — no `cp` for wrapper files), **auto-merges hooks into `.claude/settings.json`** with `_smith_source` marker. Upserts `config.json::bundles[]` (or emits the entry to stdout with `--no-config-write`). |
| `/smith-template-install --framework <name> [--version <ver>] --ai <provider> [--consumer-dir <abs>] [--no-config-write]` | yes | Adapts a framework template set to the consumer's stack — **stack-aware pruning** removes every mention of techs not in `architecture.json`. Upserts `config.json::skills[]` (or emits entries to stdout). |

### Orchestrator-internal (callable but normally driven by `/smith-new-project`)

| Command | What it does |
|---|---|
| `/smith-agents-md-write --payload <json>` | Writes `AGENTS.md` from a structured payload. Single canonical writer for the brief. Idempotent (skip if present). |
| `/smith-report-write --payload <json>` | Writes the project's **single** run report at `.smith/report.md`. Overwritten on every run — no per-run numbering. |

### Auto-loaded format specs (under `cli/bin/skills/`, `user-invocable: false`)

| Skill | Documents |
|---|---|
| `smith-architecture-format` | `.smith/architecture.json` shape + tag taxonomy. Auto-loads when the user asks about the project identity file. |
| `smith-config-format` | `.smith/config.json` shape + `bundles[]` / `skills[]` entry shapes + `_smith_source` merge marker. Auto-loads on questions about Smith state. |

### CLI-maintainer (under `cli/.claude/skills/` — dev-time only, NOT shipped)

| Command | What it does |
|---|---|
| `/smith-bundle-add <name> "<desc>" --tag t1,t2 [--ia provider]` | Scaffold a new bundle. Validates tags against the canonical taxonomy. Regenerates `bundles/config.json`. |
| `/smith-bundle-edit <name> [--add-skill ...] [--add-tag ...] [--bump-version ...]` | Modify an existing bundle. |
| `/smith-provider-add <slug> "<desc>"` | Scaffold a new AI provider format set under `cli/providers/<slug>/`. |
| `/smith-provider-edit <slug> [--rewrite-rule ...] [--add-kind ...]` | Modify an existing provider format set. |
| `/smith-template-add --framework <name> --version <ver> "<desc>"` | Scaffold a new framework/version template set. Regenerates `cli/templates/index.json`. |
| `/smith-build [--version <semver>]` | Package `cli/bin/` into a release archive under `cli/releases/`. Placeholder. |
| `smith-bundle-format` / `smith-provider-format` | Auto-loaded format specs for maintainer skills (same pattern as the consumer-side format skills). |

All `/smith-*` commands except `/smith-init`, `/smith-new-project` and
`/smith-help` check for the `.smith/smith.yaml` marker at the project
root and refuse to run if it is missing.

## Sub-agents shipped (`cli/bin/agents/`)

Driven by `/smith-new-project` and `/smith-generate-docs` — not invoked
by users directly.

| Agent | Model | Used by |
|---|---|---|
| `smith-functional-doc-writer`           | opus   | `/smith-generate-docs` |
| `smith-technical-doc-writer`            | opus   | `/smith-generate-docs` |
| `smith-template-customizer`             | opus   | `/smith-template-install` (orchestrates per-template adaptation) |
| `smith-single-template-adapter`         | sonnet | `smith-template-customizer` (one per template, parallel) |
| `smith-new-project-bundle-installer`    | haiku  | `/smith-new-project` step 4 — **planner** : reads + assembles + returns `BundlePlan` (no disk writes ; orchestrator executes the plan) |
| `smith-new-project-template-installer`  | haiku  | `/smith-new-project` step 5 — **planner** : dispatches customizer + adapter, returns `TemplatePlan` (no disk writes ; orchestrator executes the plan) |
| `smith-new-project-agents-writer`       | haiku  | `/smith-new-project` step 6 (assembles payload + invokes `/smith-agents-md-write`) |
| `smith-new-project-verifier`            | haiku  | `/smith-new-project` step 8 (11 structural checks) |
| `smith-new-project-scaffold-coordinator`| sonnet | `/smith-new-project` step 9 (provider gate + conflict guard + dispatches bootstrappers) |
| `smith-new-project-bootstrapper`        | opus   | scaffold-coordinator (one per framework, parallel ; runs the framework's `bootstrap` skill) |

**Planner pattern for steps 4 + 5.** The bundle / template installer
sub-agents are **planners**, not writers : they read the source
(`cli/bundles/...` / `cli/templates/...`) and assemble in-memory
content (`@smith-include` resolutions, adapted SKILLs) inside their
own context window, then return a structured Plan to the
orchestrator. The orchestrator executes every write from its own
persistent thread. This preserves context isolation for the heavy
reading / adaptation work while keeping writes out of sub-agent
threads where worktree-isolation cleanups had been wiping freshly-
written artefacts mid-flow.

## Layout

```
cli/
├── README.MD                     # this file
├── samples/                      # showcase consumer projects (angular-sample, acme-todo)
├── templates/                    # per framework/version skill template sets
│   ├── index.json                # written by /smith-template-add
│   ├── angular/21/
│   │   ├── config.yaml
│   │   └── skills/               # body-only markdown (no frontmatter)
│   └── java-spring-boot/4/
├── bundles/                      # opt-in libraries
│   ├── config.json               # written by /smith-bundle-add
│   ├── ia-stats/                 # auto IA_STATS.MD tracker (Claude Code hooks + Copilot VS Code tasks)
│   ├── mvn/                      # /mvn offload (claude-code + github-copilot)
│   └── npm/                      # /npm offload (claude-code + github-copilot)
├── providers/                    # per-AI-tool format reference
│   ├── claude-code/              # 4 rule-*.MD + example/ + RULES.MD
│   └── github-copilot/           # 4 rule-*.MD + example/ + RULES.MD
├── bin/                          # SHIPPABLE surface — packaged by /smith-build
│   ├── skills/                   # 12 consumer skills (see "Slash commands" above)
│   └── agents/                   # 10 sub-agents (see "Sub-agents" above)
├── releases/                     # output of /smith-build
└── .claude/                      # CLI-MAINTAINER surface (dev-time only, NOT shipped)
    └── skills/                   # /smith-bundle-{add,edit,format} + /smith-provider-{add,edit,format} + /smith-template-add + /smith-build
```

## Bundles shipped (v0.1)

| Bundle | Tags | What it gives you |
|---|---|---|
| `ia-stats` | `observability`, `hooks`, `claude-code`, `github-copilot` | Automatic `IA_STATS.MD` tracker. Two Claude Code hooks (`SubagentStop`, `PostToolUse`) **auto-merged** into `.claude/settings.json` ; same data flow as VS Code tasks for Copilot. Cross-platform Node.js script, zero dependencies. Includes the `/ia-stats` read-only slash command to print current totals. |
| `mvn`      | `build`, `java`, `backend` | `/mvn <goals>` slash command + `mvn-runner` Haiku sub-agent. Runs Maven and returns a one-line verdict + test counters + failure cause. Keeps Opus context clean. |
| `npm`      | `build`, `nodejs`, `frontend` | `/npm <args>` slash command + `npm-runner` Haiku sub-agent. Same Haiku-offload pattern as `mvn`, for the project's Node tooling. |

`/smith-new-project` selects matching bundles automatically by tag. To
install one explicitly outside the workflow :

```
/smith-bundle-install --name ia-stats --ia claude-code
```

The install **auto-merges** any hooks / tasks fragments into the
provider's live config (`.claude/settings.json` / `.vscode/tasks.json`)
using a `_smith_source: "<bundle>"` marker for idempotent
re-installs. No more "paste this snippet" manual step.

## Templates shipped (v0.1)

| Framework | Version | What it gives you |
|---|---|---|
| `angular`          | `21` | 6 skill bodies — bootstrap (interactive scaffold), coding standards, tests + coverage (Vitest), design system (Tailwind v4), i18n (Transloco), HTTP client layer from OpenAPI. The adapter **prunes optional techs** (Tailwind, Transloco, OpenAPI) not present in your stack. |
| `java-spring-boot` | `4`  | 1 bootstrap skill — interactive scaffold (`pom.xml`, application entry, optional REST controller, optional Liquibase changelog, `application.yaml`). `mvn -B verify` smoke check at the end. |

Templates are body-only markdown ; `smith-template-customizer` adds the
frontmatter on adaptation and `smith-single-template-adapter` rewrites
versions / strips CLI-side meta-refs / **prunes absent techs**
(stack-aware pruning).

## Providers shipped (v0.1)

| Provider | What's in the folder |
|---|---|
| `claude-code`    | 4 comprehensive rule files covering every frontmatter field for sub-agents, skills, all 29 hook events, and `CLAUDE.md` rules — each ships with a concrete `example-*` companion. Plus `RULES.MD` as router. |
| `github-copilot` | Same shape adapted to Copilot conventions (`.agent.md` custom agents, `.prompt.md` prompt files, `.github/instructions/*.instructions.md` with `applyTo`, VS Code tasks for hook-like behaviour). Plus `RULES.MD` as router. |

## Conventions

- **Naming** — Smith's own skills + agents use the `smith-` prefix.
  Bundle agents that are tool-runners keep their original slug
  (`mvn-runner`, `npm-runner`) ; the bundle name namespaces them.
- **Indexes** — `bundles/config.json` and `templates/index.json` are
  regenerated from disk by `/smith-bundle-add` / `/smith-template-add`.
  Never patched by hand.
- **Idempotency** — every `/smith-*` install / write skill is safe to
  re-run : files copied or written are not overwritten unless flagged,
  hooks merges are scoped by `_smith_source`, config upserts are keyed
  by name.
- **Zero install in consumer projects** — adapted skills are markdown.
  The only Smith-managed runtime script is `ia-stats`' `.js` running on
  Node stdlib — **no `package.json` required**, no `npm install`, no
  transitive dependencies.
- **Single-file run report** — `.smith/report.md` is overwritten by
  every workflow run. Older runs are not preserved (use git).

## Recent updates

- **`/smith-new-project`** — the new recommended entry point. 10-step
  agentic workflow. `/smith-init` is now a minimal marker-only skill.
- **Auto-merge of hooks / tasks** — `/smith-bundle-install` writes
  directly into `.claude/settings.json` with `_smith_source` markers.
  No more manual snippet step.
- **Stack-aware pruning** — template adapter removes every section,
  question, bullet and reporting line gated by a tech absent from the
  consumer's stack.
- **Path safety** — `--consumer-dir` is now mandatory from sub-agents
  to prevent merges from leaking into a parent repo's `.claude/`.
- **Race-free config upserts** — sub-agents use `--no-config-write`
  and emit entries to stdout ; orchestrator serialises the upserts.
- **Project-focused `AGENTS.md`** — no Smith branding inside ; talks
  about the project's stack and conventions.
- **Single-file report** — `.smith/report.md`, no per-run numbering.

## Detailed reference

Each kind of artefact (skills, agents, hooks, rules) has comprehensive
documentation in its template under `providers/<provider>/`. Each
template lists every supported frontmatter field with type, default,
allowed values, and meaning.

For interactive exploration : run `/smith-help` in Claude Code — it
auto-loads on Smith-related questions and indexes everything above.

## Status

v0.1 — first release. See `PLAN.md` for the rolling plan and open
questions.
