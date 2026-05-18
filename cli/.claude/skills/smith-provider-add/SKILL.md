---
name: smith-provider-add
description: Scaffolds a NEW AI provider folder under cli/providers/<slug>/ following the canonical layout documented in the sibling skill `smith-provider-format`. Copies the 5-file rule set + 4 example files from `cli/providers/claude-code/` as starting points, then updates per-file frontmatter to reference the new provider. Trigger with `/smith-provider-add <slug> "<one-line description>"`. CLI-maintainer command.
---

# Skill — `/smith-provider-add`

Scaffolds a **new** AI provider (e.g. `gemini-cli`, `opencode`). To
modify an existing provider, use `/smith-provider-edit` instead.

The canonical layout, the per-kind rule frontmatter contract, and the
cross-reference rules between rule files and examples are documented
in the sibling skill **`smith-provider-format`** — read it first if
not already in context. This skill only carries the scaffold-new
procedure.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `<slug>` must be kebab-case and not already exist under
  `cli/providers/`.

## How to invoke

```
/smith-provider-add <slug> "<one-line description>"
```

Example :

```
/smith-provider-add gemini-cli "Google Gemini CLI provider — supports prompts, hooks via shell commands, no first-class sub-agent dispatch."
```

If args are missing, ask via `AskUserQuestion`.

## What you do

1. **Validate `<slug>`** : kebab-case, no slashes, not already a
   sub-folder of `cli/providers/`.

2. **Create the folder** `cli/providers/<slug>/` and its
   `example/` sub-folder.

3. **Copy the 4 canonical rule files** from
   `cli/providers/claude-code/` as starting points (they are generic
   enough to be reshaped per the new provider's conventions) :
   - `rule-agent.MD`
   - `rule-skill.MD`
   - `rule-hook.MD`
   - `rule-rules.MD`
   For each copied file, update the YAML frontmatter `provider:` field
   to `<slug>`. The `path:` and `example:` fields are kept as-is for
   now ; the maintainer rewrites them by hand when adapting the body
   to the new provider's conventions.

4. **Copy the 4 companion example files** from
   `cli/providers/claude-code/example/` into `cli/providers/<slug>/example/`,
   keeping the same names :
   - `example/example-agent.md`
   - `example/example-skill.md`
   - `example/example-hook.json`
   - `example/example-rules.md`
   These ship as Claude-Code-flavoured worked-out examples — the
   maintainer rewrites them later when adapting the rule files.

5. **Write a `RULES.MD`** for the new provider — use
   `cli/providers/claude-code/RULES.MD` and
   `cli/providers/github-copilot/RULES.MD` as references. Required
   sections (see `smith-provider-format` for details) :
   - Artefact map (kind → rule file → consumer path → invocation).
   - Discovery + precedence.
   - Cross-kind interactions.
   - Gaps vs Claude Code (table).
   - When to pick which kind.

6. **Tell the user** the 5 rule files + 4 examples are Claude-Code
   PLACEHOLDERS — they must be rewritten by hand to match the new
   provider's syntax. This skill does NOT auto-translate.

## What you do NOT do

- Don't re-document the provider folder layout, the rule-frontmatter
  contract, or the example cross-reference rules — those live in
  `smith-provider-format`. Keep this skill focused on the
  scaffold-new procedure.
- Don't translate the rule bodies automatically. Adapting them to a
  new provider's API is a manual job that requires reading that
  provider's documentation.
- Don't touch `cli/.claude/`, `cli/templates/`, or `cli/bundles/`.
- Don't register the new provider in any global index ; providers
  are discovered by directory walking under `cli/providers/`. No
  catalogue file exists at the provider level.
- Don't modify an EXISTING provider — that's `/smith-provider-edit`'s
  job.

## Reporting back

```
✅ Provider `<slug>` scaffolded under cli/providers/<slug>/.
   5 rule files + 4 examples copied from claude-code as starting points.

Next steps :
  - Rewrite `<slug>/rule-agent.MD` body to match the provider's sub-agent format.
  - Rewrite `<slug>/rule-skill.MD` body to match its slash-command / skill format.
  - Rewrite `<slug>/rule-hook.MD` body (or mark as N/A if the provider has no event hooks).
  - Rewrite `<slug>/rule-rules.MD` body to match its rules / instructions format.
  - Rewrite the 4 `<slug>/example/example-*` files with provider-idiomatic content.
  - Fill the `Gaps vs Claude Code` section in `<slug>/RULES.MD`.
```
