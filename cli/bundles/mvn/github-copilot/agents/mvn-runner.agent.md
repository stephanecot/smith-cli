---
name: mvn-runner
description: Runs ONE Maven command on the project's reactor and reports the outcome (PASS/FAIL + Tests counters + failure cause). Dispatched by the `/mvn` skill ; chat-mode agent. Read-only on source.
target: vscode
tools:
  - runCommands
  - read/terminalLastCommand
user-invocable: true
disable-model-invocation: false
---

<!-- @smith-include: ../../common/agents/mvn-runner.md -->
