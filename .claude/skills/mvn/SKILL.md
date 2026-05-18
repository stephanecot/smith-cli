---
name: mvn
description: Run a Maven command (mvn) on the backend reactor in a dedicated Haiku sub-agent, instead of burning Opus context on multi-thousand-line build logs. Trigger with `/mvn <goals>` (e.g. `/mvn verify`, `/mvn -pl smith-api test`, `/mvn dependency:tree`). Use whenever the user asks to compile, test, package, verify, or inspect dependencies — anything where the parent session only needs the verdict, not the full log.
---

# Skill — `/mvn`

This skill exists for one reason: **`mvn` doesn't need Opus.** Running Maven is a deterministic shell call followed by reading the tail of the log. Doing that in the parent session would dump thousands of lines of build output into the Opus context window for no reasoning gain. Instead, this skill dispatches the `mvn-runner` agent (model: Haiku) and waits for its concise verdict.

## How to invoke

The user types `/mvn <args>`. Take everything after `/mvn` as the Maven goals + flags to forward.

If the user provides no args, default to `verify` and tell them in your one-line preamble that you're defaulting.

## What you do

1. **Do not run `mvn` yourself in the parent session.** That defeats the entire purpose of this skill.
2. **Dispatch the `mvn-runner` agent** via the Agent tool, in the foreground (you need its result before continuing). Set:
   - `subagent_type: "mvn-runner"`
   - `description`: 3–5 words, e.g. `"mvn verify on backend"`
   - `prompt`: a self-contained instruction. Include the exact command line to run, the working directory expectation (`backend/pom.xml` reactor by default), and the report shape ("PASS/FAIL headline + Tests counters + failure cause; no full log").
3. **Relay the agent's report** to the user verbatim or with a one-line top summary if you want to highlight the verdict. Do not paraphrase failure messages — copy them.

## Example dispatch prompt

```
Run `mvn -B -f backend/pom.xml verify` once and report.

Report shape:
- One line: ✅ PASS or ❌ FAIL.
- If tests ran: `Tests: run=N, failures=N, errors=N, skipped=N`.
- If FAIL: quote the failure section (failing test FQCN + assertion, or compile error file:line). No full stack trace, no full log.
- If PASS: stop after the headline + Tests line.
```

## What you do NOT do

- Don't read `pom.xml` or browse the backend code in the parent session "to help" — the runner has Read/Glob/Grep if it needs them.
- Don't fix failing tests or production code. If the runner reports a real failure, hand it to the user; if they ask you to fix it, dispatch `smi-java-springboot-developer` or `smi-java-springboot-tester`, not the runner.
- Don't re-dispatch the runner more than once per turn. If the user wants a re-run, they ask.
- Don't run destructive goals (`-Dmaven.repo.local=…` redirection, deletion of `~/.m2`, release goals). If the user requests one, refuse and explain why.

## Why this skill exists

Multi-thousand-line Maven logs in the parent context cost real tokens and crowd out the work you're actually paid to think about. Offloading the build to Haiku trades pennies for a clean Opus context, and it's strictly faster end-to-end.
