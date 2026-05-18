---
kind: agent
provider: github-copilot
title: Chat-mode agent (.github/agents/<slug>.agent.md)
path: .github/agents/<slug>.agent.md
example: example/example-agent.agent.md
---

# Rules — Copilot chat-mode agent (`.github/agents/<slug>.agent.md`)

A chat-mode agent is the Copilot equivalent of a Claude Code sub-agent.
The user selects it from the agents dropdown in Copilot Chat ; the agent's
body becomes the system prompt for the conversation, and only the
declared `tools` are available.

Modern VS Code names the artefact a **custom agent** (`.agent.md`). Older
docs called it a **chat mode** (`.chatmode.md`) — same shape, deprecated
extension.

## File path & discovery

- Workspace : `.github/agents/<slug>.agent.md` (default ; configurable via
  `chat.agentFilesLocations`).
- Also recognised : `.claude/agents/<slug>.md` when `target: vscode`
  (cross-tool agent definitions).
- User : `~/.copilot/agents/<slug>.agent.md` or VS Code profile dir.
- Filename ≠ identity ; `name:` frontmatter wins. If `name:` is omitted,
  the filename (minus `.agent.md`) is used.

## Frontmatter — every supported field

| Field                       | Required | Default          | Allowed values                                                    | Meaning |
|-----------------------------|----------|------------------|-------------------------------------------------------------------|---------|
| `name`                      | No       | filename         | string                                                            | Display name in the agents dropdown. |
| `description`               | No       | —                | one-line string                                                   | Placeholder text shown in the chat input field when this agent is active. |
| `argument-hint`             | No       | —                | string                                                            | Hint text shown in the chat input field to guide users. |
| `tools`                     | No       | all available    | YAML list of tool / tool-set / MCP names (`<server>/*` wildcard)  | Allowlist of tools this agent may use. |
| `agents`                    | No       | —                | YAML list of agent slugs, `*` for all, `[]` for none              | Sub-agents this agent may dispatch (via the `agent` tool). |
| `model`                     | No       | session model    | model name or prioritized YAML list                               | Single model or fallback list (system tries each in order). |
| `user-invocable`            | No       | `true`           | boolean                                                           | Controls whether the agent appears in the dropdown. `false` = hidden but still dispatchable as sub-agent. |
| `disable-model-invocation`  | No       | `false`          | boolean                                                           | `true` blocks the agent from being called as a sub-agent by others. |
| `target`                    | No       | `vscode`         | `vscode` / `github-copilot`                                       | Environment context. `github-copilot` enables Copilot-cloud features ; `vscode` works in the IDE only. |
| `mcp-servers`               | No       | —                | YAML list of MCP server JSON configs                              | Optional MCP servers (only honoured when `target: github-copilot`). |
| `handoffs`                  | No       | —                | YAML list of handoff entries                                      | Suggested next actions — buttons offered at the end of the conversation. See below. |
| `hooks`                     | No       | —                | object                                                            | Optional hook commands scoped to this agent. Requires `chat.useCustomAgentHooks` enabled in settings. |

### Handoff entry shape

| Field    | Required | Type    | Meaning |
|----------|----------|---------|---------|
| `label`  | Yes      | string  | Button text. |
| `agent`  | Yes      | string  | Target agent slug. |
| `prompt` | No       | string  | Prompt to send when the button is clicked. |
| `send`   | No       | boolean | `true` auto-submits the prompt ; default `false` (user reviews first). |
| `model`  | No       | string  | Qualified model name like `"Claude Sonnet 4.5 (copilot)"`. |

## Known tool sets (subset)

VS Code ships built-in tool sets the agent can list :
- `search/codebase` — semantic search over the workspace.
- `search/usages` — find references.
- `web/fetch` — fetch a URL.
- `read/terminalLastCommand` — read the last terminal command.
- `edit` — file edits.
- `agent` (for sub-agents) — enables `handoffs:` and `agents:` semantics.
- MCP server tools : `<server>/*` for all, or `<server>/<tool>` for one.

Project-specific tool sets are declared elsewhere (see VS Code Copilot
docs).

## Body conventions

- Markdown prose prepended to every user prompt while this mode is active.
- Reference tools inline with `#tool:<tool-name>`.
- Reference files inline with relative markdown links : `[link](../file.ts)`.
- Keep it tight — Copilot's context window is smaller than Claude Code's.

## Deprecated fields

`infer` (replaced by `user-invocable` + `disable-model-invocation`).
Old `.chatmode.md` extension still works in transition but is deprecated
in favour of `.agent.md`.

## Skeleton

```markdown
---
name: {{agent-slug}}
description: {{One-line — shows as placeholder in the chat input.}}
target: vscode      # or github-copilot for Copilot-cloud features
tools:
  - search/codebase
  - search/usages
  - edit
  - read/terminalLastCommand
# agents: [helper-agent]      # sub-agents this one can dispatch
# model: ["Claude Sonnet 4.5 (copilot)", "GPT-4o"]
# user-invocable: true
# handoffs:
#   - label: "Open a PR"
#     agent: pr-author
#     prompt: "Open a PR with these changes."
#     send: false
---

# {{Agent Display Name}}

## Mission
{{One paragraph — what this agent does.}}

## Procedure expected from the model
1. {{step}}
2. {{step}}

## Outputs
- {{what the user expects in the chat reply}}
```
