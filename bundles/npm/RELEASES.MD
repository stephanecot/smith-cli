# Releases — bundle `npm`

## 0.1.0 — 2026-05-16

First release. Adds `/npm <args>` slash command + `npm-runner` Haiku
sub-agent. The slash command dispatches the runner ; the runner executes
npm and returns a one-line verdict + Tests/lint/build counters + failure
cause.

- `claude-code/skills/npm/SKILL.md` — slash command `/npm <args>`.
- `claude-code/agents/npm-runner.md` — Haiku sub-agent.
- Tags: `build`, `nodejs`, `frontend`.

Known limitation : the runner agent hard-codes `frontend/` as the default
workspace. Override after install if your project's npm workspace lives
elsewhere.
