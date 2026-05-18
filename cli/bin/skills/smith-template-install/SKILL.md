---
name: smith-template-install
description: Builds adapted SKILL artefacts for a consumer project from a framework template set under cli/templates/<framework>/<version>/. Resolves the closest compatible version (guesses when --version is omitted), then dispatches smith-template-customizer + smith-single-template-adapter to produce SKILL.md files in the consumer project's `.claude/skills/` (Claude Code) or `.github/prompts/` (GitHub Copilot). Upserts the adapted skills into `.smith/config.json` `skills[]`. Trigger with `/smith-template-install --framework <name> [--version <ver>] --ai <provider>`. Requires /smith-init to have run on the consumer project.
---

# Skill — `/smith-template-install`

Read-only on `cli/templates/`. Produces adapted SKILL files in the
consumer project's `.claude/skills/` (Claude Code) or `.github/prompts/`
(GitHub Copilot). Upserts entries into `.smith/config.json`
`skills[]` (per the contract documented in `smith-config-format`).

## Pre-conditions

- `.smith/architecture.json` and `.smith/config.json` must both
  exist on the consumer project (markers that `/smith-init` ran).
- `cli/templates/index.json` must list at least one entry for the
  requested `<framework>`.

## How to invoke

```
/smith-template-install --framework <name> [--version <ver>] --ai <provider>
```

Examples :

```
/smith-template-install --framework angular --version 21 --ai claude-code
/smith-template-install --framework java                  --ai claude-code   # version inferred
/smith-template-install --framework spring-boot           --ai github-copilot
```

If `--framework` or `--ai` is missing, ask via `AskUserQuestion`.
`--version` is optional ; when omitted, the skill resolves the closest
compatible version from `cli/templates/index.json` (see below).

## Version resolution (when `--version` is omitted)

1. Read `cli/templates/index.json`. Filter entries with the requested
   `framework`.
2. If only one version exists for that framework → use it.
3. If multiple versions exist :
   - Read `.smith/architecture.json` to find the project's actual
     version for that framework (e.g. `angular: 21.2.0`).
   - Pick the largest template version `≤` the project version
     (downward match). If none, pick the smallest available template
     version and emit a `version_drift_upward` flag in the report.
4. Tell the user which version was selected and why, in one line.

## What you do

1. **Validate inputs** and resolve the version as described above.
2. **Dispatch `smith-template-customizer`** with :
   - the absolute path of `cli/templates/<framework>/<version>/` ;
   - the absolute path of the consumer project's `.smith/architecture.json` ;
   - the resolved `--ai` provider.
3. **Receive the customizer's report** — list of adapted SKILL files
   with their source template + output path + adaptation flags.
4. **Update `.smith/config.json`** at the consumer project root :
   - The canonical shape of the file + the `skills[]` entry shape are
     documented in the sibling skill **`smith-config-format`** ; consult
     its body and use the template at
     `${CLAUDE_SKILL_DIR}/../smith-config-format/template/config.template.json`
     as the source of truth.
   - For each adapted skill, **upsert** an entry in the `skills[]`
     array keyed by `name` :
     ```json
     {
       "name": "smith-<framework>-<slug>",
       "from_template": "<framework>/<version>/skills/<file>.SKILL.md",
       "path": "<consumer-relative path to the adapted SKILL.md>",
       "adapted_at": "<ISO-8601 UTC>"
     }
     ```
   - Re-running with a newer template version replaces entries with the
     same `name` — never duplicates.
   - **Preserve unknown keys** : round-trip anything in `config.json`
     that you don't explicitly touch.
   - **Update `generated_at`** to the current ISO-8601 UTC time.
   - Atomic write (tempfile → fsync → rename).
   - **Do not touch `.smith/architecture.json`** — that file describes
     the project's tech stack, not Smith outputs. Format spec lives in
     the sibling skill `smith-architecture-format`.
5. **Relay the customizer's `GENERATION_REPORT.MD`** to the user as
   the final output. Do not paraphrase ; quote the report's headline
   summary line.

## What you do NOT do

- Don't author or modify any SKILL.md content yourself. The customizer
  delegates to per-template adapters for that.
- Don't write to `cli/templates/` — this skill is read-only on the
  catalogue.
- Don't run `/smith-init` automatically. If the consumer project's
  `.smith/*-config.json` are missing, refuse and tell the user to run
  `/smith-init` first.
- Don't extend version-resolution heuristics beyond the documented rule.
  Version drift is a known limitation surfaced via the report's flags.

## Reporting back

```
✅ Built {{N}} skills from template `<framework>/<version>` for provider `<ai>`.
{{Y}} kept, {{Z}} rejected, {{F}} flagged. See .smith/GENERATION_REPORT.MD.
.smith/config.json updated — skills[] now lists {{T}} entries.
```
