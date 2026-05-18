---
name: smith-provider-edit
description: Modify an EXISTING AI provider folder under cli/providers/<slug>/ — rewrite a rule file from its companion example (or vice-versa), rename an artefact kind, add an extended kind (e.g. `rule-mcp.MD`) beyond the 4 canonical ones, edit the provider description in RULES.MD, or refresh examples after a provider API change. Respects the canonical layout + frontmatter contract documented in `smith-provider-format`. Trigger with `/smith-provider-edit <slug> [--rewrite-rule agent|skill|hook|rules] [--rewrite-example agent|skill|hook|rules] [--add-kind <new-kind>] [--rm-kind <kind>] [--description "<new>"] [--sync-example-from-rule <kind>] [--sync-rule-from-example <kind>]`. CLI-maintainer command.
---

# Skill — `/smith-provider-edit`

Modify an **existing** provider folder while preserving the canonical
layout documented in `smith-provider-format`. To create a new provider,
use `/smith-provider-add` instead.

The layout, the rule-frontmatter contract, and the cross-references
between rule files and examples are documented in the sibling skill
**`smith-provider-format`** — read it first if not already in context.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `<slug>` must be an existing sub-folder of `cli/providers/` with the
  canonical layout (RULES.MD + 4 rule-*.MD + example/).

## How to invoke

```
/smith-provider-edit <slug> <one-or-more-flags>
```

Supported flags (combinable in one invocation) :

| Flag | Effect |
|---|---|
| `--rewrite-rule <kind>`         | Open `rule-<kind>.MD` for the maintainer to rewrite. The skill validates frontmatter after the edit (kind / provider / title / path / example all present, `example:` points at a real file). |
| `--rewrite-example <kind>`      | Open `example/example-<kind>.<ext>` for the maintainer to rewrite. The skill validates that the file still exists and matches the `example:` field of the companion rule. |
| `--sync-example-from-rule <kind>` | Regenerate `example/example-<kind>.<ext>` from the `## Skeleton` block in the matching `rule-<kind>.MD` (replaces placeholder tokens with realistic example values). Useful right after a major rewrite of the rule file. |
| `--sync-rule-from-example <kind>` | Reverse operation — extract the frontmatter from `example/example-<kind>.<ext>` and update the matching `rule-<kind>.MD` `## Skeleton` block. Useful when the maintainer iterated on the example. |
| `--add-kind <new-kind>`         | Create a new `rule-<new-kind>.MD` + `example/example-<new-kind>.<ext>` for an artefact kind beyond the canonical 4 (e.g. `rule-mcp.MD` for MCP server config). Update `RULES.MD` artefact-map table. |
| `--rm-kind <kind>`              | Delete `rule-<kind>.MD` + its companion example. Update `RULES.MD`. **Refuse if `<kind>` is one of the 4 canonical kinds** (agent / skill / hook / rules) — those are required by the format. |
| `--description "<new>"`         | Update the one-line provider description at the top of `RULES.MD`. |

If no flag is given, halt and tell the user what `--rewrite-*` /
`--sync-*` / `--add-kind` / `--rm-kind` / `--description` options exist.

## What you do

1. **Validate inputs.**
   - `<slug>` exists under `cli/providers/` and has the canonical
     5-file core.
   - For every `--rewrite-*` / `--sync-*` flag : the target rule file
     + its companion example exist.
   - For `--add-kind <k>` : `rule-<k>.MD` MUST NOT exist yet, AND
     `<k>` is not one of the canonical 4.
   - For `--rm-kind <k>` : `rule-<k>.MD` exists, AND `<k>` is NOT one
     of the canonical 4 (`agent`, `skill`, `hook`, `rules`) — refuse
     with a one-line message if it is.

2. **Apply each requested change** in order :
   - **`--rewrite-rule <kind>`** : open the file for the maintainer.
     After the edit, re-read it and validate the frontmatter (`kind`,
     `provider`, `title`, `path`, `example` all present ; `example:`
     points at a real file under `example/`).
   - **`--rewrite-example <kind>`** : open the example file. After
     the edit, re-read it and check the `example:` field of the
     companion rule still resolves to this file.
   - **`--sync-example-from-rule <kind>`** : extract the
     `## Skeleton` block from `rule-<kind>.MD`, replace its
     placeholders with realistic example values (drawn from the
     provider's `RULES.MD` examples or sensible defaults), write to
     `example/example-<kind>.<ext>`. Atomic write.
   - **`--sync-rule-from-example <kind>`** : extract the frontmatter
     section from the example file, render it as a fenced block
     inside the matching `rule-<kind>.MD` `## Skeleton` section,
     replacing the existing skeleton. Atomic write. Preserve the
     prose around the skeleton.
   - **`--add-kind <new-kind>`** : create `rule-<new-kind>.MD` (with
     frontmatter `kind: <new-kind>`, `provider: <slug>`, `title`,
     `path`, `example: example/example-<new-kind>.<ext>`) and
     `example/example-<new-kind>.<ext>` (empty stub). Append a row
     to `RULES.MD`'s artefact-map table.
   - **`--rm-kind <kind>`** : delete `rule-<kind>.MD` and
     `example/example-<kind>.<ext>`. Remove the matching row from
     `RULES.MD`'s artefact-map table.
   - **`--description "<new>"`** : replace the one-line description
     near the top of `RULES.MD`. Preserve the rest of the file.

3. **Validate the final state** :
   - Every `rule-<kind>.MD` frontmatter `example:` field resolves
     to a real file.
   - `RULES.MD`'s artefact-map table has exactly one row per
     `rule-<kind>.MD` on disk.
   - Atomic writes for every changed file (tempfile → fsync →
     rename).

4. **Print** the change summary :
   ```
   ✅ Provider `<slug>` updated.
   Files changed :
     - <list of edited files>
     - <list of added files>
     - <list of removed files>
   RULES.MD artefact-map : <N> rows.
   ```

## What you do NOT do

- Don't re-document the layout or the frontmatter contract — those
  live in `smith-provider-format`.
- Don't create a brand-new provider ; route the user to
  `/smith-provider-add` if `<slug>` does not exist.
- Don't remove any of the 4 canonical kinds (agent / skill / hook /
  rules) — refuse with a one-line message.
- Don't write a `cli/providers/config.json` index ; providers stay
  filesystem-discovered per the format reference.
- Don't translate rule bodies automatically when the maintainer
  passes `--rewrite-rule` — open the file and let the maintainer
  rewrite it by hand. The skill only validates the result.
