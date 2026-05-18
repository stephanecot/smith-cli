# Bundle — `mvn`

Haiku-offload for Maven. Adds `/mvn <goals>` to your Claude Code project ; the
slash command dispatches the `mvn-runner` sub-agent (Haiku) which runs Maven and
returns a one-line verdict + Tests counters + failure cause. The parent Opus
session never sees the multi-thousand-line build log.

## Installation

```
/smith-bundle-install --name mvn --ia claude-code
```

This copies the skill + agent into your project's `.claude/` directory.

## Usage

After install :

```
/mvn verify
/mvn -pl <module> test
/mvn dependency:tree
```

Bare `/mvn` defaults to `verify` ; the skill tells you it defaulted.

## Defaults to review after install

The runner agent assumes the reactor lives at `backend/pom.xml`. If your project's
pom is elsewhere (root pom, multi-reactor, …), edit the `Default reactor` line in
`.claude/agents/mvn-runner.md` after install.

## Why this exists

Maven logs are deterministic and verbose. Running them in the parent session
wastes Opus tokens on shell output that has no reasoning value. Haiku does the
exact same job for cents on the dollar and keeps the parent context clean.

## Files

| Path | Purpose |
|---|---|
| `claude-code/skills/mvn/SKILL.md` | The `/mvn` slash command — dispatches the runner. |
| `claude-code/agents/mvn-runner.md` | The Haiku sub-agent that actually runs `mvn`. |

## Tags

`build`, `java`, `backend`
