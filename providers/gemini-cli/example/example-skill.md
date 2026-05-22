---
name: mvn
description: Run a Maven command (mvn) on the project's reactor — keeps multi-thousand-line build logs out of the parent context. Trigger when the user asks to run Maven, run tests, build the JVM project, or check Maven dependencies.
model: gemini-2.5-flash
tools: read_file, find_files, search_text, run_shell_command
---

# Skill — `/mvn`

Runs Maven off the parent context so multi-thousand-line build logs
do not flood the conversation.

## Procedure

1. Take the user's args (everything after `/mvn`) verbatim. Default
   to `verify` if no args were given.
2. Run `mvn -B <args>` from the project root via
   `run_shell_command`. Capture stdout + stderr + exit code.
3. Parse the output for :
   - Build verdict (`BUILD SUCCESS` / `BUILD FAILURE`).
   - Tests counters (`Tests run: N, Failures: F, Errors: E, Skipped: S`).
   - First failing test class + the most relevant excerpt (≤ 20 lines).
4. Return a tight summary :
   - 1-line verdict (with emoji : ✅ / ❌).
   - 1-line tests counter.
   - Failure context only when verdict is failure — first failing
     test class + the most actionable lines of output.

## Quality bar

- Never run with `-X` (debug) unless the user explicitly asked.
- Cap the summary at ≤ 15 lines.
- Never paste the full Maven log into the response — the whole point
  of this skill is to keep that out of the parent context.

## Out of scope

- Editing `pom.xml` (use `replace_in_file` directly from the parent
  context).
- Releasing / publishing artefacts (out of band).
