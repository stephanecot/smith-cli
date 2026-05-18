---
kind: hook
provider: claude-code
title: Hook (.claude/settings.json hooks key)
path: .claude/settings.json (hooks key)
example: example/example-hook.json
---

# Rules — Claude Code hook (`.claude/settings.json` `hooks` key)

A hook is a host-shell command (or HTTP / MCP / prompt / agent invocation)
that fires automatically on a Claude Code lifecycle event. Hooks are
declarative — the user does not invoke them.

## File path & merging

- Project hooks live in `.claude/settings.json` under the `hooks` key.
- User hooks live in `~/.claude/settings.json` (lower priority).
- Local-only overrides live in `.claude/settings.local.json` (gitignored).
- Managed policy hooks (enterprise) override everything.
- A hook can also live in a **skill** or **sub-agent** frontmatter `hooks:`
  field — scoped to that component's lifetime.
- Hooks from all sources **merge** ; identical handlers are deduplicated
  by command string / URL.

## Event reference (Claude Code 2025)

| Event                  | Fires                                                                  | Can block | Matcher? | Default timeout |
|------------------------|------------------------------------------------------------------------|:--------: |:--------:|:---------------:|
| `SessionStart`         | At session start / resume / clear / compact                            | No        | yes (`startup`, `resume`, `clear`, `compact`) | 600s |
| `Setup`                | With `--init-only`, `--init`, or `--maintenance`                       | No        | yes (`init`, `maintenance`) | 600s |
| `UserPromptSubmit`     | User submits a prompt (before Claude sees it)                          | **Yes**   | no       | 30s |
| `UserPromptExpansion`  | Slash command expands before reaching Claude                           | **Yes**   | yes (command name) | 30s |
| `PreToolUse`           | Before any tool call                                                   | **Yes**   | yes (tool name regex) | 600s |
| `PermissionRequest`    | Before the permission dialog                                           | **Yes**   | yes (tool name) | 600s |
| `PermissionDenied`     | When auto-mode denies a tool call                                      | No        | yes (tool name) | 600s |
| `PostToolUse`          | After any tool call succeeds                                           | No        | yes (tool name) | 600s |
| `PostToolUseFailure`   | After any tool call fails                                              | No        | yes (tool name) | 600s |
| `PostToolBatch`        | After a batch of parallel tool calls resolves                          | **Yes**   | no       | 600s |
| `Stop`                 | When Claude finishes responding                                        | **Yes**   | no       | 600s |
| `StopFailure`          | Turn ends due to API error                                             | No        | yes (error type) | 600s |
| `Notification`         | Notification dispatched                                                | No        | yes (notification type) | 600s |
| `SubagentStart`        | A sub-agent is spawned                                                 | No        | yes (agent type) | 600s |
| `SubagentStop`         | A sub-agent finishes                                                   | **Yes**   | yes (agent type) | 600s |
| `TeammateIdle`         | Agent-team teammate about to go idle                                   | **Yes**   | no       | 600s |
| `TaskCreated`          | `TaskCreate` tool fires                                                | **Yes**   | no       | 600s |
| `TaskCompleted`        | `TaskUpdate` sets a task to completed                                  | **Yes**   | no       | 600s |
| `ConfigChange`         | Settings file changes mid-session                                      | **Yes**   | yes (config source) | 600s |
| `CwdChanged`           | Working directory changes                                              | No        | no       | 600s |
| `FileChanged`          | A watched file changes on disk                                         | No        | yes (literal filenames, e.g. `.env`) | 600s |
| `WorktreeCreate`       | A worktree is being created                                            | **Yes**   | no       | 600s |
| `WorktreeRemove`       | A worktree is being removed                                            | No        | no       | 600s |
| `PreCompact`           | Before auto-compaction                                                 | **Yes**   | yes (`manual` / `auto`) | 600s |
| `PostCompact`          | After auto-compaction                                                  | No        | yes (`manual` / `auto`) | 600s |
| `InstructionsLoaded`   | A `CLAUDE.md` / `.claude/rules/*.md` loads                             | No        | yes (load reason) | 600s |
| `Elicitation`          | MCP server asks for user input                                         | **Yes**   | yes (MCP server name) | 600s |
| `ElicitationResult`    | User responded to MCP elicitation                                      | **Yes**   | yes (MCP server name) | 600s |
| `SessionEnd`           | Session terminates                                                     | No        | yes (exit reason) | 600s |

## Hook handler types

| `type`     | Fields                                                                           | Notes |
|------------|----------------------------------------------------------------------------------|-------|
| `command`  | `command` (path), `args[]`, `async`, `asyncRewake`, `shell` (`bash`/`powershell`) | Default ; runs a host process. |
| `http`     | `url`, `headers{}`, `allowedEnvVars[]`                                            | POST the payload to a webhook. |
| `mcp_tool` | `server`, `tool`, `input{}` (with `${...}` placeholders)                          | Calls an MCP tool with the event payload. |
| `prompt`   | `prompt`, `model`                                                                 | Asks Claude to evaluate something (e.g. safety check). Timeout 30s default. |
| `agent`    | `prompt`                                                                          | Delegates to a sub-agent. Timeout 60s default. |

Shared fields on every handler : `if` (sub-matcher like `Bash(rm *)`),
`timeout` (seconds), `statusMessage` (custom spinner), `once` (run once
per session).

## Payload (stdin, JSON)

Every hook receives a JSON object on stdin with at least :

```json
{
  "session_id": "...",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/abs/path",
  "permission_mode": "default | acceptEdits | auto | dontAsk | bypassPermissions | plan",
  "hook_event_name": "<event>"
}
```

Event-specific fields are appended :

- `PreToolUse` / `PostToolUse` / `PermissionRequest` :
  `{ tool_name, tool_input, tool_use_id }`. `PostToolUse` adds
  `tool_result`. `PostToolUseFailure` adds `error`.
- `SubagentStart` / `SubagentStop` : `{ agent_type, agent_id, parent_tool_use_id, output? }`.
- `UserPromptSubmit` : `{ prompt }`.
- `UserPromptExpansion` : `{ expansion_type, command_name, command_args, command_source, prompt }`.
- `Stop` : `{ stop_reason, output }`.
- `Notification` : `{ notification_type, message }`.
- `FileChanged` : `{ file_path, change_type }` (`created` / `modified` / `deleted`).
- `ConfigChange` : `{ config_source, changed_files[] }`.
- `WorktreeCreate` : `{ base_path, isolation_mode }`. Stdout MUST contain the worktree path.
- See [hooks reference](https://code.claude.com/docs/en/hooks) for full schema.

## Exit codes (command hooks)

- `0` — success ; stdout interpreted as JSON decision or plain context.
- `2` — **blocking error** (on events that support blocking — see table).
  Stderr is shown to Claude (PostToolUse / SubagentStop / Stop) or to the
  user (Notification / FileChanged / CwdChanged / etc).
- Other non-zero — non-blocking error ; stderr surfaced to the user.

## JSON output (decision shape)

Print on stdout to control behaviour :

```json
{
  "decision": "block",
  "reason": "Explanation",
  "additionalContext": "Text appended to Claude's context",
  "hookSpecificOutput": {
    "permissionDecision": "allow | deny | ask | defer",
    "permissionDecisionReason": "...",
    "updatedInput": { "...": "..." },
    "updatedRules": [ "..." ]
  }
}
```

`continue: false` and `decision: "block"` are equivalent in most events.

## Path placeholders

- `${CLAUDE_PROJECT_DIR}` — repo root.
- `${CLAUDE_PLUGIN_ROOT}` — plugin installation dir.
- `${CLAUDE_PLUGIN_DATA}` — plugin persistent data dir.

These work inside `command`, `args`, and as environment variables for the
spawned process.

## Conventions

- Keep hook commands short and side-effect-only ; long work must use
  `async: true`.
- Never raise from a command hook — log to stderr and exit 0 (or exit 2
  for blocking events). A persistently failing hook may be auto-disabled.
- Idempotent : Claude Code may retry on timeout.
- Permission-decision merging when multiple hooks return on the same
  event : `deny` > `block`/`ask` > `allow`/`defer`.

## Skeleton — `.claude/settings.json`

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/scripts/lint.sh",
            "timeout": 30
          }
        ]
      }
    ],
    "SubagentStop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PROJECT_DIR}/.claude/scripts/append-agent-status.sh --event SubagentStop"
          }
        ]
      }
    ]
  }
}
```

## Skeleton — inline in skill / agent frontmatter

```yaml
---
name: my-skill
description: ...
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: ./security-check.sh
---
```
