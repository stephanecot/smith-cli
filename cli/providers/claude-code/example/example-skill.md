---
name: commit
description: Stage and commit the current changes with a Conventional Commits-style message. Dispatch when the user says "commit", "make a commit", or asks for a commit message. Read-only on production code ; only writes a commit.
when_to_use: User wants to commit changes. Triggers on "commit", "ship", "make a commit", "git commit".
disable-model-invocation: true
allowed-tools: Bash(git status *) Bash(git diff *) Bash(git add *) Bash(git commit *)
argument-hint: "[scope]"
---

# Skill — `/commit`

Stage and commit the working tree's changes. The user is the only one who
should trigger this (`disable-model-invocation: true`) — auto-committing
is dangerous.

## Current state

!`git status --short`

## Diff to commit

!`git diff --staged`

## How to invoke

The user types `/commit [scope]`. `<scope>` is optional ; if provided, it
becomes the parenthesised scope in the Conventional Commits subject :
`feat(auth): ...`. If omitted, infer the scope from the most-touched
directory in the diff.

## What you do

1. **Read the state above.** If there are no changes (`git status` empty),
   stop and tell the user.
2. **Draft a commit message** :
   - Subject : `<type>(<scope>): <imperative summary>` — under 72 chars.
     Types : `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`.
   - Body : 1-3 lines explaining the **why** (not the what — the diff
     shows that).
3. **Stage everything** that's tracked and not ignored : `git add -A`.
   Do NOT stage files matching `.env`, `*.pem`, `credentials*`, or
   anything in `.gitignore` (Git already filters those, but warn if a
   suspicious file is in the index).
4. **Commit** :
   ```
   git commit -m "$(cat <<'EOF'
   <subject>

   <body>
   EOF
   )"
   ```
5. **Show the result** : `git log -1 --oneline` to confirm.

## What you do NOT do

- Don't `git push` — pushing is a separate decision, ask the user.
- Don't amend an existing commit unless the user explicitly says
  `--amend`.
- Don't use `--no-verify` to bypass hooks. If a pre-commit hook fails,
  surface the failure and ask the user how to proceed.
- Don't commit files that look like secrets (`*.env`, `*.pem`,
  `credentials*`, `*.key`).

## Reporting back

```
✅ Committed: <subject>
<short-sha> on branch <branch>
```
