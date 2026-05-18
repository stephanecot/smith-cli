# GitHub Copilot — provider router

This folder ships **4 fill-in-the-blank templates** for the GitHub Copilot
surface. Each template is self-contained — it carries the per-kind rules
in its own header so a generator can read one file and produce a valid
artefact without cross-references.

This `RULES.MD` is the **router** : where each artefact lives, how it is
invoked, and which other artefact it interacts with. Detailed
field-by-field rules for each kind live in its template.

Source of truth on the web :
- [Response customization](https://docs.github.com/en/copilot/concepts/response-customization)
- [Custom instructions (VS Code)](https://code.visualstudio.com/docs/copilot/customization/custom-instructions)
- [Prompt files (VS Code)](https://code.visualstudio.com/docs/copilot/customization/prompt-files)
- [Custom chat modes / agents (VS Code)](https://code.visualstudio.com/docs/copilot/customization/custom-chat-modes)

## Artefact map

| Kind   | Template            | Path in consumer project                                                   | Invocation |
|--------|---------------------|----------------------------------------------------------------------------|------------|
| Agent  | `rule-agent.md` | `.github/agents/<slug>.agent.md` (also `.claude/agents/` when `target: vscode`) | Picked from the agents dropdown in Copilot Chat OR dispatched as a sub-agent. |
| Skill  | `rule-skill.md` | `.github/prompts/<slug>.prompt.md`                                          | `/<slug>` in Copilot Chat OR `Chat: Run Prompt` command. |
| Hook   | `rule-hook.md`  | `.vscode/tasks.json` / `lefthook.yml` / `.github/workflows/<n>.yml`         | Host-driven (VS Code task, git hook, CI). Copilot has no in-process event hooks. |
| Rules  | `rule-rules.md` | `.github/copilot-instructions.md` (repo-wide) ; `.github/instructions/<n>.instructions.md` (scoped) | Always-on (or path-scoped via `applyTo`). |

## Discovery + precedence

Copilot reads instructions in the following order (top wins) :

1. Personal instructions (GitHub.com Chat settings popup ; user-only).
2. Path-specific instructions (`.github/instructions/<n>.instructions.md`)
   when `applyTo` matches the current file.
3. Repository-wide instructions (`.github/copilot-instructions.md`).
4. Agent instructions (`AGENTS.md` / `CLAUDE.md` / `GEMINI.md` at repo root).
5. Organization-wide instructions (lowest).

Prompt files and chat-mode agents are discovered from :
- Workspace : `.github/prompts/` (default ; configurable via
  `chat.promptFilesLocations`), `.github/agents/` (default ; configurable
  via `chat.agentFilesLocations`).
- User : VS Code profile dir (synced via Settings Sync → "Prompts and
  Instructions").

## Cross-kind interactions

- A **prompt file** (skill) may reference workspace files inline via
  relative markdown links and reference tools via `#tool:<name>`. Tool
  resolution priority : prompt → referenced agent → agent default.
- A **chat-mode agent** declares the tool sets the model may use ; the
  prompt file inherits these when the agent is the active mode.
- **Hooks** are NOT a Copilot concept — they are delegated to the host
  environment (VS Code tasks, git hooks via lefthook/husky, GitHub
  Actions). See `rule-hook.md`.
- **Rules** (custom instructions) load globally or by `applyTo` glob.
  They are never invokable — only consulted.

## Gaps vs Claude Code

| Capability                          | Claude Code | Copilot     |
|-------------------------------------|-------------|-------------|
| Dispatchable sub-agent (`Agent` tool) | yes        | partial (chat modes + handoffs ; user-driven, no inline `Agent` tool) |
| In-process event hooks              | yes (29 events) | no (delegated to VS Code tasks / git hooks / CI) |
| Slash command auto-discovery        | yes        | yes (prompt files dropdown) |
| Auto-load skill on description match| yes        | no — agents/prompts are user-picked |
| Path-scoped rules                   | yes (`paths:`) | yes (`applyTo:`) |
| Per-skill model override            | yes (`model:`) | yes (prompt + agent `model:`) |
| Per-skill tool allowlist            | yes (`allowed-tools:`) | yes (prompt `tools:`, agent `tools:`) |
| Smaller context window              | larger     | smaller — keep skill and instruction bodies shorter |

## When to pick which kind

| Need | Use |
|---|---|
| Reusable prompt the user types as `/<slug>` | **Prompt file** (`.prompt.md`) |
| Persistent agent the user selects from a dropdown | **Chat-mode agent** (`.agent.md`) |
| Always-on coding conventions | **Rules** (`copilot-instructions.md`) |
| Scope-specific rules (only Python files) | **Rules** (`.github/instructions/<n>.instructions.md` with `applyTo:`) |
| Run-on-save / pre-commit / CI automation | **Host hooks** (VS Code task / git hook / GitHub Actions) |

## Smith's mapping per kind

Smith bundles that target Copilot place artefacts under
`<bundle>/github-copilot/` :
- `prompts/<slug>.prompt.md` for skill-like flows.
- `agents/<slug>.agent.md` for sub-agent-like flows.
- VS Code task fragments and lefthook configs for hook-like flows.
- `instructions/<n>.instructions.md` for rules.

`/smith-bundle-install --ia github-copilot` copies these into the consumer
project's `.github/` (and `.vscode/` for tasks) tree.
