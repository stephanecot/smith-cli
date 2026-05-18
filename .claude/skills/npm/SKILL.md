---
name: npm
description: Run an npm command (install, run <script>, test, build, lint, ci, audit) inside the frontend/ workspace, in a dedicated Haiku sub-agent — instead of burning Opus context on multi-thousand-line Vitest / Vite / lint logs. Trigger with `/npm <args>` (e.g. `/npm test`, `/npm run build`, `/npm ci`, `/npm run lint`). Use whenever the user asks to test, build, lint, or install — anything where the parent session only needs the verdict.
---

# Skill — `/npm`

This skill exists for one reason: **`npm` doesn't need Opus.** Running an npm script is a deterministic shell call followed by reading the tail of the log. Doing that in the parent session would dump thousands of lines of test/build output into the Opus context window for no reasoning gain. Instead, this skill dispatches the `npm-runner` agent (model: Haiku) and waits for its concise verdict.

## How to invoke

The user types `/npm <args>`. Take everything after `/npm` as the args to forward to npm.

If the user provides no args, ask them which script they want (Vitest? lint? build?) — `/npm` alone is not actionable.

## What you do

1. **Do not run `npm` yourself in the parent session.** That defeats the entire purpose of this skill.
2. **Dispatch the `npm-runner` agent** via the Agent tool, in the foreground (you need its result before continuing). Set:
   - `subagent_type: "npm-runner"`
   - `description`: 3–5 words, e.g. `"npm test on frontend"`
   - `prompt`: a self-contained instruction. Include the exact command line, the working directory (`frontend/`), and the report shape ("PASS/FAIL headline + Tests/lint/build counters + failure cause; no full log").
3. **Relay the agent's report** to the user verbatim or with a one-line top summary. Do not paraphrase failure messages — copy them.

## Example dispatch prompts

For tests:
```
Run `cd frontend && npm test -- --run --coverage 2>&1 | tail -200` once and report.

Report shape:
- One line: ✅ PASS or ❌ FAIL.
- Tests: `passed=N, failed=N, skipped=N` (Vitest summary).
- Coverage: hit or miss, with the worst metric if FAIL.
- If FAIL: quote the failing test name + assertion only. No full log.
```

For build:
```
Run `cd frontend && npm run build 2>&1 | tail -200` once and report.

Report shape:
- One line: ✅ PASS or ❌ FAIL.
- If FAIL: quote the first build error (file:line + message). No full log.
- If PASS: bundle size summary line if visible, otherwise just the headline.
```

## What you do NOT do

- Don't read `package.json` or browse the frontend code in the parent session "to help" — the runner has Read/Glob/Grep if it needs them.
- Don't fix failing tests, lint errors, or build errors. If the runner reports a real failure, hand it to the user; if they ask you to fix it, dispatch `smi-angular-developer` or `smi-angular-tester`, not the runner.
- Don't re-dispatch the runner more than once per turn. If the user wants a re-run, they ask.
- Don't dispatch a long-running dev server (`npm run start`, `npm run dev`, `npm run watch`) through this skill — they don't terminate. If the user really wants a dev server, run it yourself with `run_in_background=true` so they can monitor it; explain the reason in one line.

## Why this skill exists

Multi-thousand-line Vitest / Vite / lint logs in the parent context cost real tokens and crowd out the work you're actually paid to think about. Offloading the run to Haiku trades pennies for a clean Opus context, and it's strictly faster end-to-end.
