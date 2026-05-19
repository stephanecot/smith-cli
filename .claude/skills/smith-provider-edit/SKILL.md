---
name: smith-provider-edit
description: Modify an EXISTING AI provider folder under cli/providers/<slug>/ — rewrite a format YAML, rewrite its companion example, edit the provider.yaml metadata, or refresh examples after a provider API change. Every change is validated against the JSON Schemas at cli/providers/specs/ before being reported as successful. Trigger with `/smith-provider-edit <slug> [--edit-format agent|skill|hook] [--edit-example agent|skill|hook] [--edit-provider] [--sync-example-from-format <kind>] [--sync-format-from-example <kind>] [--description "<new>"]`. CLI-maintainer command.
---

# Skill — `/smith-provider-edit`

Modify an **existing** provider folder while preserving the canonical
4-YAML layout and the schema contract under `cli/providers/specs/`. To
create a new provider, use `/smith-provider-add` instead.

The layout, the schema contract, and the cross-references between
format files and examples are documented in the sibling skill
**`smith-provider-format`** — read it first if not already in context.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `<slug>` must be an existing sub-folder of `cli/providers/` with the
  canonical layout (provider.yaml + 3 format-*.yaml + example/).
- All 4 schemas under `cli/providers/specs/` must exist and be valid
  JSON Schema 2020-12.

## How to invoke

```
/smith-provider-edit <slug> <one-or-more-flags>
```

Supported flags (combinable in one invocation) :

| Flag | Effect |
|---|---|
| `--edit-format <kind>`           | Open `format-<kind>.yaml` (`<kind>` ∈ agent / skill / hook) for the maintainer to rewrite. After the edit, the skill validates the file against `format-<kind>.schema.json` and refuses YAML comments. |
| `--edit-example <kind>`          | Open `example/example-<kind>[.suffix].<ext>` for the maintainer to rewrite. The skill validates that the file still exists and matches the `example:` field declared in the companion format file (which itself must still validate). |
| `--edit-provider`                | Open `provider.yaml` for the maintainer to edit. The skill validates the result against `provider.schema.json` and refuses YAML comments. |
| `--sync-example-from-format <kind>` | Regenerate `example/example-<kind>[.suffix].<ext>` from a literal skeleton block embedded in the matching `format-<kind>.yaml` (replaces placeholder tokens with realistic example values). Useful right after a major rewrite. Skip if no skeleton block exists. After the write, re-validate both `format-<kind>.yaml` and the example path declared in it. |
| `--sync-format-from-example <kind>` | Reverse operation — extract the frontmatter section from the example file and replace the literal skeleton block in the matching `format-<kind>.yaml`. After the write, re-validate against `format-<kind>.schema.json`. |
| `--description "<new>"`          | Replace the top-level `description:` value in `provider.yaml`. Preserve every other key. Re-validate against `provider.schema.json`. |

If no flag is given, halt and tell the user which `--edit-*` /
`--sync-*` / `--description` options exist.

## What you do

1. **Validate inputs.**
   - `<slug>` exists under `cli/providers/` and has the canonical
     4-YAML core (provider.yaml + format-agent.yaml + format-skill.yaml
     + format-hook.yaml).
   - For every `--edit-format` / `--edit-example` / `--sync-*` flag —
     the target format file + its companion example exist.
   - `<kind>` MUST be one of `agent`, `skill`, `hook`. Refuse any
     other value with a one-line message — the 3 kinds are hardcoded
     in `provider.schema.json` via the `kinds.required` list.
   - Load the 4 schemas from `cli/providers/specs/` so they are
     available for post-edit validation.

2. **Apply each requested change** in order :
   - **`--edit-format <kind>`** — open `format-<kind>.yaml` for the
     maintainer. After the edit, re-read the file, parse it as YAML,
     and validate against `format-<kind>.schema.json`. Also reject
     YAML comments at the document level (lines beginning `\s*#`
     outside a literal `|` block).
   - **`--edit-example <kind>`** — open the example file. After the
     edit, re-read it and check the `example:` field of the companion
     format file still resolves to this filename (re-validate the
     format file too).
   - **`--edit-provider`** — open `provider.yaml`. After the edit,
     parse and validate against `provider.schema.json`. Confirm
     `slug:` still equals the folder name and that
     `kinds.{agent,skill,hook}.format` all point at existing files.
     Reject YAML comments.
   - **`--sync-example-from-format <kind>`** — look up a literal
     skeleton block embedded in `format-<kind>.yaml` (conventionally a
     top-level `skeleton: |` key). If absent, skip with a one-line
     warning. Otherwise replace the placeholders with realistic
     example values, atomic write to
     `example/example-<kind>[.suffix].<ext>`, then re-validate the
     format file (it must still satisfy its schema, since the example
     path may have been touched).
   - **`--sync-format-from-example <kind>`** — extract the frontmatter
     section from the example file (between the leading `---` fences
     or — for `.json` examples — the top-level object), render it as a
     literal `|` block, replace the existing `skeleton:` key in
     `format-<kind>.yaml`. Atomic write. Re-validate against
     `format-<kind>.schema.json`.
   - **`--description "<new>"`** — replace the top-level
     `description:` value in `provider.yaml`. Preserve every other
     key. Re-validate against `provider.schema.json`.

3. **Validate the final state** :
   - `provider.yaml` validates against `provider.schema.json`.
   - Each `format-<kind>.yaml` validates against its
     `format-<kind>.schema.json`.
   - Every `example:` field resolves to a real file under `example/`.
   - No YAML comments anywhere in `provider.yaml` or `format-*.yaml`.
   - Atomic writes for every changed file (tempfile → fsync →
     rename).

4. **Print** the change summary :
   ```
   ✅ Provider `<slug>` updated.
   Files changed :
     - <list of edited files>
     - <list of added files>
     - <list of removed files>
   Schemas validated : provider, format-agent, format-skill, format-hook.
   ```

## What you do NOT do

- Don't re-document the layout or the schema contract — those live in
  `smith-provider-format` + the 4 `.json` schemas under
  `cli/providers/specs/`.
- Don't create a brand-new provider ; route the user to
  `/smith-provider-add` if `<slug>` does not exist.
- Don't add or remove a 4th format YAML — the 3 kinds (agent / skill
  / hook) are hardcoded by `provider.schema.json`. Extra concepts
  live inline in `provider.yaml`.
- Don't reintroduce the old `RULES.MD` / `rule-*.MD` layout — refuse
  with a one-line message if the maintainer asks for it.
- Don't write a `cli/providers/config.json` index ; providers stay
  filesystem-discovered.
- Don't add YAML comments to any `provider.yaml` or `format-*.yaml`.
- Don't translate format bodies automatically when the maintainer
  passes `--edit-format` — open the file and let the maintainer
  rewrite it by hand. The skill only validates the result.
- Don't accept a partial-success state — if ANY schema validation
  fails after the edit, restore the previous version (or roll back
  the in-flight write) and surface the validator errors.
```
