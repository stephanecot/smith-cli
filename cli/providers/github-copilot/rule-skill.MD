---
kind: skill
provider: github-copilot
title: Prompt file (.github/prompts/<slug>.prompt.md)
path: .github/prompts/<slug>.prompt.md
example: example/example-skill.prompt.md
---

# Rules — Copilot prompt file (`.github/prompts/<slug>.prompt.md`)

A prompt file is the Copilot equivalent of a Claude Code skill : a
reusable instruction set the user invokes with `/<slug>` from Copilot
Chat, or via the `Chat: Run Prompt` command (⇧⌘P).

## File path & discovery

- Workspace : `.github/prompts/<slug>.prompt.md` (default ; configurable
  via `chat.promptFilesLocations`).
- User : VS Code profile dir (synced via Settings Sync → "Prompts and
  Instructions").
- Monorepo : enable `chat.useCustomizationsInParentRepositories` to
  discover prompt files in parent directories.

## Frontmatter — every supported field

| Field           | Required | Default       | Allowed values                                                                            | Meaning |
|-----------------|----------|---------------|-------------------------------------------------------------------------------------------|---------|
| `name`          | No       | filename      | string                                                                                    | Display name shown after `/` in chat. |
| `description`   | No       | —             | one-line string                                                                           | Brief description of the prompt's purpose. |
| `argument-hint` | No       | —             | string                                                                                    | Hint text shown in the chat input field. |
| `agent`         | No       | current agent | `ask` / `agent` / `plan` / custom agent name                                              | Which agent (mode) executes this prompt. |
| `model`         | No       | session model | any available model identifier                                                            | Language model for this prompt. |
| `tools`         | No       | —             | YAML list of tool names, tool-set names, MCP names (`<server>/*` for all server tools)    | Tool allowlist while the prompt runs. |

## Body conventions

- Markdown. The body is the prompt content sent to the model.
- Reference workspace files inline with **relative markdown links** :
  `[link](../path/to/file.ts)`. Copilot inlines the file content.
- Reference tools with `#tool:<tool-name>` (e.g. `#tool:codebase`).
- Variable substitutions :
  | Variable                            | Expands to |
  |-------------------------------------|------------|
  | `${input:variableName}`             | Prompts the user for input. |
  | `${input:variableName:placeholder}` | Input with placeholder text. |
  | `${selection}`                      | Current editor selection. |
  | `${file}`                           | Active file. |

## Tool priority order (when set at multiple levels)

1. Tools listed in the prompt file (highest).
2. Tools from the referenced custom agent.
3. Default tools for the selected agent.

## Invocation

Three ways for the user :
1. Type `/<slug>` in the chat input.
2. Run `Chat: Run Prompt` from the command palette (⇧⌘P).
3. Click the play button in the editor title bar (when viewing the prompt
   file).

## Skeleton

```markdown
---
name: {{slug}}
description: {{One-line — shows in the slash-command dropdown.}}
agent: ask        # or edit / agent / plan / <custom-agent-slug>
# model: claude-sonnet-4-6
tools:
  - codebase
  - editFiles
  - runCommands
# argument-hint: "[issue-number]"
---

# /{{slug}}

## Goal
{{One paragraph — what this prompt achieves end-to-end.}}

## Procedure
1. {{step}}
2. {{step}}

## Inputs (placeholders the user fills)
- `${input:fieldName:Field label}` — {{purpose}}
- `${selection}` — uses the currently selected code (if any)
- `${file}` — uses the active file

## References
- Repo conventions : [copilot-instructions](../copilot-instructions.md)
- Related rules : [angular instructions](../instructions/angular.instructions.md)

## Output shape
{{What format the model should return — markdown ? code block ? a diff ?}}

## Notes
- `agent: ask` runs in chat without editing files.
- `agent: edit` lets the model propose direct edits the user can review/apply.
- `agent: agent` enables tool use (limited subset compared to Claude Code).
```
