---
name: npm
description: Run an npm command (install, run <script>, test, build, lint, ci, audit) inside the project's frontend workspace — keeps multi-thousand-line Vitest / Vite / lint logs out of the parent context. Trigger with `/npm <args>` (e.g. `/npm test`, `/npm run build`, `/npm ci`, `/npm run lint`).
model: small
user-invocable: true
---

# Skill — `/npm`

This skill exists for one reason : **`npm` doesn't need the main session's
context.** Running an npm script is a deterministic shell call followed by
reading the tail of the log. Doing that in the parent conversation would
dump thousands of lines of test/build output for no reasoning gain. This
skill dispatches the `npm-runner` sub-agent and waits for its concise
verdict.

## How to invoke

The user types `/npm <args>`. Take everything after `/npm` as the args to
forward to npm. If no args are given, refuse and ask which script the
user wants — bare `/npm` is not actionable.

## What you do

1. Do not run `npm` yourself in the parent session.
2. Dispatch the `npm-runner` sub-agent in the foreground (you need its
   result before continuing). Pass a self-contained brief : the exact
   command line, the working directory (`frontend/` by default), and
   the report shape (one-line PASS/FAIL + Tests/lint/build counters +
   failure cause ; no full log).
3. Relay the runner's report verbatim, or with a one-line top summary.
   Do not paraphrase failure messages — copy them.

## What you do NOT do

- Don't read `package.json` or browse the frontend code in the parent
  session "to help" — the runner has its own read tools.
- Don't fix failing tests, lint errors, or build errors. If the runner
  reports a real failure, hand it to the user.
- Don't re-dispatch the runner more than once per turn. If the user
  wants a re-run, they ask.
- Don't dispatch a long-running dev server (`npm run start`, `dev`,
  `watch`) through this skill — those don't terminate.
