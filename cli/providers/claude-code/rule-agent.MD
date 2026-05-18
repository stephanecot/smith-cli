---
kind: agent
provider: claude-code
title: Sub-agent (.claude/agents/<slug>.md)
path: .claude/agents/<slug>.md
example: example/example-agent.md
---

# Rules — Claude Code sub-agent (`.claude/agents/<slug>.md`)

A sub-agent runs in its own context window with a custom system prompt,
specific tool access, and independent permissions. When the dispatcher
(main session) sees a task that matches a sub-agent's `description`, it
delegates by calling the `Agent` tool with `subagent_type: <slug>`.

## File path & discovery

- Project scope : `<repo>/.claude/agents/<slug>.md`
- User scope : `~/.claude/agents/<slug>.md`
- Plugin scope : `<plugin>/agents/<slug>.md` (namespaced `plugin:slug`)
- Identity = the `name:` frontmatter field, NOT the filename or directory.
- Two files with the same `name` in the same scope : one wins silently —
  keep `name` unique.

## Frontmatter — every supported field

| Field             | Required | Default     | Allowed values                                                              | Meaning |
|-------------------|----------|-------------|-----------------------------------------------------------------------------|---------|
| `name`            | **Yes**  | —           | kebab-case, lowercase + digits + hyphens                                    | Unique slug. `Agent` tool uses it as `subagent_type`. Filename does NOT have to match. |
| `description`     | **Yes**  | —           | one-line natural-language string                                            | When the dispatcher should delegate to this agent. Pack triggers (verbs, file types, paths). |
| `tools`           | No       | inherit all | comma-separated tool names                                                  | Allowlist of tools the agent may use. To preload Skills use `skills:` (not `Skill` here). |
| `disallowedTools` | No       | —           | comma-separated tool names                                                  | Denylist applied first, then `tools` resolves against the remaining pool. |
| `model`           | No       | `inherit`   | `sonnet` / `opus` / `haiku` / full model id (`claude-opus-4-7`) / `inherit` | Per-agent model override. `inherit` reuses the main conversation's model. |
| `permissionMode`  | No       | inherit     | `default` / `acceptEdits` / `auto` / `dontAsk` / `bypassPermissions` / `plan` | Permission behaviour for this agent's tool calls. Ignored for plugin agents. |
| `maxTurns`        | No       | unlimited   | positive integer                                                            | Hard cap on agentic turns before the agent must stop. |
| `skills`          | No       | —           | YAML list of skill slugs                                                    | Skills preloaded at startup ; full body injected, not just the description. |
| `mcpServers`      | No       | —           | YAML list of inline defs OR strings referencing already-configured servers  | MCP tool access scoped to this agent only. Ignored for plugin agents. |
| `hooks`           | No       | —           | object keyed by event name (see `rule-hook.MD`)                             | Lifecycle hooks scoped to this agent. Ignored for plugin agents. |
| `memory`          | No       | none        | `user` / `project` / `local`                                                | Enables a persistent memory directory for cross-session learning. |
| `background`      | No       | `false`     | boolean                                                                     | `true` to always run as a background task (long-running, foreground if false). |
| `effort`          | No       | inherit     | `low` / `medium` / `high` / `xhigh` / `max`                                 | Effort tier when this agent runs. Available levels depend on the model. |
| `isolation`       | No       | none        | `worktree`                                                                  | `worktree` runs the agent in a temporary git worktree (isolated repo copy). |
| `color`           | No       | —           | `red` / `blue` / `green` / `yellow` / `purple` / `orange` / `pink` / `cyan` | Display tint in the task list. |
| `initialPrompt`   | No       | —           | string                                                                      | Auto-submitted as the first user turn when this agent runs as the main session (`--agent` / `agent` setting). Prepended to any user prompt. |

## Body conventions

- The body is the agent's **system prompt** verbatim. It does NOT see the
  main conversation's history.
- Structure that works well : Mission → Inputs → Procedure → Outputs →
  Quality bar → Out of scope.
- Keep it tight : every line costs context tokens on every invocation.
- Don't reference "the parent session" or "the user" — the agent only
  knows what's in its prompt + the dispatcher's brief.

## Available tools (built-in)

`Bash`, `BashOutput`, `Read`, `Write`, `Edit`, `NotebookEdit`, `Glob`,
`Grep`, `Agent`, `WebFetch`, `WebSearch`, `AskUserQuestion`,
`ExitPlanMode`, `TodoWrite`, MCP tools, plus all bundled Skills.

## How the dispatcher picks an agent

The dispatcher reads each available agent's `name` + `description` and
matches by semantic similarity to the task at hand. **The `description`
is the only field that drives selection** — make it specific :
- Lead with the agent's domain (verb + object) : "Reviews code for
  quality and best practices."
- List concrete triggers : "Use after a Write or Edit on `*.py`."
- State the I/O shape if useful : "Returns a list of issues with file:line."

## Skeleton

```markdown
---
name: {{agent-slug}}
description: {{What this agent does, when to use it, what it returns.}}
model: {{haiku|sonnet|opus|inherit}}
tools: {{Read, Glob, Grep, Bash}}    # or omit to inherit all
# permissionMode: {{default|acceptEdits|...}}
# maxTurns: {{N}}
# isolation: worktree                # for risky edits in an isolated worktree
# color: blue
---

# Agent — {{Agent Display Name}}

## Mission
{{One paragraph — what this agent owns end-to-end. Where its boundary
sits with neighbouring agents.}}

## Inputs
- {{arg name}} — {{purpose, format, example}}

## Procedure
1. {{step}}
2. {{step}}

## Outputs
- {{path or artefact}} — {{what it contains}}

## Quality bar
- {{non-negotiable invariant}}

## Out of scope
- {{things the agent must NOT do, to keep boundaries clean}}
```
