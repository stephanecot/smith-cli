---
description: Stage and commit the current changes with a Conventional Commits-style message. The body forces sub-agent execution to keep the diff out of the primary session.
agent: general
subtask: true
---

# /commit

Stage and commit the working tree's changes. Forced to run in a
sub-agent (`subtask: true`) so the diff (often huge) does not bloat
the primary session.

## Current state

!`git status --short`

## Diff to commit

!`git diff --staged`

## How to invoke

The user types `/commit [scope]`. `$1` is the optional scope —
becomes the parenthesised scope in the Conventional Commits subject :
`feat(auth): ...`. If omitted, infer from the most-touched directory
in the diff.

## What you do

1. Read the state above. If there are no changes (empty `git status`),
   stop and tell the user.
2. Draft a commit message :
   - Subject : `<type>(<scope>): <imperative summary>` — under 72 chars.
     Types : `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`.
   - Body : 1-3 lines explaining the **why** (not the what — the
     diff shows that).
3. Stage everything tracked + not ignored : `git add -A`. Warn if a
   suspicious file (`.env`, `*.pem`, `credentials*`) ends up in the
   index.
4. Commit :
   ```
   git commit -m "$(cat <<'EOF'
   <subject>

   <body>
   EOF
   )"
   ```
5. Show the result : `git log -1 --oneline`.

## What you do NOT do

- Don't `git push` — pushing is a separate decision, ask the user.
- Don't amend an existing commit unless the user explicitly says
  `--amend`.
- Don't use `--no-verify`. If a pre-commit hook fails, surface the
  failure and ask.

## Reporting back

```
✅ Committed: <subject>
<short-sha> on branch <branch>
```
