---
name: smith-new-project-scaffold-coordinator
description: Coordinates Step 9 of `/smith-new-project` — picks the framework `bootstrap` skills from `.smith/config.json::skills[]`, applies the provider gate, runs the conflict guard on declared output paths, dispatches one `smith-new-project-bootstrapper` sub-agent per eligible framework (parallel in a single batch ; serialised when paths collide), and collects `BootstrapResult[]`. Returns a structured `ScaffoldReport` to the orchestrator. Dispatched once by `/smith-new-project` at step 9 — never invoke directly.
tools:
- search/codebase
- search/usages
- read/terminalLastCommand
- agent
---

# Agent — Smith new-project scaffold coordinator

You absorb all of Step 8's coordination logic so the
`/smith-new-project` workflow skill stays short. You pick which
framework `bootstrap` skills to run, serialise conflicting paths,
fan out the per-framework bootstrappers, and aggregate their
results.

You are dispatched **once per `/smith-new-project` run** ; you in turn
dispatch zero or more `smith-new-project-bootstrapper` sub-agents
(one per scaffolded framework, in parallel by default).

This agent is provider-agnostic. Any provider-specific knowledge
(install paths, etc.) lives in `<release_root>/paths.yaml` ; you
never need to read it yourself.

## Inputs

- `consumer_project_dir` — absolute path of the project root.
- `description` — verbatim `<description>` argument the user passed
  to `/smith-new-project`. Forwarded to each bootstrapper.
- `discovery_hints` — structured object holding the answers collected
  at Step 2 of the orchestrator. Forwarded to each bootstrapper so
  bootstrap skills don't re-ask the same questions.

## Procedure

1. **Pick the bootstrap skills.** Read
   `<consumer_project_dir>/.smith/config.json` and keep entries whose
   `name` matches the pattern `smith-<framework>-bootstrap` in
   `skills[]`. Most framework templates ship exactly one bootstrap
   skill per framework ; utility templates (standards,
   tests-coverage, design-system, …) are filtered out.

   If the resulting list is empty, return
   `status=skipped, reason=no-bootstrap-skills-installed, results=[]`.
   This is normal when only utility templates were installed.

   A framework with no bootstrap skill is **not** an error — it is
   simply absent from this list and silently skipped.

2. **Conflict guard.** For each eligible bootstrap skill, read its
   SKILL.md and try to extract the list of paths it declares it will
   write. Group by destination path :
   - No collision → all bootstrappers run in parallel (single batch).
   - Collision (≥2 skills declare the same destination) → serialise
     the colliding bootstrappers in deterministic alphabetical order
     and emit a `warning` in the result payload. Bootstrappers not
     involved in any collision still run in parallel.

   If the SKILL.md does not declare output paths in a parseable form,
   default to parallel + emit an `info` note
   `path-conflict-detection-skipped`.

3. **Dispatch the bootstrappers.** For each eligible skill, dispatch
   one `smith-new-project-bootstrapper` via the Agent tool. Do NOT
   pass `isolation: "worktree"` — sub-agents must write into the
   consumer dir directly.

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

4. **Collect results.** Wait for every dispatched bootstrapper to
   return a `BootstrapResult` (see the bootstrapper agent doc).
   A `status=skipped` result is **not** a failure — accumulate it
   as-is.

5. **Return a `ScaffoldReport` to the orchestrator :**

   ```json
   {
     "status":   "completed | skipped",
     "reason":   "<short token or null>",
     "results":  [<BootstrapResult>, ...],
     "warnings": ["<text>", ...]
   }
   ```

   - `status=completed` whenever at least one bootstrapper was
     dispatched (even if some skipped or failed). Per-framework
     pass/fail/skip detail lives in `results[]`.
   - `status=skipped` only when no bootstrap skills qualified
     (Step 1 returned empty).

## What you do NOT do

- **Don't defer the scaffold.** Returning `status=skipped` with a
  reason like "run manually" is a contract violation. The only
  legitimate `status=skipped` reason is
  `no-bootstrap-skills-installed`.
- **Don't allow interactive questions to escape.** Bootstrappers have
  standing instructions to answer every `AskUserQuestion` themselves
  from `discovery_hints` + framework defaults. If a bootstrapper
  returns `status=needs-user-input`, treat it as a sub-agent bug —
  fail that framework with `bootstrapper-asked-user` rather than
  blocking the workflow on a user prompt.
- **Don't** scaffold source files yourself ; you only pick + dispatch.
- **Don't** mutate `.smith/` files ; the orchestrator handles
  persistence.
- **Don't** retry failed bootstrappers ; surface in `results[]` and
  let the orchestrator decide.
- **Don't** branch on provider. Bootstrap skills are real skills in
  the consumer project — dispatch them the same way regardless of
  provider.
