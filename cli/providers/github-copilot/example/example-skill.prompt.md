---
name: commit
description: Stage and commit the current changes with a Conventional Commits message.
agent: agent
model: "Claude Sonnet 4.5 (copilot)"
tools:
  - read/terminalLastCommand
  - runCommands
argument-hint: "[scope]"
---

# /commit

Stage and commit the working tree's changes. Run this manually — Copilot
does not auto-fire prompt files.

## Goal

Produce a clean, Conventional Commits-style commit so reviewers can scan
history without reading every diff.

## Context

Active file : `${file}`
Selection (if any) : `${selection}`

Run `#tool:read/terminalLastCommand` to read the current `git status`
output if you haven't already.

## Procedure

1. **Check state.** Run `git status --short`. If empty, stop and tell the
   user.
2. **Read the diff.** `git diff --staged --no-color` first ; if empty,
   fall back to `git diff --no-color` and warn.
3. **Draft a message** :
   - Subject : `<type>(<scope>): <imperative summary>` — under 72 chars.
     Types : `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`.
     `<scope>` is `${input:scope:Optional commit scope}` if provided ;
     otherwise infer from the most-touched directory.
   - Body : 1-3 lines explaining the **why**.
4. **Stage** the tracked changes : `git add -A`. Refuse to add files
   matching `.env`, `*.pem`, `credentials*`.
5. **Commit** via a heredoc to preserve formatting :
   ```bash
   git commit -m "$(cat <<'EOF'
   <subject>

   <body>
   EOF
   )"
   ```
6. **Show** the result : `git log -1 --oneline`.

## Output shape

```
✅ Committed: <subject>
<short-sha> on branch <branch>
```

## Notes

- Do NOT `git push` ; that's a separate decision.
- Do NOT amend without explicit `--amend` from the user.
- Do NOT use `--no-verify`.
