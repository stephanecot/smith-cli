---
name: npm-runner
description: Runs ONE npm command (install, run <script>, test, build, lint, ci, audit) inside the project's frontend workspace and reports the outcome (PASS/FAIL + Tests/lint/build counters + failure cause). Dispatched by the `/npm` skill ; chat-mode agent. Read-only on source.
target: vscode
tools:
  - runCommands
  - read/terminalLastCommand
user-invocable: true
disable-model-invocation: false
---

<!-- @smith-include: ../../common/agents/npm-runner.md -->
