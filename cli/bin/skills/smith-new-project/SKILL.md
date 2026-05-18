---
name: smith-new-project
description: Bootstraps a brand-new project end-to-end. 10-step agentic workflow — `/smith-init` (if needed), interactive stack discovery, `.smith/architecture.json` + `.smith/config.json` shells, parallel bundle installs (one sub-agent per bundle via `/smith-bundle-install`), parallel template installs (one sub-agent per template via `/smith-template-install`), AGENTS.md generation (sub-agent `smith-new-project-agents-writer` → skill `/smith-agents-md-write`, ≤100 lines), smith-config refresh, verification sub-agent, **then scaffold the project source** via the `smith-new-project-scaffold-coordinator` sub-agent (which fans out one `smith-new-project-bootstrapper` per framework bootstrap skill ; tolerates missing or absent bootstraps), and finally a markdown report under `.smith/report/` capturing the full run including the scaffold. Trigger with `/smith-new-project "<description>" [--provider claude-code|github-copilot]`.
---

# Skill — `/smith-new-project`

Greenfield orchestrator. Takes a one-line project description and ends
with a runnable Smith-managed workspace : Smith metadata (configs +
`AGENTS.md`) written and verified first, then **the project's source
tree scaffolded** by the framework `bootstrap` skills (Claude Code
provider only), and finally a report under `.smith/report/` that
captures the full run including the scaffold.

This skill **does not author scaffolded source files itself** — Step 9
delegates that to the per-framework `bootstrap` skills that Step 5
adapted. The orchestrator stays a thin coordinator : it picks bundles
and templates, fans out installs / scaffolds in parallel, audits the
Smith metadata, then reports.

For greenfield projects only. For converting an existing project, see
`/smith-convert-project` (separate skill, not authored yet).

## How to invoke

```
/smith-new-project "<description>" [--provider claude-code|github-copilot]
```

- `<description>` — required. One-line natural-language summary of the
  project. Drives stack discovery, lands in `architecture.json` /
  `AGENTS.md` / the report.
- `--provider` — optional, defaults to `claude-code`. Selects the AI
  tool Smith targets across the workflow.

If `<description>` is missing, ask via `AskUserQuestion`.

## Pre-flight

- Working directory must be a writable filesystem. Refuse with a clear
  error otherwise.
- Git is recommended but not mandatory. If the project is not a git
  working tree, warn and continue — `git_sha` lands as `null` in the
  config files.

## Workflow (10 steps)

The workflow is **strictly sequential at the orchestration level**.
Parallelism happens **inside** steps 4, 5 and 9 (one sub-agent per
bundle / template / bootstrap skill, dispatched in a single batch).
Each step records timing + created files into a running `TraceLog`
that step 10 dumps into the final report.

### Step 1 — `/smith-init` (conditional)

- If `.smith/smith.yaml` already exists, skip and log
  `SKIPPED smith-init (already initialised, provider=<from yaml>)`.
- Otherwise dispatch the sibling skill
  **`smith-init`** with the resolved `--provider`. Wait for it to
  return, then re-read `.smith/smith.yaml` to confirm the marker is
  present.

The provider Smith targets for the rest of the workflow comes from
`.smith/smith.yaml` (single source of truth past this point) — even
when the user passed `--provider` and the file already existed.

### Step 2 — Stack discovery (interactive)

Parse `<description>` for explicit signals : languages, frameworks,
versions, databases, infra hints. Build a draft `ProjectStack` (same
shape as `.smith/architecture.json` — see the sibling skill
**`smith-architecture-format`** for the canonical schema).

For every **structuring** signal the description doesn't pin down, ask
**one focused question** via `AskUserQuestion`. Stop asking as soon as
the stack is implementable. Examples of structuring questions :

- "Frontend framework + version ?" (Angular 21 / React 19 / Vue 3 / none)
- "Backend framework + version ?" (Spring Boot 4 / Quarkus 3 / FastAPI / none)
- "Primary database ?" (PostgreSQL / MySQL / MongoDB / none)
- "Build tool ?" (only if ambiguous — defaults are deterministic)
- "Test stack ?" (only if the framework has multiple idiomatic options)

Skip questions whose answer is obvious from the description or from
framework defaults (e.g. "Spring Boot" → Maven by default, no need to
ask unless the user mentioned Gradle).

The user may also paste a richer brief at this step — accept it and
re-parse before re-asking.

### Step 3 — Write `.smith/architecture.json` + empty `.smith/config.json` shell

Consult the sibling skills **`smith-architecture-format`** and
**`smith-config-format`** for the canonical shape of both files. The
templates live next to them at
`${CLAUDE_SKILL_DIR}/../smith-architecture-format/template/architecture.template.json`
and
`${CLAUDE_SKILL_DIR}/../smith-config-format/template/config.template.json`.

Write both files **before** dispatching any sub-agent, in this order :

1. `.smith/architecture.json` — fill from the discovery stack. Drop
   `_comment` fields. Atomic write (tempfile → fsync → rename).
2. `.smith/config.json` — fill the empty shell : provider from
   `.smith/smith.yaml`, `skills: []`, `bundles: []`,
   `specifications.*` paths pointing at files that don't exist yet,
   `ai_memory_file: "AGENTS.md"`. Atomic write.

Steps 4 and 5 upsert into `config.json` ; it MUST exist before
they run.

### Step 4 — Bundle installs (planner sub-agents + orchestrator-side writes)

Read `cli/bundles/config.json` (CLI catalogue, read-only). Pick every
bundle whose `tags[]` intersect with the project's stack tags (computed
from `architecture.json`). At minimum, prefer the bundles that target
the provider chosen in `.smith/smith.yaml`.

**Two-phase design — planner + executor.** The bundle-installer
sub-agents are dispatched in parallel **as planners** : each reads
the bundle's source + assembles the `@smith-include` resolutions in
its own context window (heavy reading work, kept off the
orchestrator's context) and returns a structured `BundlePlan`. The
orchestrator then executes every plan from its own persistent thread
(lightweight write ops, immune to worktree-isolation cleanups that
previously wiped sub-agent writes mid-flow).

**Phase A — Plan (parallel sub-agents)**

Dispatch **one `smith-new-project-bundle-installer` sub-agent per
selected bundle**, in a single batch. Each sub-agent receives :
- `bundle_name`, `provider`, `consumer_project_dir`.

Each returns a `BundlePlan` :
```json
{
  "bundle":       "<name>",
  "status":       "ready | skipped | failed",
  "reason":       "<token or null>",
  "writes":       [{ "destination": "<abs>", "content": "<full>", "kind": "skill|agent" }, ...],
  "copies":       [{ "source": "<abs>", "destination": "<abs>", "executable": <bool> }, ...],
  "hook_merges":  [{ "target": "<abs>/.claude/settings.json",
                     "source_tag": "<bundle>",
                     "fragment": { "hooks": {...} } }, ...],
  "bundle_entry": { ... }   // for config.json::bundles[]
}
```

Sub-agents do NOT write to the consumer disk — see the
`smith-new-project-bundle-installer` agent doc for why.

**Phase B — Execute (orchestrator thread, serial)**

After all plans are collected, the orchestrator executes them
sequentially from its own thread :

1. For each plan with `status: "ready"`, in deterministic
   alphabetical bundle order :
   - Create parent directories for every `writes[].destination` and
     `copies[].destination`.
   - For each `writes[]` entry : use the `Write` tool to write the
     `content` to `destination`. Verify destination starts with
     `<consumer_project_dir>` (path-escape guard).
   - For each `copies[]` entry : use `Bash(cp source destination)`
     atomically ; set executable bit on `.py` / `.sh` / `.js` when
     `executable: true`.
   - For each `hook_merges[]` entry : open the target settings file
     (create empty `{}` if missing), drop entries where
     `_smith_source == source_tag`, append fragment entries tagged
     with `_smith_source: source_tag`, write back. Refuse if target
     is `.claude/settings.local.json` (hooks are team-wide).

2. After all bundle writes succeed, do **ONE serial upsert** of
   `.smith/config.json` : read current file, upsert every
   `bundle_entry` from collected plans into `bundles[]` (keyed by
   `name`), bump `generated_at`, atomic-write.

3. Per-plan failure (`status: failed`) : skip its writes, log
   reason for the report, continue with remaining plans.

### Step 5 — Template installs (planner sub-agents + orchestrator-side writes)

Read `cli/templates/index.json`. Pick every template whose `framework`
appears in `architecture.json::frameworks[].name` (Angular 21,
java-spring-boot 4, etc.). Resolve version per the documented downward
match rule (see `smith-template-install`).

**Same two-phase design as step 4 — planner sub-agents + serial
orchestrator writes.** Template adaptation is significantly heavier
than bundle reading (each framework has 5–6 SKILL bodies to adapt via
the `smith-template-customizer` → `smith-single-template-adapter`
chain), so context isolation via sub-agents is even more important
here than for bundles.

**Phase A — Plan (parallel sub-agents)**

Dispatch **one `smith-new-project-template-installer` sub-agent per
selected framework**, in a single batch. Each receives :
- `framework`, `version` (or `null`), `provider`, `consumer_project_dir`.

Each runs the customizer + adapter chain internally and returns a
`TemplatePlan` :
```json
{
  "framework":        "<name>",
  "version_resolved": "<v>",
  "status":           "ready | failed",
  "writes":           [{ "destination": "<abs>",
                         "content": "<full SKILL.md>",
                         "kind": "skill",
                         "from_template": "<source path>" }, ...],
  "skill_entries":    [{ "name": "smith-<fw>-<slug>", ... }, ...],
  "report_excerpt":   "...",
  "kept":             <int>,
  "rejected":         <int>,
  "flagged":          <int>,
  "pruned_tech_counts": { "<tech>": <count>, ... }
}
```

Sub-agents do NOT write to the consumer disk.

**Phase B — Execute (orchestrator thread, serial)**

After all plans are collected, the orchestrator executes them
sequentially :

1. For each plan with `status: "ready"`, in alphabetical framework
   order :
   - Create parent directories for every `writes[].destination`.
   - For each `writes[]` entry : `Write` the assembled SKILL content
     to `destination`. Verify path stays inside `<consumer_project_dir>`.

2. After all template writes succeed, do **ONE serial upsert** of
   `.smith/config.json` : merge with the upsert from step 4 if both
   happen in the same session — re-read the latest state, upsert
   every `skill_entries[]` from collected plans into `skills[]`
   (keyed by `name`), bump `generated_at`, atomic-write.

3. Per-plan failure : skip its writes, log reason, continue.

Template installs also emit `.smith/GENERATION_REPORT.MD` as a
secondary artefact via the customizer ; this is written from the
sub-agent context and is the one allowed exception to the no-write
rule (it is non-load-bearing — a regenerated audit trail, safe to
miss).

### Step 6 — Write `AGENTS.md` at the project root (sub-agent)

This step is **not inlined** — dispatch the dedicated sub-agent
**`smith-new-project-agents-writer`**. The sub-agent assembles the
`/smith-agents-md-write` payload from `.smith/architecture.json` +
`.smith/config.json` + `.smith/smith.yaml` + the original
`<description>` argument (and at this point in the workflow, no
bootstrap results — step 9 hasn't run yet, so it passes
`bootstrap_results: []`), then invokes the skill, which renders
the template, enforces the 100-line cap (truncating optional sections
in a documented order if needed), and atomic-writes `AGENTS.md` at the
project root.

The sub-agent receives :
- `consumer_project_dir` — absolute path of the project root ;
- `description` — verbatim `<description>` argument ;
- `bootstrap_results: []` — empty at step 6 ; populated only if the
  orchestrator re-dispatches the writer after step 9 (see below).

The sub-agent returns
`{ status, reason, path, lines, bytes, truncated[] }`. Surface any
`truncated[]` content as a warning in the trace log so it lands in
the final report.

Idempotent : the underlying skill refuses to overwrite an existing
`AGENTS.md`, so re-running this step on an already-bootstrapped
project is a safe no-op (`status=skipped, reason=already-present`).

**Optional refresh after step 9** : if step 9 actually scaffolds (i.e.
`provider == claude-code` and at least one bootstrap skill is
installed) AND `AGENTS.md` did not pre-exist (i.e. step 6 returned
`status=created`), the orchestrator may delete `AGENTS.md` and
re-dispatch this sub-agent with the populated `bootstrap_results` so
the "Source scaffold" section reflects what was actually generated.
This is opt-in : default behaviour is to keep the brief from the
first write (which already lists frameworks that will be scaffolded,
just without per-framework file counts).

### Step 7 — Refresh `.smith/config.json`

Steps 4 and 5 have already upserted into
`config.json::bundles[]` and `skills[]`. Scaffold (Step 9) runs
**after** this refresh, so its source files are not yet known here.
This step is a **read-back + sanity check** of the Smith metadata as
it stands before scaffolding :

1. Read the current `config.json`.
2. Verify the file conforms to the shape documented in
   `smith-config-format` (top-level keys present, arrays well-typed,
   `generated_at` ≤ now).
3. Refresh `generated_at` to the current ISO-8601 UTC.
4. Atomic write.

If the file is malformed, fail loudly and emit a diagnostic — do not
silently rewrite, because that would lose data the install skills
produced.

### Step 8 — Verification sub-agent

Dispatch a single **`smith-new-project-verifier`** sub-agent. It walks
the consumer project and confirms :

- `.smith/smith.yaml` exists with `enabled: true` ;
- `.smith/architecture.json` validates against
  `smith-architecture-format` ;
- `.smith/config.json` validates against `smith-config-format` ;
- every file listed in `config.json::bundles[].files[]`
  exists on disk at its `destination` ;
- every file referenced by `config.json::skills[].path` exists ;
- `AGENTS.md` exists and is ≤100 lines.

The verifier returns a structured `VerifyReport` :
`{ checks: [{name, status: pass|fail|warn, detail}], counts, failed[] }`.

Verification failures **do not roll back** the workflow — they are
surfaced in the final report so the user can decide.

### Step 9 — Scaffold the project source (coordinator sub-agent)

The Smith bootstrap is now fully in place — configs written, bundles +
templates installed, AGENTS.md present, smith-config refreshed,
verifier green. **Step 9 finally uses what was set up.** All the
coordination logic (picking framework bootstrap skills, provider gate,
conflict guard, parallel fan-out, results aggregation) lives in the
dedicated **`smith-new-project-scaffold-coordinator`** sub-agent — this
step just dispatches it.

**🚫 Never defer this step.** The orchestrator MUST execute Step 9 ;
emitting a message like "scaffold deferred — run `/smith-<fw>-bootstrap`
manually" is a contract violation. The whole point of Step 9 is to
remove that manual step. If the coordinator returns
`status=skipped` it is for one of two documented reasons only
(see below) — neither is "the orchestrator decided not to run".

**🚫 Zero interactive questions during the scaffold.** Bootstrap
skills' Phase 0 questions MUST be pre-answered by the orchestrator
before dispatch. Build a comprehensive `discovery_hints` object that
pins every question the bootstrap will ask, in this order of source :
1. Explicit signals already extracted from `<description>` (e.g.
   project name from the directory base name when the description
   doesn't pin it ; package coords from the description if mentioned).
2. Answers collected at Step 2 discovery.
3. **Framework defaults** for everything else — the bootstrap skill's
   own Phase 0 documents the default per question (e.g.
   `routing: on`, `tailwind: on`, `i18n: on (fr+en, fr default)`,
   `openapi: off`, `test: vitest`, `auth_shell: off` for Angular ;
   `liquibase: off`, `rest_controller: on` for Spring Boot).

The bootstrapper sub-agent has standing instructions to answer any
`AskUserQuestion` itself from these defaults (recording each in
`assumed_defaults[]`) — never to forward the question to the user
mid-workflow.

Dispatch one `smith-new-project-scaffold-coordinator` with :
- `consumer_project_dir` — absolute path of the project root ;
- `description` — the original `<description>` argument, verbatim ;
- `discovery_hints` — the **complete** structured object built above
  (description-derived + Step 2 + framework defaults). Every Phase 0
  question of every bootstrap skill MUST have an answer here.

Same **MANDATORY** isolation policy as steps 4 / 5 : dispatch the
coordinator (and through it, the bootstrappers) WITHOUT
`isolation: "worktree"`. Bootstrap writes go straight to the
consumer project tree.

The coordinator returns a `ScaffoldReport`
(`{ status, reason, results[], warnings[], next_steps_hint[] }`).
Two outcomes are normal and non-blocking :
- `status=skipped, reason=provider-not-skill-invocable` — Copilot
  provider ; surface the `next_steps_hint` entries in the final
  report so the user runs the prompts manually.
- `status=skipped, reason=no-bootstrap-skills-installed` — only
  utility templates were installed (standards, design-system, …).

When `status=completed`, accumulate the `BootstrapResult[]` entries
into the trace log for Step 10. **Per-framework skips inside `results[]`
are also normal** — many framework templates legitimately ship without
a `bootstrap` skill, and a missing SKILL.md on disk yields
`status=skipped` rather than failing the workflow.

**No rollback** on any partial failure : whatever the sub-agents wrote
to disk stays there for inspection. Failures (true ones, not skips)
become a warning block in the final report.

### Step 10 — Write the run report

Dispatch the sibling skill **`smith-report-write`** with the full
`TraceLog` collected across steps 1–9. It produces the project's
**single** run report at the fixed path `.smith/report.md`
(overwritten on every run) covering :

- arguments used (description, provider) ;
- per-step timings and outcomes ;
- bundles installed (name + version + files copied) ;
- templates built (framework + version + skills counts) ;
- bootstrapped frameworks (framework + files scaffolded + smoke-test
  status) ;
- AGENTS.md status ;
- verifier checks (table : pass / fail / warn) ;
- next-step suggestions (e.g. `/smith-generate-docs`,
  `/smith-dashboard`, "paste these hooks into `.claude/settings.json`",
  "run these Copilot prompts to scaffold the project").

### Final user-facing summary

```
✅ Smith new-project run completed in {{T}}s.
.smith/smith.yaml          : <created|reused>
.smith/architecture.json : <created|skipped>
.smith/config.json   : <created|skipped>
AGENTS.md                  : <created|skipped>

Bundles installed   : {{B_OK}} ok, {{B_FAIL}} failed.
Templates installed : {{T_OK}} ok, {{T_FAIL}} failed.
Bootstrap scaffold  : {{S_OK}} ok, {{S_FAIL}} failed, {{S_SKIP}} skipped.
Verifier            : {{V_PASS}}/{{V_TOTAL}} checks passed.

Full report : .smith/report.md
Next        : /smith-generate-docs · /smith-dashboard
```

## What you do NOT do

- **Don't** modify `cli/bundles/config.json` or `cli/templates/index.json` —
  those are CLI-maintainer territory (`/smith-bundle-add`,
  `/smith-template-add`).
- **Don't** scaffold framework code yourself. Step 9 delegates that to
  the framework `bootstrap` skills that were adapted in Step 5 — this
  orchestrator only dispatches them ; it never authors `pom.xml` /
  `package.json` / source files directly.
- **Don't** call `/smith-init` if `.smith/smith.yaml` already exists,
  even with `--force`. There is no `--force` here.
- **Don't** overwrite an existing `AGENTS.md`, `architecture.json`,
  or `config.json`. Re-running on a project that's already
  bootstrapped is partially idempotent : Steps 1 + 6 + 3 short-circuit ;
  Steps 4 / 5 / 9 still run and may upsert new bundles / templates /
  scaffold files ; Steps 7 + 8 + 10 always run.
- **Don't** dispatch the verifier (Step 8), scaffolder (Step 9) or
  report (Step 10) sub-agents in parallel with the install sub-agents —
  they need the install steps to be finished first.
- **Don't** dispatch bootstrap sub-agents for `github-copilot`. Their
  adapted prompts are user-driven, not skill-tool-invocable.

## Why this skill exists

Bootstrapping a Smith project used to be a manual chain : run
`/smith-init`, then `/smith-bundle-install` once per bundle, then
`/smith-template-install` once per framework, then write `AGENTS.md`
by hand, then run each framework `bootstrap` skill by hand to scaffold
the source tree, then check everything. This skill collapses that
chain into a single agentic workflow, with parallelism where it's safe
(bundle / template / bootstrap fan-outs are independent), Smith
metadata verified **before** scaffolding so the source step runs
against a known-good baseline, and a single report at the end covering
both Smith setup and the source scaffold.
