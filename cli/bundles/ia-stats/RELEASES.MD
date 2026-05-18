# Releases — bundle `ia-stats`

## 0.1.0 — 2026-05-16

First release. Hook-driven AGENT_STATUS.MD tracker for Claude Code.

- `claude-code/hooks/ia-stats.hooks.json` — declares two hooks :
  - `SubagentStop` → captures agent slug, model, token usage, duration.
  - `PostToolUse` → captures tool name and duration.
- `claude-code/scripts/append-agent-status.js` — Node.js script that
  appends a row to `AGENT_STATUS.MD` at the project root ; creates the
  file on first event ; trims the activity log to the last 50 entries.
  **Cross-platform** — same hook command works on Windows + macOS +
  Linux, so a mixed team gets identical behaviour. **Stdlib only** :
  the script uses only `require('fs')` and `require('path')` —
  **no `package.json`** is needed in the consumer project, and no
  `npm install` is ever required. No Python, no jq, no bash, no
  PowerShell.
- `claude-code/skills/agent-status/SKILL.md` — read-only `/agent-status` slash
  command that prints the current contents of `AGENT_STATUS.MD`.

Design choice — automatic by default : tracking runs through Claude Code
event hooks (`SubagentStop`, `PostToolUse`) so `AGENT_STATUS.MD` is always
current without manual invocation. To opt out, do not install this bundle.
