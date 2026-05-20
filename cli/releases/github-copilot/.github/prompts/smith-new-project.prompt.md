---
name: smith-new-project
description: Bootstraps a brand-new Smith-managed project end-to-end from a pre-built release tree. 10-step agentic workflow — `/smith-init`, stack discovery, `.smith/architecture.json` + `.smith/config.json`, bundle installs (filter + copy from `<release>/.smith/bundles/`), template installs (filter + adapt skill bodies for the project stack), AGENTS.md, smith-config refresh, verifier, framework scaffold, run report. Reads consumer-side install paths from `<release>/.smith/paths.yaml` so the skill body is identical across providers (claude-code / github-copilot / opencode). No `@smith-include` resolution, no frontmatter composition at install time. Trigger with `/smith-new-project "<description>"`.
---

# Skill — `/smith-new-project`

Greenfield orchestrator. Bootstraps a runnable Smith-managed project
from the pre-built release tree this skill ships inside.

## Release-tree model

This skill is part of a `/smith-build` release. `<release_root>/` is
the directory containing this skill ; resolve it by walking up from
the running skill's location until you find a `.smith/` directory
with `paths.yaml` + `bundles/` + `templates/` inside. The tree :

```
<release_root>/
└── .smith/
    ├── paths.yaml               ← consumer-side install paths (provider-resolved)
    ├── release.yaml             ← build manifest
    ├── bundles/
    │   ├── config.json          ← catalogue : tags + skills + hooks
    │   └── <bundle>/
    │       ├── config.yaml
    │       ├── skills/<slug>/SKILL.md   ← real skill, frontmatter included
    │       └── hooks/...                ← flat hook files for this release
    └── templates/
        ├── index.json           ← catalogue : frameworks + versions
        └── <framework>/<version>/
            ├── config.yaml
            └── skills/<slug>/SKILL.md   ← real skill ; body still has
                                           {{placeholder}} + stack-gated sections
```

Plus the provider's runtime root (`.claude/skills/` + `.claude/agents/`,
or `.github/prompts/` + `.github/agents/`, or `.opencode/commands/` +
`.opencode/agents/`) holding the Smith bin skills + sub-agents.

`.smith/paths.yaml` carries every provider-specific path template
used by this workflow :

```yaml
skill:    "<template using {slug}>"      # consumer destination for installed skills
agent:    "<template using {slug}>"      # consumer destination for installed agents
hook_dir: "<template using {bundle}>"    # where bundle hook files land
settings: "<consumer settings file>"     # for *.hooks.json fragment merges ; may be null
```

Read `.smith/paths.yaml` once at the start of the workflow and
reuse it throughout. **The skill body never branches on provider** —
every provider-specific concern is encoded in this file.

## How to invoke

```
/smith-new-project "<description>"
```

`<description>` is required ; if missing, ask via `AskUserQuestion`.
There is no `--provider` flag — the provider was chosen when the
release was built ; this skill is provider-agnostic.

## Pre-flight

- Current working directory must be writable (this is the consumer
  project).
- Resolve `<release_root>` ; it must contain `.smith/paths.yaml`,
  `.smith/bundles/`, `.smith/templates/`. Refuse with
  `release-not-found` otherwise.
- Git is recommended but not mandatory.

## Workflow

Strictly sequential at the orchestrator level. Parallelism happens
inside Step 5 (one adapter sub-agent per template skill) and Step 8
(one bootstrapper per framework). Each step appends timing + outcomes
to a `TraceLog` that Step 9 dumps into `.smith/report.md`.

### Step 1 — `/smith-init` (conditional)

If `.smith/smith.yaml` already exists, skip. Otherwise dispatch the
sibling skill `smith-init`, then re-read `.smith/smith.yaml` to
confirm the marker.

### Step 2 — Stack discovery (sub-agent)

**MANDATORY sub-agent dispatch — never inline.** Use the Agent tool to
invoke `smith-stack-discoverer` with `description` and
`consumer_project_dir`. The discoverer will ask the user the
structuring questions it needs (frontend framework / backend
framework / database / build tool / test stack / infra target) via
`AskUserQuestion` and return a fully-populated stack. **Do NOT skip
this step**, do NOT short-circuit it by parsing the description
yourself — even if the description looks rich, the discoverer
applies framework defaults + records `assumed_defaults[]` for the
report, which the orchestrator cannot reproduce.

Wait for its structured return :

```json
{
  "status":           "ready | failed",
  "reason":           "<token or null>",
  "stack":            { ...same keys as architecture.json::project... },
  "questions_asked":  <int>,
  "assumed_defaults": [...]
}
```

On `status=failed` (`description-too-vague` / `user-cancelled`),
surface to the user and exit cleanly. The discoverer is the **only**
step allowed to call `AskUserQuestion`.

### Step 3 — Write `.smith/architecture.json` + `.smith/config.json`

Read canonical templates from the sibling skills
`smith-architecture-format` and `smith-config-format`. Fill from the
discovery stack ; atomic-write both files. `config.json` starts as
an empty shell ; Steps 4 + 5 upsert into it.

### Step 4 — Bundle installs (filter + copy)

Pure filter + copy ; no sub-agent.

1. Read `<release_root>/.smith/bundles/config.json`.
2. Pick bundles whose `tags[]` intersect the project's stack tags
   (union of `tags[]` across every entry in `architecture.json`).
3. For each picked bundle, in deterministic alphabetical order :
   - For each `skill` in the bundle's `config.yaml::skills[]`, copy
     `<release_root>/.smith/bundles/<bundle>/skills/<slug>/SKILL.md` to
     `<consumer>/<paths.skill.format(slug=<slug>)>`.
   - For each file under `<release_root>/.smith/bundles/<bundle>/hooks/` :
     - If `paths.settings` is non-null AND the filename matches
       `*.hooks.json` → merge the JSON fragment into
       `<consumer>/<paths.settings>` tagged with
       `_smith_source: <bundle>`.
     - Else → copy verbatim to
       `<consumer>/<paths.hook_dir.format(bundle=<bundle>)>/<file>`.
4. Upsert `.smith/config.json::bundles[]` with one entry per bundle
   listing the consumer-relative paths written. Atomic write of
   `config.json` at the end, bump `generated_at`.

Per-bundle failure is logged in the trace and skipped — never roll
back the others.

### Step 5 — Template installs (filter + adapter)

Release template skills are already real `SKILL.md` files (frontmatter
composed at build time). Step 5 filters them against the stack and
adapts the body to resolve `{{placeholder}}` markers + prune
sections gated by absent techs.

1. Read `<release_root>/.smith/templates/index.json`.
2. Pick (framework, version) pairs matching the project's stack
   (`framework` ∈ `architecture.json::frameworks[].name` ; version
   per the downward-match rule — highest template version `≤` the
   project's framework version, fall back to lowest available).
3. For each picked framework, walk
   `<release_root>/.smith/templates/<fw>/<ver>/skills/` and drop skills whose
   central tech is absent from the project stack (e.g. drop
   `i18n-transloco` when `transloco` isn't in the stack).
4. For each kept skill, dispatch **`smith-single-template-adapter`**
   in parallel (single `Agent` batch). The adapter reads the release
   `SKILL.md`, leaves the frontmatter untouched, rewrites the body
   (resolves `{{placeholder}}` markers + prunes absent-tech sections),
   and returns the adapted file content + a change log :
   ```json
   {
     "from_template":   "<release-relative source path>",
     "destination":     "<consumer abs path = paths.skill.format(slug=smith-<fw>-<slug>)>",
     "content":         "<full adapted SKILL.md>",
     "skill_entry":     { "name": "smith-<fw>-<slug>", "path": "...", "adapted_at": "..." },
     "changes":         [{ "type": "...", "...": "..." }, ...]
   }
   ```
5. The orchestrator writes each returned `content` to its
   `destination` (verify path stays inside `<consumer>`). Upsert
   every `skill_entry` into `.smith/config.json::skills[]`. Atomic
   write.

A non-load-bearing `.smith/GENERATION_REPORT.MD` is emitted from the
collected change logs.

### Step 6 — Write `AGENTS.md` (sub-agent)

Dispatch **`smith-new-project-agents-writer`** with
`consumer_project_dir`, the original `description`, and
`bootstrap_results: []`. It assembles the payload for
`/smith-agents-md-write`, invokes the skill, atomic-writes
`AGENTS.md`. Idempotent : refuses to overwrite an existing
`AGENTS.md`.

### Step 7 — Verification sub-agent

Dispatch **`smith-new-project-verifier`**. Confirms `.smith/smith.yaml`,
`architecture.json`, `config.json` shapes ; every
`bundles[].files[].destination` exists ; every `skills[].path`
exists ; `AGENTS.md` is ≤100 lines. Returns a structured
`VerifyReport`. Failures **do not roll back** — surfaced in the
final report.

### Step 8 — Scaffold project source (coordinator sub-agent)

Dispatch **`smith-new-project-scaffold-coordinator`** with
`consumer_project_dir`, `description`, and `discovery_hints` (built
from Step 2 answers + `assumed_defaults[]` + framework defaults).
The coordinator picks every `smith-<fw>-bootstrap` skill installed
at Step 5, runs the conflict guard on declared output paths, fans
out one `smith-new-project-bootstrapper` per framework in parallel,
and returns a `ScaffoldReport`.

🚫 Zero interactive questions. Every bootstrap Phase 0 answer is
pre-resolved in `discovery_hints` ; bootstrapper sub-agents have
standing instructions to answer from defaults rather than ping the
user.

If `discovery_hints` lacks an answer for a question, the bootstrapper
falls back to that framework's documented default — never to a user
prompt.

### Step 9 — Write the run report

Dispatch the sibling skill **`smith-report-write`** with the full
`TraceLog`. Produces `.smith/report.md` (overwritten on every run)
covering arguments, per-step timings, bundles installed, templates
installed (kept / rejected / pruned), scaffolded frameworks,
AGENTS.md status, verifier checks, next-step suggestions.

### Final user-facing summary

```
✅ Smith new-project run completed in {{T}}s.
.smith/smith.yaml          : <created|reused>
.smith/architecture.json   : <created|skipped>
.smith/config.json         : <created|skipped>
AGENTS.md                  : <created|skipped>

Bundles installed   : {{B_OK}} ok, {{B_FAIL}} failed.
Templates installed : {{T_OK}} ok, {{T_FAIL}} failed.
Bootstrap scaffold  : {{S_OK}} ok, {{S_FAIL}} failed, {{S_SKIP}} skipped.
Verifier            : {{V_PASS}}/{{V_TOTAL}} checks passed.

Full report : .smith/report.md
```

## What you do NOT do

- **Don't** branch on provider in this skill or any sub-agent. Every
  provider-specific path lives in `<release_root>/paths.yaml`.
- **Don't** read source-side `cli/bundles/`, `cli/templates/`, or
  `cli/providers/`. The consumer-side workflow only reads
  `<release_root>/`.
- **Don't** resolve `@smith-include` directives — they were resolved
  at release-build time. Encountering one in a release artefact is a
  `release-build-broken` failure.
- **Don't** scaffold framework code yourself ; Step 8 delegates to
  per-framework `bootstrap` skills.
- **Don't** call `/smith-init` if `.smith/smith.yaml` exists.
- **Don't** overwrite an existing `AGENTS.md`, `architecture.json`,
  or `config.json`. Steps 1 + 3 + 6 short-circuit when files already
  exist ; Steps 4 / 5 / 8 still upsert.
