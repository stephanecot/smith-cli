# Smith CLI

A Claude Code-native command set for **bootstrapping AI agent surfaces in
any project**. Smith reads a project, produces functional + technical
specifications, then adapts a catalogue of skill templates to the
project's tech stack. Opt-in bundles (mvn, npm, ia-stats, …) can be
installed à la carte.

No server. No database. Markdown files + a couple of zero-dependency
Node.js scripts where automation is needed. No Python, no `npm install`,
no `package.json` requirement in consumer projects.

## Quick start

```
cd <your-project>                       # the project you want to agentify
# In Claude Code :
/smith-init --provider claude-code
```

Smith writes two narrative specs + two structured JSON files under `.smith/` :

- `FUNCTIONAL_SPECIFICATION.MD` — what the system does (PO / QA / onboarding).
- `TECHNICAL_SPECIFICATION.MD` — architecture for a senior engineer.
- `architecture.json` — **what the project IS**. Detected languages /
  runtimes / frameworks / build / test / infra / database tools, each with
  `name`, `version`, `tags`. Re-detected on every `/smith-init` rerun.
- `config.json` — **what Smith DID**. Provider, spec paths,
  `AGENTS.md` pointer, list of adapted skills (with source template),
  list of installed bundles (with version + tags + files). Upserted by
  `/smith-bundle-install` and `/smith-template-install`. Both JSONs feed
  `/smith-dashboard`.

It then adapts the matching skill templates from `cli/templates/` and
drops the adapted SKILL files into your project's `.claude/skills/` (or
`.github/prompts/` for GitHub Copilot).

Finally, Smith writes a token-optimized **always-on AI brief** at the repo
root :

- `AGENTS.md` (recognised by both Claude Code and GitHub Copilot via the
  cross-tool `AGENTS.md` convention).

Hard cap : ≤ 100 lines. The file points at the `.smith/` specs rather
than duplicating their content — so it stays cheap to keep in every
turn's context.

Need help ? Run `/smith-help` — it's a Claude Code skill that auto-loads
on any Smith-related question.

## Slash commands (11)

### Consumer-facing (shipped under `cli/bin/skills/` — bundled on release)

| Command | What it does |
|---|---|
| `/smith-init "<description>"` | Bootstrap — creates `.smith/architecture.json` (stack with tags) + `.smith/config.json` (Smith state) + `AGENTS.md` at the project root. Idempotent. |
| `/smith-generate-docs` | Writes `.smith/FUNCTIONAL_SPECIFICATION.MD` and `.smith/TECHNICAL_SPECIFICATION.MD` by filling macro templates ; dispatches the two doc-writer agents in parallel. Does NOT touch the JSON config files. |
| `/smith-help` | Reference — auto-loads on Smith questions. |
| `/smith-dashboard` | Render `.smith/dashboard.html` from `architecture.json` + `config.json`. |
| `/smith-bundle-list [--tag X[,Y]]` | List bundles (intersection filter). |
| `/smith-bundle-install --name X --ia <provider>` | Copy a bundle into your project's `.claude/` (or `.github/`). Upserts `bundles[]` in `.smith/config.json`. |
| `/smith-template-install --framework <name> [--version <ver>] --ai <provider>` | Adapt a framework template set to a consumer project. Upserts `skills[]` in `.smith/config.json`. |

### CLI-maintainer (live under `cli/.claude/skills/` — dev-time only, NOT shipped)

| Command | What it does |
|---|---|
| `/smith-bundle-add <name> "<desc>" --tag t1,t2 [--ia provider]` | Scaffold a new bundle (defaults to all providers) ; validate tags ; regen `bundles/config.json`. |
| `/smith-provider-add <slug> "<desc>"` | Scaffold a new AI provider format set under `cli/providers/<slug>/`. |
| `/smith-template-add --framework <name> --version <ver> "<desc>"` | Scaffold a new framework/version template set under `cli/templates/`. Regenerates `cli/templates/index.json`. |
| `/smith-build [--version <semver>]` | Package `cli/bin/` into a release archive under `cli/releases/`. Placeholder — body to be filled. |

All slash commands except `/smith-init` and `/smith-help` require
`/smith-init` to have run on the consumer project. They check for
`.smith/FUNCTIONAL_SPECIFICATION.MD` as a marker. `/smith-dashboard` also
requires both `.smith/architecture.json` and `.smith/config.json`,
which `/smith-init` writes alongside the specs.

## Layout

```
cli/
├── README.MD                     # this file
├── PLAN.md                       # rolling plan + open questions
├── samples/                      # showcase consumer projects (acme-todo, …)
├── templates/                    # per framework/version skill template sets
│   ├── index.json                # written by /smith-template-add
│   └── angular/21/
│       ├── config.yaml
│       └── skills/               # body-only markdown (no frontmatter)
├── bundles/                      # opt-in libraries
│   ├── config.json               # written by /smith-bundle-add
│   ├── ia-stats/                 # auto agent-status tracking via hooks (multi-provider)
│   ├── mvn/                      # /mvn offload (claude-code + github-copilot)
│   └── npm/                      # /npm offload (claude-code + github-copilot)
├── providers/                    # per-AI-tool format reference
│   ├── claude-code/              # 4 rule-*.MD + example/ + RULES.MD
│   └── github-copilot/           # 4 rule-*.MD + example/ + RULES.MD
├── bin/                          # SHIPPABLE surface — packaged by /smith-build on release
│   ├── skills/                   # 8 consumer skills (init, help, generate-docs, dashboard, bundle-{list,install}, template-install, config-format)
│   └── agents/                   # 4 pipeline agents (functional + technical doc writers, template customizer + adapter)
├── releases/                     # output of /smith-build (zip archives per version)
└── .claude/                      # CLI-MAINTAINER Claude Code surface (dev-time only — NOT shipped)
    ├── skills/                   # smith-bundle-add, smith-provider-add, smith-template-add, smith-build
    ├── agents/                   # (empty — pipeline agents now live in cli/bin/agents/)
    ├── hooks/
    └── rules/
```

**Two-tier skill layout** :
- `cli/bin/` — the **shippable surface**. Skills + agents that get
  packaged into a release archive by `/smith-build` and shipped to
  consumer projects.
- `cli/.claude/` — the **CLI-maintainer surface** (dev-time only).
  Skills the CLI owners run to extend Smith (`/smith-bundle-add`,
  `/smith-provider-add`, `/smith-template-add`) plus `/smith-build`
  itself. Not part of any release archive.

## Bundles shipped (v0.1)

| Bundle | Tags | What it gives you |
|---|---|---|
| `ia-stats` | `observability`, `hooks`, `claude-code` | Automatic `AGENT_STATUS.MD` tracker. Two hooks (`SubagentStop`, `PostToolUse`) + a cross-platform Node.js script (zero npm deps — stdlib only, no `package.json` needed) that appends a row per event. Includes the `/agent-status` read-only slash command. |
| `mvn` | `build`, `java`, `backend` | `/mvn <goals>` slash command + `mvn-runner` Haiku sub-agent. Runs Maven and returns a one-line verdict + Tests counters + failure cause. Keeps Opus context clean. |
| `npm` | `build`, `nodejs`, `frontend` | `/npm <args>` slash command + `npm-runner` Haiku sub-agent. Same Haiku-offload pattern as `mvn`, scoped to the project's `frontend/` workspace. |

Install any one with `/smith-bundle-install --name <bundle> --ia claude-code`.

## Templates shipped (v0.1)

| Framework | Version | What it gives you |
|---|---|---|
| `angular` | `21` | 5 skill bodies — coding standards, tests + coverage (Vitest), design system (Tailwind v4), i18n (Transloco), HTTP client layer from OpenAPI. Body-only markdown ; `smith-template-customizer` adds the frontmatter on adaptation. |

Adapt with `/smith-template-install --framework angular --version 21 --ai claude-code`.

## Providers shipped (v0.1)

| Provider | What's in the folder |
|---|---|
| `claude-code` | 4 comprehensive rule files (`rule-agent.MD`, `rule-skill.MD`, `rule-hook.MD`, `rule-rules.MD`) covering every frontmatter field for sub-agents, skills, all 29 hook events, and `CLAUDE.md` rules — each ships with a concrete `example-*` companion. Plus `RULES.MD` as router. |
| `github-copilot` | Same shape adapted to Copilot conventions (`.agent.md` custom agents, `.prompt.md` prompt files, `.github/instructions/*.instructions.md` with `applyTo`, VS Code tasks / lefthook / GitHub Actions for hook-like behaviour). Plus `RULES.MD` as router. |

## Conventions

- **Naming** : Smith's pipeline agents and skills use the `smith-` prefix
  (`smith-init`, `smith-functional-doc-writer`, …). Bundle agents that are
  tool-runners keep their original slug without the prefix (`mvn-runner`,
  `npm-runner`) — the bundle name namespaces them.
- **Indexes** : `bundles/config.json` and `templates/index.json` are
  regenerated from disk by the corresponding `/smith-*-add` skill. Never
  patched by hand.
- **Zero install in consumer projects** : adapted skills are markdown files
  that Claude Code reads directly. The only Smith-managed script
  (`ia-stats`) is a single `.js` running on Node stdlib — **no
  `package.json` required**, no `npm install`, no transitive dependencies.

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
