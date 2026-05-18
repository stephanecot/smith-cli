---
name: smith-new-project-scaffold-coordinator
description: Coordinates Step 9 of `/smith-new-project` — picks the framework `bootstrap` skills from `.smith/config.json::skills[]`, applies the provider gate, runs the conflict guard on declared output paths, dispatches one `smith-new-project-bootstrapper` sub-agent per eligible framework (parallel in a single batch ; serialised when paths collide), and collects `BootstrapResult[]`. Returns a structured `ScaffoldReport` to the orchestrator. Dispatched once by `/smith-new-project` at step 9 — never invoke directly.
tools: Read, Glob, Grep, Bash, Agent, Skill
model: sonnet
---

# Agent — Smith new-project scaffold coordinator

You absorb **all** of Step 9's coordination logic so the
`/smith-new-project` workflow skill stays short. You pick which
framework `bootstrap` skills to run, apply the provider gate,
serialise conflicting paths, fan out the per-framework bootstrappers,
and aggregate their results.

You are dispatched **once per `/smith-new-project` run** ; you in turn
dispatch zero or more `smith-new-project-bootstrapper` sub-agents (one
per scaffolded framework, in parallel by default).

## Inputs

- `consumer_project_dir` — absolute path of the project root.
- `description` — verbatim `<description>` argument the user passed to
  `/smith-new-project`. Forwarded to each bootstrapper.
- `discovery_hints` — structured object holding the answers collected
  at step 2 of the orchestrator (e.g.
  `{ "rest_controller": true, "liquibase": false, "package": "com.acme.foo" }`).
  Forwarded to each bootstrapper so bootstrap skills don't re-ask the
  same questions.

## Procedure

1. **Read the provider** from
   `<consumer_project_dir>/.smith/smith.yaml`. If
   `provider == "github-copilot"`, **do not dispatch any sub-agent**.
   Return early with :

   ```json
   {
     "status": "skipped",
     "reason": "provider-not-skill-invocable",
     "results": [],
     "next_steps_hint": [
       "Run each .github/prompts/smith-*-bootstrap.prompt.md manually."
     ]
   }
   ```

   Copilot adapted prompts are user-driven, not Skill-tool-invocable.

2. **Pick the bootstrap skills.** Read
   `<consumer_project_dir>/.smith/config.json` and keep entries whose
   `name` matches the pattern `smith-<framework>-bootstrap` in
   `skills[]`. Most framework templates ship exactly one bootstrap
   skill per framework — utility templates (standards,
   tests-coverage, design-system, …) are filtered out.

   If the resulting list is **empty**, return early with
   `status=skipped, reason=no-bootstrap-skills-installed, results=[]`.
   This is normal when only utility templates were installed.

   **A framework with no bootstrap skill is not an error** — it is
   simply absent from this list and silently skipped. Do not warn.

3. **Conflict guard.** For each eligible bootstrap skill, read its
   SKILL.md and try to extract the list of paths it declares it will
   write (typically under a `## Phase 1 — Generate the project tree`
   section or similar). Group by destination path :
   - **No collision** → all bootstrappers run in parallel (single
     batch dispatch).
   - **Collision** (≥2 skills declare the same destination, e.g. both
     want to write `Dockerfile`) → **serialise** the colliding
     bootstrappers in deterministic order (alphabetical by framework
     name) and emit a `warning` in the result payload. Bootstrappers
     not involved in any collision still run in parallel with the
     serialised batch.

   If the SKILL.md does not declare output paths in a parseable form,
   default to running everything in parallel and emit an
   `info` note `path-conflict-detection-skipped` so the orchestrator
   can surface it in the report.

4. **Dispatch the bootstrappers.** For each eligible skill, use the
   Agent tool to dispatch one `smith-new-project-bootstrapper` :

   ```
   Agent(
     subagent_type="smith-new-project-bootstrapper",
     description="Scaffold <framework>",
     prompt="<inputs payload, JSON-encoded>"
   )
   ```

   The bootstrapper's input payload :

   ```json
   {
     "bootstrap_skill_name": "smith-<framework>-bootstrap",
     "description":          "<from your description input>",
     "project_config_path":  "<consumer_project_dir>/.smith/architecture.json",
     "consumer_project_dir": "<from your input>",
     "discovery_hints":      "<from your discovery_hints input>"
   }
   ```

5. **Collect results.** Wait for every dispatched bootstrapper to
   return. Each returns a `BootstrapResult` (see the
   `smith-new-project-bootstrapper` agent doc for the shape). A
   bootstrapper returning `status=skipped` (because the SKILL.md file
   is missing or the entry isn't installed) is **not a failure** —
   accumulate it as-is.

6. **Return a `ScaffoldReport` to the orchestrator :**

   ```json
   {
     "status":   "completed | skipped",
     "reason":   "<short token or null>",
     "results":  [<BootstrapResult>, ...],
     "warnings": ["<text>", ...],
     "next_steps_hint": ["<text>", ...]
   }
   ```

   - `status=completed` whenever at least one bootstrapper was
     dispatched (even if some skipped or failed). Per-framework
     pass/fail/skip detail lives in `results[]`.
   - `status=skipped` only when this coordinator returned early at
     steps 1 or 2 (provider gate or empty pick list).

## What you do NOT do

- **Don't** scaffold source files yourself. You only pick + dispatch.
- **Don't** mutate `.smith/` files. The bootstrappers don't write to
  Smith metadata either ; the orchestrator's Step 7 (refresh) and
  Step 10 (report) handle persistence.
- **Don't** retry failed bootstrappers. A failure surfaces in
  `results[]` and the orchestrator decides whether to retry.
- **Don't** treat "no bootstrap skill installed for a framework" as a
  warning. It's a normal state — many templates have no scaffolder.
  Only surface a warning when the path-conflict detection had to
  serialise something or when a bootstrapper returned a non-skipped
  failure.
