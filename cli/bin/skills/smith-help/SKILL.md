---
name: smith-help
description: Reference for the Smith CLI consumer surface. Use this skill whenever the developer asks how Smith works, what `/smith-init` / `/smith-generate-docs` / `/smith-dashboard` / `/smith-bundle-list` / `/smith-bundle-install` / `/smith-template-install` do, what `.smith/project-config.json` + `.smith/smith-config.json` + `AGENTS.md` contain, or how to get started. Covers ONLY the consumer-facing skills shipped under `cli/bin/skills/` — CLI-maintainer commands (`/smith-bundle-add`, `/smith-provider-add`, `/smith-template-add`, `/smith-build`) are out of scope. Auto-load on any question about Smith, smith-cli, smith bundles, or `/smith-*` slash commands.
when_to_use: User says "how do I", "what does", "where is", "what is smith", "smith cli", "smith bundle", "smith template", "smith provider", or types any `/smith-*` slash command and asks what it does. Also fires when the user wants to discover what Smith can do, get an overview, or pick the right command for their goal.
---

# Smith CLI — quick reference

Smith CLI is a Claude Code-native command set for **bootstrapping AI agent
surfaces in any project**. It produces functional + technical
specifications, then adapts a catalogue of skill templates to the project's
tech stack, and ships opt-in bundles (mvn, npm, ia-stats, …) that the user
can install à la carte.

This skill is the canonical answer to "how do I use Smith". It auto-loads
on any Smith-related question.

## Mental model in 3 lines

1. **One pipeline** — `/smith-init` reads the project, produces three spec
   files, and adapts the matching skill templates for the chosen AI tool.
2. **A catalogue under `cli/`** — `bundles/` (opt-in skill/agent libraries),
   `templates/` (per framework/version skill stubs), `providers/` (per AI
   tool format reference).
3. **All slash commands except `/smith-init` and `/smith-help`** require
   `/smith-init` to have run first ; they check for `.smith/FUNCTIONAL_SPECIFICATION.MD`
   as a marker.

## Slash command map (7 consumer commands)

| Command | Pre-init required ? | Purpose |
|---|:---:|---|
| `/smith-init "<description>" [--provider claude-code\|github-copilot]` | no — it IS the init | Bootstrap : creates `.smith/project-config.json` (stack with tags) + `.smith/smith-config.json` (Smith state) + `AGENTS.md`. Idempotent — skips files that already exist. |
| `/smith-generate-docs` | yes | Writes `.smith/FUNCTIONAL_SPECIFICATION.MD` and `.smith/TECHNICAL_SPECIFICATION.MD` by filling macro templates ; dispatches two doc-writer agents in parallel ; does NOT touch the JSON config files. |
| `/smith-help` | no | This skill — auto-loads on Smith-related questions. |
| `/smith-dashboard` | yes | Renders `.smith/dashboard.html` from `project-config.json` + `smith-config.json`. Read-only on the two JSONs ; idempotent regeneration. |
| `/smith-bundle-list [--tag X[,Y]]` | yes | Read-only listing of `cli/bundles/config.json`. Multiple `--tag` values are AND'd. |
| `/smith-bundle-install --name X --ia <provider>` | yes | Copies a bundle's files into the consumer project's `.claude/` (or `.github/`). Upserts `bundles[]` in `.smith/smith-config.json`. |
| `/smith-template-install --framework <name> [--version <ver>] --ai <provider>` | yes | Reads a template set, dispatches `smith-template-customizer` + `smith-single-template-adapter`, writes adapted SKILL files to the consumer's `.claude/skills/` (or `.github/prompts/`). Upserts `skills[]` in `.smith/smith-config.json`. |

Legend : **yes** = requires `/smith-init` on the consumer project ;
**no** = standalone.

CLI-maintainer commands (`/smith-bundle-add`, `/smith-provider-add`,
`/smith-template-add`, `/smith-build`) are NOT shipped with the
consumer release and are intentionally out of scope here. They live
under `cli/.claude/skills/` of the Smith CLI workspace and are run by
the CLI owners only.

## Directory layout (`cli/` root)

```
cli/
├── PLAN.md
├── README.MD
├── samples/                      # showcase consumer projects (e.g. acme-todo)
├── templates/                    # framework/version skill template sets
│   ├── index.json
│   └── angular/21/
├── bundles/                      # opt-in libraries (multi-provider)
│   ├── config.json
│   ├── ia-stats/
│   ├── mvn/
│   └── npm/
├── providers/                    # per-AI-tool format reference
│   ├── claude-code/
│   └── github-copilot/
├── bin/                          # ← the 7 consumer skills documented in this skill
│   ├── skills/                   # smith-init / smith-help / smith-generate-docs / smith-dashboard / smith-bundle-{list,install} / smith-template-install / smith-project-config-format / smith-config-format
│   └── agents/                   # smith-functional-doc-writer + smith-technical-doc-writer + smith-template-customizer + smith-single-template-adapter
├── releases/                     # output of /smith-build (maintainer-side)
└── .claude/                      # CLI-MAINTAINER skills — not shipped, out of scope here
```

## Bundle config shape (`bundles/<name>/config.yaml`)

```yaml
name: <kebab-case>
description: |
  Multi-line — what the bundle does end-to-end.
version: 0.1.0
tags: [<from taxonomy>]
providers: [claude-code | github-copilot]
files:
  claude-code:
    - kind: skill | agent | hook | script | rules
      path: claude-code/...
      description: One-line — what this file is for.
```

The kind field tells `/smith-bundle-install` where to drop each file in
the consumer project (`skill` → `.claude/skills/`, `agent` →
`.claude/agents/`, `hook` → print snippet for `settings.json`, `script` →
`.claude/scripts/`, `rules` → `.claude/rules/`).

## Template config shape (`templates/<framework>/<version>/config.yaml`)

```yaml
framework: <kebab>
version: "<ver>"
description: |
  Multi-line — what this template set covers.
files:
  - kind: skill
    path: skills/<slug>.SKILL.md
    description: One-line.
adapter_placeholders:
  "{{language}}": ...
  "{{runtime}}": ...
  "{{framework}}": ...
  "{{framework_version}}": ...
  "{{root_package}}": ...
```

Template skill files are **body-only markdown** — no YAML frontmatter.
The customizer generates the frontmatter on adaptation (with
`name: smith-<framework>-<slug>` and a project-tailored description).

## Tag taxonomy (canonical, lives in `/smith-bundle-add` SKILL.md)

- **role** : `build`, `test`, `lint`, `format`, `deploy`, `observability`,
  `docs`, `scaffold`, `sdlc`, `release`, `security`.
- **language** : `java`, `kotlin`, `javascript`, `typescript`, `python`,
  `go`, `rust`, `csharp`, `ruby`, `php`, `shell`.
- **runtime** : `jvm`, `nodejs`, `python3`, `dotnet`, `browser`.
- **tier** : `frontend`, `backend`, `fullstack`, `infra`, `cli`, `library`.
- **provider** : `claude-code`, `github-copilot`, `gemini-cli`, `opencode`.
- **integration** : `hooks`, `slash-command`, `mcp`, `sub-agent`.

Wire format is a flat `tags: [a, b, c]` list. Categories exist only as
authoring guidance.

## Two-tier mental model

- **Smith CLI itself** lives at `cli/.claude/` — these are the skills +
  agents you (the user) run when you're working **inside `cli/`** to
  extend Smith.
- **Consumer projects** install bundles via `/smith-bundle-install`.
  Their `.claude/` ends up populated by Smith ; Smith itself doesn't
  live there.

This means : to use a Smith bundle in your own project, you don't need
to have `cli/` checked out — you only need the files Smith copies in.

## Where do I start ? (3 recipes)

### Recipe A — bootstrap a new project with Smith

```
cd <consumer-project>            # the project you want to agentify
/smith-init "<one-line description>"
# Smith writes .smith/project-config.json + .smith/smith-config.json + AGENTS.md.
/smith-generate-docs
# Smith writes .smith/FUNCTIONAL_SPECIFICATION.MD + .smith/TECHNICAL_SPECIFICATION.MD.
/smith-template-install --framework angular --version 21 --ai claude-code
# Smith adapts cli/templates/angular/21/skills/*.SKILL.md into .claude/skills/.
```

### Recipe B — install the mvn or npm Haiku-offload bundle

```
# already inside an init'd project
/smith-bundle-list --tag build
/smith-bundle-install --name mvn --ia claude-code
# Smith copies skill + agent into .claude/ and prints a 'verify' line
```

### Recipe C — add automatic agent tracking (`AGENT_STATUS.MD`)

```
/smith-bundle-install --name ia-stats --ia claude-code
# Smith copies the hook fragment, the Python script, and the /agent-status skill
# Smith prints the JSON snippet to merge into .claude/settings.json
```

## Pre-init guard rail

Every `/smith-*` command except `/smith-init` and `/smith-help` checks for
`.smith/FUNCTIONAL_SPECIFICATION.MD` at the project root. If missing, the
command halts with one line :

```
This command requires /smith-init to have run. Run it first.
```

## What this skill does NOT do

- It does not execute any command for the user — it explains. If the user
  asks "run `/smith-bundle-list`", the assistant runs the corresponding
  skill, not this one.
- It does not list bundles or templates — that's `/smith-bundle-list` and
  the `cli/templates/index.json` file (read directly when needed).
- It does not bootstrap a project — that's `/smith-init`.

## Reporting back

When the user asks an open question ("how does smith work ?"), reply
with the relevant section of this skill, NOT the entire body. Pick the
narrowest answer the question warrants, link to the relevant slash
command, and offer to run it if the user wants to act.
