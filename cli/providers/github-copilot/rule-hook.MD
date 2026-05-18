---
kind: hook
provider: github-copilot
title: Hook (host-driven — VS Code task / git hook / GitHub Actions)
path: .vscode/tasks.json OR lefthook.yml OR .github/workflows/<n>.yml
example: example/example-hook-tasks.json
---

# Rules — Copilot "hook" (host-driven : VS Code task / git hook / GitHub Actions)

GitHub Copilot does **not** support generic event hooks comparable to
Claude Code's `PreToolUse` / `PostToolUse` / `SubagentStop`. Hook-like
behaviour is delegated to one of three host mechanisms :

| Mechanism      | File                                      | Trigger                       |
|----------------|-------------------------------------------|-------------------------------|
| VS Code task   | `.vscode/tasks.json`                      | save / open / build (via `runOptions.runOn`) |
| Git hook       | `lefthook.yml` (or `husky/`)              | pre-commit / pre-push / post-merge |
| CI action      | `.github/workflows/<n>.yml`               | push / pull-request / schedule |

A bundle that targets Copilot AND needs hook-like behaviour MUST :
1. Pick one of the three mechanisms.
2. Ship the matching artefact + an install snippet in the bundle README.
3. Document the opt-in steps (Copilot does not auto-install host hooks).

There is a fourth, experimental option : the **`hooks:` field on a custom
agent** (`.agent.md`) — only enabled when the user sets
`chat.useCustomAgentHooks: true` in VS Code settings. It is opt-in and
scoped to that agent's lifetime.

## VS Code task (`.vscode/tasks.json`)

| Field                            | Meaning |
|----------------------------------|---------|
| `version`                        | `"2.0.0"` (constant). |
| `tasks[].label`                  | Display name. |
| `tasks[].type`                   | `"shell"` (default) or `"process"`. |
| `tasks[].command`                | The command line. |
| `tasks[].args`                   | Argument list (avoids shell quoting issues). |
| `tasks[].presentation.reveal`    | `"always"` / `"silent"` / `"never"`. |
| `tasks[].presentation.panel`     | `"shared"` / `"dedicated"` / `"new"`. |
| `tasks[].runOptions.runOn`       | `"default"` (user runs it) / `"folderOpen"` (auto on open). |
| `tasks[].problemMatcher`         | Optional matcher for error parsing. |

VS Code does not have built-in `onSave` triggers — for save-time work,
use a watcher task that runs continuously OR an extension like Trigger
Task on Save.

## Git hook (lefthook)

`lefthook.yml` is declarative and language-agnostic, ships as `lefthook`
binary (Go), and lives at the repo root.

| Field          | Meaning |
|----------------|---------|
| `<hook-name>`  | e.g. `pre-commit`, `pre-push`, `post-merge`. |
| `commands.<n>.run` | Shell command to execute. |
| `commands.<n>.glob`| Glob to filter staged files (`*.go`, `src/**`). |
| `commands.<n>.files` | Override the file list (e.g. `git diff --name-only`). |
| `commands.<n>.exclude` | Regex/glob to exclude paths. |
| `commands.<n>.tags`    | Group tag so multiple commands can be filtered. |
| `commands.<n>.skip`    | Conditions to skip (e.g. on rebase). |
| `commands.<n>.run` placeholders | `{staged_files}`, `{files}`, `{push_files}`. |

## GitHub Actions (`.github/workflows/<n>.yml`)

For CI-side automation. Standard YAML — out of scope for the per-event
"hook" rule but listed here for completeness.

## Conventions

- Hook scripts live under `.smith/scripts/` in the consumer repo to avoid
  colliding with non-Smith scripts.
- Idempotent + side-effect-only (same constraints as Claude Code hooks).
- Print to stderr on failure ; let the host decide whether to abort
  (`pre-commit` blocks the commit on non-zero exit ; VS Code tasks do
  not abort the editor).

## Skeleton — VS Code task

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "{{bundle}}: on-folder-open",
      "type": "shell",
      "command": "python3",
      "args": ["${workspaceFolder}/.smith/scripts/{{bundle}}-onopen.py"],
      "presentation": { "reveal": "silent", "panel": "dedicated" },
      "runOptions": { "runOn": "folderOpen" }
    }
  ]
}
```

## Skeleton — lefthook pre-commit

```yaml
pre-commit:
  commands:
    {{bundle}}:
      glob: "**/*.{ts,tsx,js}"
      run: python3 .smith/scripts/{{bundle}}-precommit.py {staged_files}
```

## Skeleton — GitHub Actions workflow

```yaml
name: {{bundle}}-on-push
on: { push: { branches: [main] } }
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run {{bundle}} script
        run: python3 .smith/scripts/{{bundle}}-ci.py
```
