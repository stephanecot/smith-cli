---
name: smith-help
description: Reference for the Smith CLI consumer surface. Use this skill whenever the developer asks how Smith works, what `/smith-new-project` / `/smith-init` / `/smith-generate-docs` / `/smith-dashboard` / `/smith-bundle-list` / `/smith-bundle-install` / `/smith-template-install` do, what `.smith/architecture.json` + `.smith/config.json` + `.smith/smith.yaml` + `.smith/report.md` + `AGENTS.md` contain, or how to get started. Covers ONLY the consumer-facing skills shipped under `cli/bin/skills/` — CLI-maintainer commands (`/smith-bundle-add`, `/smith-provider-add`, `/smith-template-add`, `/smith-build`, …) are out of scope. Auto-load on any question about Smith, smith-cli, smith bundles, or `/smith-*` slash commands.
when_to_use: User says "how do I", "what does", "where is", "what is smith", "smith cli", "smith bundle", "smith template", "smith provider", or types any `/smith-*` slash command and asks what it does. Also fires when the user wants to discover what Smith can do, get an overview, or pick the right command for their goal.
---

# Smith CLI — quick reference

Smith CLI is a Claude Code-native command set for **bootstrapping AI
agent surfaces in any project**. The recommended entry point is
`/smith-new-project "<one-line description>"` — a 10-step agentic
workflow that takes a description and ends with a runnable
Smith-managed project (configs + bundles + adapted skills + AGENTS.md
+ source scaffold + report).

This skill is the canonical answer to "how do I use Smith". It
auto-loads on any Smith-related question.

## Mental model in 3 lines

1. **One command does it all** — `/smith-new-project "<desc>"` runs a
   10-step pipeline (init → discovery → configs → bundles → templates
   → AGENTS.md → refresh → verify → scaffold → report) end-to-end.
2. **A catalogue under `cli/`** — `bundles/` (opt-in skill/agent
   libraries with auto-merged hooks), `templates/` (per
   framework/version skill stubs adapted to your stack), `providers/`
   (per AI tool format reference).
3. **`.smith/smith.yaml` is the marker** — every `/smith-*` command
   except `/smith-new-project`, `/smith-init` and `/smith-help`
   refuses to run if the marker is missing.

## Slash command map (8 user-invocable consumer commands)

| Command | Pre-marker required ? | Purpose |
|---|:---:|---|
| `/smith-new-project "<description>" [--provider claude-code\|github-copilot]` | no — it runs `/smith-init` if needed | **The recommended entry point.** 10-step agentic workflow : `/smith-init` → stack discovery → architecture.json + config.json → parallel bundle installs → parallel template installs → AGENTS.md → config refresh → verifier → scaffold the source tree → write `.smith/report.md`. |
| `/smith-init [--provider claude-code\|github-copilot]` | no — it IS the marker | Minimal init : creates `.smith/smith.yaml` (init datetime + provider + `enabled: true`). Does NOT write configs, AGENTS.md, or run discovery. Most users want `/smith-new-project` instead. |
| `/smith-help` | no | This skill — auto-loads on Smith-related questions. |
| `/smith-generate-docs` | yes | Writes `.smith/FUNCTIONAL_SPECIFICATION.MD` + `TECHNICAL_SPECIFICATION.MD` from `architecture.json`. Dispatches two doc-writer agents in parallel. |
| `/smith-dashboard` | yes | Renders `.smith/dashboard.html` from `architecture.json` + `config.json`. Read-only on the two JSONs ; idempotent regeneration. |
| `/smith-bundle-list [--tag X[,Y]]` | yes | Read-only listing of `cli/bundles/config.json`. Multiple `--tag` values are AND'd. |
| `/smith-bundle-install --name X --ia <provider> [--consumer-dir <abs>] [--no-config-write]` | yes | Installs a bundle : copies files (resolving `@smith-include` directives via `Read` + `Write` — never `cp` for skill / agent wrappers), **auto-merges hook fragments into `.claude/settings.json`** with `_smith_source` marker for idempotent re-installs. Upserts `config.json::bundles[]` (with `merged_into[]`), or emits a `BUNDLE_ENTRY:` line on stdout when `--no-config-write` is set. |
| `/smith-template-install --framework <name> [--version <ver>] --ai <provider> [--consumer-dir <abs>] [--no-config-write]` | yes | Reads a template set, dispatches `smith-template-customizer` + `smith-single-template-adapter` per template. The adapter **strips CLI-side meta-refs** and **prunes optional techs not present in `architecture.json`** (e.g. removes every Tailwind reference when the consumer project doesn't use Tailwind). Upserts `config.json::skills[]` or emits `SKILL_ENTRY:` lines on stdout. |

## Orchestrator-internal skills (under `cli/bin/skills/`, used by `/smith-new-project`)

These are callable directly but normally driven by the workflow ; end
users rarely invoke them by hand.

| Skill | Purpose |
|---|---|
| `/smith-agents-md-write --payload <json>` | Writes `AGENTS.md` from a structured payload. Single canonical writer. Idempotent (skips if file exists). Enforces a 100-line cap with documented truncation order. **Project-focused** — the rendered brief carries no Smith branding (no mention of `.smith/`, `/smith-*` commands, installed bundles, etc. ; the brief talks about the project's stack and conventions). |
| `/smith-report-write --payload <json>` | Writes the project's **single** run report at `.smith/report.md` (overwritten on every workflow run — no per-run numbering, no `<NNN>-<slug>` prefix). |

## Auto-loaded format specs (under `cli/bin/skills/`, `user-invocable: false`)

Format-only skills — auto-load when the assistant needs to know the
exact shape of a Smith file, never invoked as slash commands.

| Skill | Documents |
|---|---|
| `smith-architecture-format` | `.smith/architecture.json` — project identity (name + description + summary + detected stack with kebab-case `tags[]`). Includes the canonical tag taxonomy. |
| `smith-config-format`       | `.smith/config.json` — Smith state (provider + spec paths + `skills[]` adapted from templates + `bundles[]` installed with `files[]` + `merged_into[]`). Documents the `_smith_source` merge marker. |

CLI-maintainer commands (`/smith-bundle-add`, `/smith-bundle-edit`,
`/smith-provider-add`, `/smith-provider-edit`, `/smith-template-add`,
`/smith-build`, plus the `smith-bundle-format` / `smith-provider-format`
auto-load specs) are NOT shipped with the consumer release and are
intentionally out of scope here. They live under `cli/.claude/skills/`
of the Smith CLI workspace and are run by the CLI owners only.

## What lands in the consumer project

Under `<consumer>/.smith/` (Smith metadata) :

| File | Created by | Re-written by |
|---|---|---|
| `smith.yaml`                       | `/smith-init` | nobody (delete to disable Smith on the project) |
| `architecture.json`                | `/smith-new-project` step 3 | nobody (delete + re-run to re-detect) |
| `config.json`                      | `/smith-new-project` step 3 | `/smith-bundle-install` (upserts `bundles[]`), `/smith-template-install` (upserts `skills[]`), step 7 (refresh) |
| `FUNCTIONAL_SPECIFICATION.MD`      | `/smith-generate-docs` | every `/smith-generate-docs` run |
| `TECHNICAL_SPECIFICATION.MD`       | `/smith-generate-docs` | every `/smith-generate-docs` run |
| `report.md`                        | `/smith-report-write` | every `/smith-new-project` run (overwritten ; no per-run history) |

At the consumer project root :

| File | Created by | Notes |
|---|---|---|
| `AGENTS.md` | `/smith-agents-md-write` (driven by `/smith-new-project` step 6) | Project-focused brief, ≤100 lines. Loaded by Claude Code / Copilot on every turn. No Smith branding inside. Idempotent — skipped if already present. |

Under `<consumer>/.claude/` (Claude Code) or `<consumer>/.github/` (Copilot) :

- `skills/` — adapted framework skills (from `/smith-template-install`) + installed bundle skills.
- `agents/` — installed bundle sub-agents.
- `scripts/` — Node-stdlib helper scripts shipped by bundles.
- `settings.json` — auto-merged hook entries (Claude Code). Each Smith-injected entry carries `"_smith_source": "<bundle>"` so re-installs replace them in place ; entries without the marker (hand-written or from other tools) are preserved untouched.

## Bundle config shape (`bundles/<name>/config.yaml`)

```yaml
name: <kebab-case>
description: |
  Multi-line — what the bundle does end-to-end.
version: 0.1.0
tags: [<from taxonomy>]
providers: [claude-code, github-copilot]
files:
  common:
    - kind: skill-body | agent-body | script
      path: common/...
  claude-code:
    - kind: skill | agent | hook | script
      path: claude-code/...
  github-copilot:
    - kind: skill | agent | task | script
      path: github-copilot/...
```

The kind field tells `/smith-bundle-install` how to handle the file :
- `skill` / `agent` → wrapper files with `@smith-include` directive,
  resolved + assembled via `Read` + `Write` (NEVER `cp`).
- `script` → byte-copy to `.claude/scripts/` or `.vscode/scripts/`,
  executable bit set for `.py` / `.sh` / `.js`.
- `hook` (Claude Code) → **merged** into `.claude/settings.json` with
  `_smith_source` marker.
- `task` (Copilot) → **merged** into `.vscode/tasks.json` with
  `_smith_source` marker.

`common/` files are NEVER copied as-is — their content is inlined into
the per-provider wrappers at install time.

## Template config shape (`templates/<framework>/<version>/config.yaml`)

```yaml
framework: <kebab>
version: "<ver>"
description: |
  Multi-line — what this template set covers.
files:
  - kind: skill
    path: skills/<slug>.md
adapter_placeholders:
  "{{language}}": ...
  "{{runtime}}": ...
  "{{framework}}": ...
  "{{framework_version}}": ...
  "{{root_package}}": ...
  "{{project_name}}": ...
```

Template skill files are **body-only markdown** — no YAML frontmatter.
The customizer generates the frontmatter on adaptation
(`name: smith-<framework>-<slug>`, project-tailored description) and
**prunes every section / question / bullet gated by a tech absent from
`architecture.json`** (stack-aware pruning).

## Tag taxonomy (canonical, lives in `/smith-bundle-add` SKILL.md)

- **role**        : `build`, `test`, `lint`, `format`, `deploy`, `observability`, `docs`, `scaffold`, `sdlc`, `release`, `security`.
- **language**    : `java`, `kotlin`, `javascript`, `typescript`, `python`, `go`, `rust`, `csharp`, `ruby`, `php`, `shell`.
- **runtime**     : `jvm`, `nodejs`, `python3`, `dotnet`, `browser`.
- **tier**        : `frontend`, `backend`, `fullstack`, `infra`, `cli`, `library`.
- **provider**    : `claude-code`, `github-copilot`, `gemini-cli`, `opencode`.
- **integration** : `hooks`, `slash-command`, `mcp`, `sub-agent`.

Wire format is a flat `tags: [a, b, c]` list. Categories exist only as
authoring guidance.

## Where do I start ? (3 recipes)

### Recipe A — bootstrap a new project end-to-end (the usual flow)

```
cd <consumer-project>            # the project you want to agentify
/smith-new-project "<one-line description>"
# Runs the 10-step workflow : init → discovery → configs → bundles
# → templates → AGENTS.md → refresh → verify → scaffold source → report.
# When done, .smith/report.md tells you what was installed.
```

### Recipe B — install just one bundle on an existing Smith-managed project

```
# already inside an init'd project (.smith/smith.yaml present)
/smith-bundle-list --tag build
/smith-bundle-install --name mvn --ia claude-code
# Copies the bundle's skill + agent, auto-merges any hooks fragment
# into .claude/settings.json with _smith_source="mvn".
```

### Recipe C — add automatic agent tracking (`IA_STATS.MD`)

```
/smith-bundle-install --name ia-stats --ia claude-code
# Copies the /ia-stats skill + the Node-stdlib script,
# AUTO-merges the SubagentStop + PostToolUse hooks into
# .claude/settings.json (no manual snippet to paste).
# After the first sub-agent dispatch or tool call, IA_STATS.MD appears
# at the project root. Read it with /ia-stats.
```

## Pre-marker guard rail

Every `/smith-*` command except `/smith-new-project`, `/smith-init`
and `/smith-help` checks for `.smith/smith.yaml` at the consumer
project root. If missing, the command halts with :

```
This command requires /smith-init (or /smith-new-project) to have run
on this project. Run one of them first.
```

`/smith-new-project` itself dispatches `/smith-init` as its step 1
when the marker is absent.

## Path safety — `--consumer-dir`

When sub-agents invoke `/smith-bundle-install` or
`/smith-template-install` from a non-consumer CWD (e.g. parent repo
shell), they MUST pass `--consumer-dir <absolute-path>` so the install
writes destinations rooted at the right `.claude/` tree. Otherwise the
install walks up from CWD to find `.smith/smith.yaml`. Hooks merges in
particular must land in the consumer's `.claude/settings.json`, never
in a parent repository's.

## Race-free `config.json` upserts

When `/smith-new-project` runs several bundle / template installers in
parallel, each is dispatched with `--no-config-write`. Each install
prints its `bundles[]` / `skills[]` entry as a `BUNDLE_ENTRY:` /
`SKILL_ENTRY:` line on stdout instead of mutating `config.json`. The
orchestrator collects every entry, then upserts them all serially in
one final atomic write — eliminating the read-write race that
previously let parallel installers clobber each other.

## What this skill does NOT do

- It does not execute any command for the user — it explains. If the
  user asks "run `/smith-bundle-list`", the assistant runs the
  corresponding skill, not this one.
- It does not list bundles or templates — that's `/smith-bundle-list`
  and the `cli/templates/index.json` file (read directly when needed).
- It does not bootstrap a project — that's `/smith-new-project`.

## Reporting back

When the user asks an open question ("how does smith work ?"), reply
with the relevant section of this skill, NOT the entire body. Pick the
narrowest answer the question warrants, link to the relevant slash
command, and offer to run it if the user wants to act.
