# Releases — bundle `mvn`

## 0.1.0 — 2026-05-16

First release. Adds `/mvn <goals>` slash command + `mvn-runner` Haiku
sub-agent. The slash command dispatches the runner ; the runner executes
Maven and returns a one-line verdict + Tests counters + failure cause.

- `claude-code/skills/mvn/SKILL.md` — slash command `/mvn <goals>`.
- `claude-code/agents/mvn-runner.md` — Haiku sub-agent.
- Tags: `build`, `java`, `backend`.

Known limitation : the runner agent hard-codes `backend/pom.xml` as the default
reactor. Override after install if your project's pom lives elsewhere.
