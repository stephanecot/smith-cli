---
name: pip
description: Run a pip command (install, freeze, list, show, uninstall, ...) inside the project's Python workspace — keeps multi-thousand-line resolver / install logs out of the parent context. Trigger with `/pip <args>` (e.g. `/pip install -r requirements.txt`, `/pip freeze`, `/pip list --outdated`).
model: small
tools:
- codebase
- usages
- problems
- runCommands
- terminalLastCommand
---

# Skill — `/pip`

This skill exists for one reason : **`pip` doesn't need the main
session's context.** Running pip is a deterministic shell call followed
by reading the tail of the resolver / install log. Doing that in the
parent conversation would dump thousands of lines of dependency
resolution output for no reasoning gain.

## How to invoke

The user types `/pip <args>`. Take everything after `/pip` as the args
to forward to pip. If no args are given, refuse and ask which pip
subcommand the user wants — bare `/pip` is not actionable.

Detect the right invocation form :
1. If the project ships a virtualenv (`.venv/bin/pip`), use it.
2. Else if `pip` is on `$PATH`, use `pip`.
3. Else fall back to `python -m pip` (or `python3 -m pip`).

## What you do

1. Resolve the working directory : the project root that owns
   `requirements*.txt` / `pyproject.toml` / `setup.py`. Default to the
   current consumer dir.
2. Run the resolved `pip <args>` command. Capture stdout + stderr.
3. Read the tail of the output to extract :
   - Counters (installed, upgraded, downgraded, uninstalled, skipped).
   - The failure cause (first `ERROR:` line) if exit code ≠ 0.
4. Report ONE line :
   - On success : `OK — pip <subcommand> · installed=N upgraded=N`.
   - On failure : `FAIL — <one-line cause>`.
5. Do NOT paste the full log into the parent session. Mention the
   exit code if non-zero.

## What you do NOT do

- Don't read `requirements*.txt` / `pyproject.toml` in the parent
  session "to help" before running pip — the runner has its own read
  tools.
- Don't fix failing installs (missing system deps, version conflicts,
  network errors). If pip reports a real failure, hand it to the
  user.
- Don't re-run pip more than once per turn. If the user wants a
  retry, they ask.
- Don't pin or unpin versions automatically. Editing
  `requirements*.txt` or `pyproject.toml` is a separate, explicit
  task.
- Don't activate or deactivate virtualenvs (`source .venv/bin/activate`)
  — pick the right `pip` executable at invocation time, no shell
  state mutation.
- Don't run destructive flags by default (`--break-system-packages`,
  `--force-reinstall` without explicit user intent, removing global
  packages). Refuse and explain.
