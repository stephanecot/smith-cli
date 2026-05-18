# Bundle — `ia-stats`

Automatic agent / skill consumption tracker. Every time a sub-agent stops or a
tool call returns, a Claude Code hook fires a Node.js script that appends a
row to `AGENT_STATUS.MD` at the consumer project's root. No manual
`/agent-stats` invocation needed — the file stays current on its own.
Cross-platform : the **same** hook command works on Windows, macOS, and
Linux, so a mixed team gets identical behaviour everywhere. Zero npm
dependencies (Node stdlib only) ; no Python, no jq, no bash.

## Why automatic (and not manual)

Tracking runs through Claude Code event hooks (`SubagentStop`,
`PostToolUse`) so `AGENT_STATUS.MD` stays current without the user
invoking anything. If you prefer manual cadence (snapshot on demand),
do not install this bundle ; read or write the file yourself.

## Installation

```
/smith-bundle-install --name ia-stats --ia claude-code
```

This drops three files into your project's `.claude/` directory and prints the
two-line snippet to add to your `.claude/settings.json` `hooks` section.

After install, every sub-agent dispatch and every tool call appends a row to
`AGENT_STATUS.MD` (created on first event).

## What gets tracked

`AGENT_STATUS.MD` carries two tables :

1. **Running totals** — one row per agent slug and one per tool name, with
   total calls, total tokens, last invoked timestamp.
2. **Recent activity** — the last 50 events, chronological, with timestamp,
   event type (`SubagentStop` or `PostToolUse`), agent/tool name, tokens, and
   duration.

## Files

| Path | Purpose |
|---|---|
| `claude-code/hooks/ia-stats.hooks.json` | Hook declaration to paste into `.claude/settings.json`. |
| `claude-code/scripts/append-agent-status.js` | Node.js script invoked by the hook. Reads the event payload from stdin (JSON), updates running totals + recent activity, writes back to `AGENT_STATUS.MD`. Cross-platform, zero dependencies. |
| `claude-code/skills/agent-status/SKILL.md` | Read-only `/agent-status` slash command that prints the current contents of `AGENT_STATUS.MD`. |

## Requirements

- **Node.js >= 16** on PATH (`node --version`). Ships pre-installed on
  most dev machines and CI runners ; downloadable for free from
  nodejs.org if missing.
- Write access to the project root (the script creates / appends
  `AGENT_STATUS.MD`).
- That's it — **no `package.json` required**, no `npm install`, no third-party
  packages. The script uses only Node's `fs` + `path` from stdlib.

## Tags

`observability`, `hooks`, `claude-code`
