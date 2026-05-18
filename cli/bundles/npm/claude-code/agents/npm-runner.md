---
name: npm-runner
description: Runs ONE npm command (install, run <script>, test, build, lint, ci, audit) inside the project's frontend workspace and reports the outcome (PASS/FAIL + Tests/lint/build counters + failure cause). Dispatched by the `/npm` skill ; never invoke directly. Read-only on source.
tools: Bash, Read, Glob, Grep
model: haiku
---

<!-- @smith-include: ../../common/agents/npm-runner.md -->
