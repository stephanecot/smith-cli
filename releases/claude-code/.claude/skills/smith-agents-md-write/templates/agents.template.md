<!-- auto-generated brief for AI assistants. Manual edits may be overwritten when the project bootstrap re-runs. Keep changes minimal ; deeper guidance belongs in dedicated docs. -->

# {{project_name}}

> {{description_argument_verbatim}}

## What this project is

{{project_summary_one_line}}

## Stack

- **Languages**    : {{languages_inline}}
- **Runtimes**     : {{runtimes_inline}}
- **Frameworks**   : {{frameworks_inline}}
- **Build tools**  : {{build_tools_inline}}
- **Test tools**   : {{test_tools_inline}}
- **Infra tools**  : {{infra_tools_inline}}
- **Databases**    : {{databases_inline}}

## How to work in this repo

- Use the framework's idiomatic build / test / lint commands (see "Stack" above).
- Run the test suite before submitting a change ; the test stack listed above is the source of truth for what "green" means.
- Generated files (lock files, build artefacts, generated clients) are not edited by hand — re-run the producing tool instead.

## Coding conventions

- Follow each framework's idiomatic patterns (file layout, naming, change-detection / state model, dependency-injection style, etc.).
- Use the strictest typing the language supports.
- Keep modules small and single-purpose ; prefer composition over inheritance / inheritance-by-default.
- Co-locate tests with source ; write the test before, or at least with, the change.

## Don't

- Don't commit secrets, credentials, or local-only configuration. Use environment variables or the project's secret store.
- Don't bypass the linter / formatter. If a rule is wrong, change the rule, don't `// eslint-disable`.
- Don't delete this file — AI assistants read it on every turn to understand the project.
