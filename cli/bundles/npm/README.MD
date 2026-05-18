# Bundle — `npm`

Haiku-offload for npm. Adds `/npm <args>` to your Claude Code project ; the slash
command dispatches the `npm-runner` sub-agent (Haiku) which runs npm and returns
a one-line verdict + Tests/lint/build counters + failure cause. The parent Opus
session never sees the multi-thousand-line Vitest / Vite / lint log.

## Installation

```
/smith-bundle-install --name npm --ia claude-code
```

This copies the skill + agent into your project's `.claude/` directory.

## Usage

After install :

```
/npm test
/npm run build
/npm ci
/npm run lint
```

Bare `/npm` is not actionable — the skill asks you which script you want.

## Defaults to review after install

The runner agent assumes the frontend workspace lives at `frontend/`. If your
project's npm workspace is elsewhere (root, `web/`, `apps/web/`, …), edit the
`Default working directory` line in `.claude/agents/npm-runner.md` after install.

## Why this exists

Vitest, Vite, and ESLint logs are verbose. Running them in the parent session
wastes Opus tokens on shell output that has no reasoning value. Haiku does the
exact same job for cents on the dollar and keeps the parent context clean.

## Files

| Path | Purpose |
|---|---|
| `claude-code/skills/npm/SKILL.md` | The `/npm` slash command — dispatches the runner. |
| `claude-code/agents/npm-runner.md` | The Haiku sub-agent that actually runs `npm`. |

## Tags

`build`, `nodejs`, `frontend`
