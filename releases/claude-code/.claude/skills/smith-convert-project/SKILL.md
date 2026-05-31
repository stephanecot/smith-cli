---
name: smith-convert-project
description: Converts an EXISTING project into a Smith-managed workspace from a pre-built release tree. 8-step agentic workflow — `/smith-init`, stack detection (read consumer source) + discovery (ask only genuine gaps), `.smith/architecture.json` + `.smith/config.json`, bundle installs (filter + copy from `<release>/.smith/bundles/`), **framework** template installs in `mode=convert` (`<release>/.smith/templates/framework/` — N skills per framework, adapted to the project's observed conventions by reading its source), AGENTS.md, verifier, run report. **No bootstrap step** — the source tree already exists and is never scaffolded. Reads consumer-side install paths from `<release>/.smith/paths.yaml` so the skill body is identical across providers (claude-code / github-copilot / opencode). Trigger with `/smith-convert-project "<description>"`.
---

# Skill — `/smith-convert-project`

Brownfield orchestrator. Wires an EXISTING project into Smith
from the pre-built release tree this skill ships inside.

The key contract difference vs `/smith-new-project` : the project
source already exists. We never scaffold ; we adapt every
installed skill to the project's observed conventions.

## 🚫 Absolute rule — NEVER mutate the consumer source code

This skill (and every sub-agent it dispatches) MUST treat the
consumer's existing source tree as **strictly read-only**. The
only writes allowed are inside Smith-managed locations :

- `.smith/` (architecture.json, config.json, smith.yaml, report.md,
  GENERATION_REPORT.MD)
- The provider's runtime root paths declared in
  `<release_root>/paths.yaml` (`paths.skill.format(...)`,
  `paths.agent.format(...)`, `paths.hook_dir.format(...)`)
- The consumer settings file at `paths.settings` (JSON-fragment
  merges only — never wholesale rewrite)
- `AGENTS.md` at the project root (created only if absent ;
  never edited if present)

**Forbidden — no exceptions :**

- Reformatting, renaming, or rewriting any existing source file.
- Adding new source files outside the Smith-managed paths above
  (no `src/utils/smith_helpers.py`, no `lib/smith.ts`, no
  scaffolded modules, no example code).
- Editing existing config files (`pyproject.toml`, `package.json`,
  `pom.xml`, `tsconfig.json`, `.eslintrc`, `ruff.toml`, etc.).
- Editing `Dockerfile`, `docker-compose.yml`, `.env`, `.env.example`,
  or any other infra/runtime config the project owns.
- Editing tests or running `--fix` / formatters on any file.
- Modifying `.git/`, `.gitignore`, or any VCS state.

If you find yourself about to write to a path that is not in the
allow-list above, **stop**. Either you are about to violate the
contract (refuse) or you found a missing entry in `paths.yaml`
(report it as a release-build bug, do not improvise).

Sub-agents inherit this rule. The adapter reads source files to
learn conventions but never writes to them ; the detector reads
manifests but never writes. The orchestrator owns every write and
verifies each destination is inside the allow-list before calling
the file API.

## Release-tree model

This skill is part of a `/smith-build` release. `<release_root>/`
is the directory containing this skill ; resolve it by walking up
from the running skill's location until you find a `.smith/`
directory with `paths.yaml` + `bundles/` + `templates/` inside.
The tree :

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
        └── framework/                            ← category : N skills per (name, version)
            ├── index.json
            └── <name>/<version>/
                ├── config.yaml
                └── skills/<slug>/SKILL.md        ← real skill ; body still has
                                                    {{placeholder}} + stack-gated sections
```

The release also ships a `bootstrap/` category under
`templates/`. **This skill ignores it entirely** — bootstrap
scaffolders are for greenfield use only.

Plus the provider's runtime root (`.claude/skills/` + `.claude/agents/`,
or `.github/prompts/` + `.github/agents/`, or `.opencode/commands/` +
`.opencode/agents/`) holding the Smith bin skills + sub-agents.

`.smith/paths.yaml` carries every provider-specific path template
used by this workflow :

```yaml
skill:      "<template using {slug}>"    # consumer destination for installed skills
agent:      "<template using {slug}>"    # consumer destination for installed agents
hook_dir:   "<template using {bundle}>"  # where standalone bundle hook files land
script_dir: "<scripts directory>"        # where bundle sidecar scripts land ; fragments reference this path
settings:   "<consumer settings file>"   # for *.hooks.json fragment merges ; may be null
```

Read `.smith/paths.yaml` once at the start of the workflow and
reuse it throughout. **The skill body never branches on provider** —
every provider-specific concern is encoded in this file.

## How to invoke

```
/smith-convert-project "<description>"
```

`<description>` is required ; if missing, ask via `AskUserQuestion`.
There is no `--provider` flag — the provider was chosen when the
release was built ; this skill is provider-agnostic.

## Pre-flight

- Current working directory must be writable AND must look like
  an existing project (not empty). If the directory is empty or
  contains only `.git/`, refuse with `empty-project` and suggest
  `/smith-new-project` instead.
- Resolve `<release_root>` ; it must contain `.smith/paths.yaml`,
  `.smith/bundles/`, `.smith/templates/framework/`. Refuse with
  `release-not-found` otherwise. Note : `templates/bootstrap/` is
  not required by this skill.
- Git is recommended but not mandatory. We do NOT check whether
  the tree is clean — the user is in charge of their workspace.

## Workflow

Strictly sequential at the orchestrator level. Parallelism happens
inside Step 5 (one adapter sub-agent per framework-template skill,
all in `mode=convert`). Each step appends timing + outcomes to a
`TraceLog` that Step 8 dumps into `.smith/report.md`.

### Step 1 — `/smith-init` (conditional)

If `.smith/smith.yaml` already exists, skip. Otherwise dispatch the
sibling skill `smith-init`, then re-read `.smith/smith.yaml` to
confirm the marker.

### Step 2 — Stack detection + discovery (two sub-agents)

This step is the load-bearing difference vs `/smith-new-project`.
Run two sub-agents in sequence :

**Step 2.a — `smith-stack-detector`** (MANDATORY).

Dispatch with `consumer_project_dir` and `description`. The
detector walks the project's manifests + framework configs and
returns a `seed_stack` populated from observed evidence, plus a
`gaps[]` list and an `evidence[]` audit trail. Read-only.

```json
{
  "status":     "ready | failed",
  "reason":     "<token or null>",
  "seed_stack": { ...partial ProjectStack... },
  "evidence":   [{ "field": "...", "source": "...", "value": "..." }, ...],
  "gaps":       [{ "field": "...", "reason": "..." }, ...],
  "files_read": ["...", "..."]
}
```

On `status=failed`, `reason=no-manifest-found`, continue to Step
2.b with an empty `seed_stack` — the discoverer will run a full
interactive pass as it would for a greenfield. On
`reason=consumer-dir-not-readable`, surface and exit.

**Step 2.b — `smith-stack-discoverer`** (MANDATORY sub-agent dispatch
— never inline). Pass `description`, `consumer_project_dir`, and the
detector's `seed_stack` as `seed_stack` input. The discoverer treats
every populated entry as anchored and only asks about genuine gaps
via `AskUserQuestion`. It returns the same shape as in
`/smith-new-project` Step 2 :

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

Persist the detector's `evidence[]` + `files_read[]` into the
TraceLog so Step 8 can render a "detected from your source"
section in the report.

### Step 3 — Write `.smith/architecture.json` + `.smith/config.json`

Read canonical templates from the sibling skills
`smith-architecture-format` and `smith-config-format`. Fill from the
discovery stack ; atomic-write both files. `config.json` starts as
an empty shell ; Steps 4 + 5 upsert into it.

If `.smith/architecture.json` or `.smith/config.json` already
exists, **do not overwrite**. Read it, merge the new stack into
its `project.*` block (preserving any user edits), and atomic-write
the merged result. Log a `merged-existing` note in the trace.

### Step 4 — Bundle installs (filter + copy)

Pure filter + copy ; no sub-agent.

0. **Propagate `paths.yaml` to the consumer** (one-time). If
   `<consumer>/.smith/paths.yaml` does not exist, copy
   `<release_root>/.smith/paths.yaml` to it verbatim. Atomic write.
   Consumer-installed skills (e.g. the `dashboard-ai` bundle) read
   this file at runtime so their bodies stay provider-agnostic —
   no per-provider table inside the bundle.
1. Read `<release_root>/.smith/bundles/index.yaml`.
2. Pick bundles using the union of two rules — a bundle is picked
   if EITHER condition holds :
   - `core: true` on the bundle entry. **Core bundles are
     always installed**, regardless of stack tags. Today the
     only one is `ia-stats` ; future base bundles join the same
     auto-install set. See `smith-bundle-format::Core bundles`.
   - `tags[]` intersect the project's stack tags (union of
     `tags[]` across every entry in `architecture.json`).
3. For each picked bundle, in deterministic alphabetical order :
   - For each `skill` in the bundle's `config.yaml::skills[]`, copy
     `<release_root>/.smith/bundles/<bundle>/skills/<slug>/SKILL.md` to
     `<consumer>/<paths.skill.format(slug=<slug>)>`.
   - If `<release_root>/.smith/bundles/<bundle>/skills/<slug>/assets/`
     exists, copy its tree verbatim to
     `<consumer>/.smith/skills/<slug>/assets/` (preserving file
     modes — Node scripts may need the executable bit). Missing
     bucket → no-op.
   - For each file under `<release_root>/.smith/bundles/<bundle>/hooks/` :
     - If `paths.settings` is non-null AND the filename matches
       `*.hooks.json` → merge the JSON fragment into
       `<consumer>/<paths.settings>` tagged with
       `_smith_source: <bundle>`.
     - Else (sidecar script — `.js` / `.sh` / `.py` / `.ts`) → copy
       verbatim to `<consumer>/<paths.script_dir>/<file>`, setting the
       executable bit on `.js` / `.sh` / `.py`. This is the path the
       merged fragment's command references (e.g.
       `node .claude/scripts/append-ia-stats.js`), so `script_dir`
       and the fragment MUST stay consistent — same convention as
       `/smith-bundle-install`.
4. Upsert `.smith/config.json::bundles[]` with one entry per bundle
   listing the consumer-relative paths written. Atomic write of
   `config.json` at the end, bump `generated_at`.

Per-bundle failure is logged in the trace and skipped — never roll
back the others.

### Step 5 — Framework template installs (filter + adapter in `convert` mode)

The release ships two template categories — `framework/` and
`bootstrap/`. This skill installs `framework/` only.

1. Read `<release_root>/.smith/templates/framework/index.yaml`.
2. Pick (framework, version) pairs matching the project's stack
   (`framework` ∈ `architecture.json::frameworks[].name` ; version
   per the downward-match rule — highest template version `≤` the
   project's framework version, fall back to lowest available).
3. For each picked framework, walk the entry's `skills[]` in
   `framework/index.json` (each carries `name`, `version`, `tags`)
   and **keep only skills whose `tags[]` intersect the project's
   stack tags** (union of `tags[]` across every entry in
   `architecture.json`). The corresponding skill directory in the
   release lives at
   `<release_root>/.smith/templates/framework/<fw>/<ver>/skills/<installed-name>/`
   — already named after the installed slug (`smith-<fw>-<localslug>`),
   iso-name rule applied at build time.
4. For each kept skill, dispatch **`smith-single-template-adapter`**
   in parallel (single `Agent` batch) with :
   ```json
   {
     "template_path":         "<absolute path to release SKILL.md>",
     "project_stack":         { ...from architecture.json... },
     "destination":           "<consumer abs path = paths.skill.format(slug=<installed-name>)>",
     "mode":                  "convert",
     "consumer_project_dir":  "<consumer abs path>"
   }
   ```
   The adapter resolves placeholders + prunes absent tech, then —
   because `mode=convert` — mines the consumer source under
   `consumer_project_dir` to anchor the body on observed
   conventions (layout, naming, framework patterns, tooling
   configs). It returns adapted content + a change log that may
   include `convention_anchored` and `convention_unclear` entries
   on top of the standard set.
5. The orchestrator writes each returned `content` to its
   `destination` (verify path stays inside `<consumer>`). Upsert
   every `skill_entry` into `.smith/config.json::skills[]`. Atomic
   write.

A non-load-bearing `.smith/GENERATION_REPORT.MD` is emitted from the
collected change logs ; the `convention_anchored[]` + `convention_unclear[]`
sections are the most useful surfaces for the user reviewing the
conversion.

### Step 6 — Write `AGENTS.md` (sub-agent)

Dispatch **`smith-project-agents-writer`** with
`consumer_project_dir`, the original `description`, and
`bootstrap_results: []` (always empty — no scaffolding happened).
It assembles the payload for `/smith-agents-md-write`, invokes the
skill, atomic-writes `AGENTS.md`. Idempotent : refuses to overwrite
an existing `AGENTS.md`.

### Step 7 — Verification sub-agent

Dispatch **`smith-project-verifier`**. Confirms `.smith/smith.yaml`,
`architecture.json`, `config.json` shapes ; every
`bundles[].files[].destination` exists ; every `skills[].path`
exists ; `AGENTS.md` is ≤100 lines. Returns a structured
`VerifyReport`. Failures **do not roll back** — surfaced in the
final report.

### Step 8 — Write the run report

Dispatch the sibling skill **`smith-report-write`** with the full
`TraceLog`. Produces `.smith/report.md` (overwritten on every run)
covering : arguments, per-step timings, detector evidence + files
read, discovery questions asked + assumed defaults, bundles
installed, templates installed (kept / rejected / pruned),
conventions anchored + unclear (from adapter change logs),
AGENTS.md status, verifier checks, next-step suggestions.

### Final user-facing summary

```
✅ Smith convert-project run completed in {{T}}s.
.smith/smith.yaml          : <created|reused>
.smith/architecture.json   : <created|merged>
.smith/config.json         : <created|merged>
AGENTS.md                  : <created|skipped>

Detector             : {{N_FILES}} files read, {{N_EVIDENCE}} fields detected, {{N_GAPS}} gaps surfaced.
Bundles installed    : {{B_OK}} ok, {{B_FAIL}} failed.
Templates installed  : {{T_OK}} ok, {{T_FAIL}} failed.
Conventions anchored : {{C_ANCHORED}} matched, {{C_UNCLEAR}} unclear.
Verifier             : {{V_PASS}}/{{V_TOTAL}} checks passed.

Full report : .smith/report.md
```

## What you do NOT do

- **Don't** scaffold source code. The project already exists.
  Bootstrap templates (`<release>/.smith/templates/bootstrap/`)
  exist in the release tree but are out of scope for this skill —
  never read, never install, never dispatch.
- **Don't** dispatch `smith-new-project-scaffold-coordinator` or
  `smith-new-project-bootstrapper`. Those are greenfield-only.
- **Don't** branch on provider in this skill or any sub-agent.
  Every provider-specific path lives in
  `<release_root>/paths.yaml`.
- **Don't** read source-side `bundles/`, `templates/`, or
  `providers/`. The consumer-side workflow only reads
  `<release_root>/`.
- **Don't** resolve `@smith-include` directives — they were resolved
  at release-build time. Encountering one in a release artefact is a
  `release-build-broken` failure.
- **Don't** call `/smith-init` if `.smith/smith.yaml` exists.
- **Don't** overwrite an existing `AGENTS.md`. Step 6 short-circuits
  if it already exists. Steps 3 and 4 / 5 merge / upsert rather
  than overwrite.
- **Don't** mutate the consumer's source tree — period. See the
  absolute rule at the top of this skill. The adapter rewrites
  the **template** to match the **project**, never the other way
  round. No formatter runs, no auto-fix, no scaffolded files
  outside the Smith-managed paths.
