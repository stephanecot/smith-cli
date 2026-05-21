---
name: mvn
description: Run a Maven command (mvn) on the project's reactor — keeps multi-thousand-line build logs out of the parent context. Trigger with `/mvn <goals>` (e.g. `/mvn verify`, `/mvn -pl <module> test`, `/mvn dependency:tree`).
model: small
---

# Skill — `/mvn`

This skill exists for one reason : **`mvn` doesn't need the main session's
context.** Running Maven is a deterministic shell call followed by reading
the tail of the log. Doing that in the parent conversation would dump
thousands of lines of build output for no reasoning gain. This skill
dispatches the `mvn-runner` sub-agent and waits for its concise verdict.

## How to invoke

The user types `/mvn <args>`. Take everything after `/mvn` as the Maven
goals + flags to forward. If no args are given, default to `verify` and
announce the default in your one-line preamble.

## What you do

1. Do not run `mvn` yourself in the parent session.
2. Dispatch the `mvn-runner` sub-agent in the foreground (you need its
   result before continuing). Pass a self-contained brief : the exact
   command line to run, the working directory expectation (the project's
   reactor — `backend/pom.xml` by default), and the report shape
   (one-line PASS/FAIL + Tests counters + failure cause ; no full log).
3. Relay the runner's report verbatim, or with a one-line top summary.
   Do not paraphrase failure messages — copy them.

## What you do NOT do

- Don't read `pom.xml` or browse project code in the parent session "to
  help" — the runner has its own read tools.
- Don't fix failing tests or production code. If the runner reports a
  real failure, hand it to the user.
- Don't re-dispatch the runner more than once per turn. If the user
  wants a re-run, they ask.
- Don't run destructive goals (`-Dmaven.repo.local=…` redirection,
  deletion of `~/.m2`, release goals). Refuse and explain.
