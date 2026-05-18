# Claude Code — provider router

This folder ships **4 fill-in-the-blank templates** for the Claude Code surface.
Each template is self-contained — it carries the per-kind rules in its own
header so a generator (Smith's `/smith-bundle-add`, future skill mutators,
…) can read one file and produce a valid artefact without cross-references.

This `RULES.MD` is the **router** : where each artefact lives, how it is
invoked, and which other artefact it interacts with. The detailed
field-by-field rules for each kind live in its template.

Source of truth on the web :
- [Sub-agents](https://code.claude.com/docs/en/sub-agents)
- [Skills](https://code.claude.com/docs/en/skills)
- [Hooks](https://code.claude.com/docs/en/hooks)
- [Memory / CLAUDE.md](https://code.claude.com/docs/en/memory)
- [Settings](https://code.claude.com/docs/en/settings)
- [Tools reference](https://code.claude.com/docs/en/tools-reference)
- [Permission modes](https://code.claude.com/docs/en/permission-modes)

## Artefact map

| Kind   | Template            | Path in consumer project                              | Invocation       |
|--------|---------------------|-------------------------------------------------------|------------------|
| Agent  | `rule-agent.MD` | `.claude/agents/<slug>.md`                            | `Agent` tool (`subagent_type: <slug>`) |
| Skill  | `rule-skill.MD` | `.claude/skills/<slug>/SKILL.md` (+ supporting files) | `/<slug>` slash command OR auto by Claude on description match |
| Hook   | `rule-hook.MD`  | declared in `.claude/settings.json` `hooks` key       | fires on event (no user invocation) |
| Rules  | `rule-rules.MD` | `CLAUDE.md` (repo root) OR `.claude/rules/<n>.md`     | always-on in context |

## Discovery + precedence

| Scope        | Path                                                       | Priority |
|--------------|------------------------------------------------------------|----------|
| Managed      | enterprise settings directory                              | 1 (highest) |
| `--agents` / `--add-dir` CLI | current session                            | 2 |
| Project      | `<repo>/.claude/agents|skills|rules/`                      | 3 |
| User         | `~/.claude/agents|skills/`                                 | 4 |
| Plugin       | `<plugin>/agents|skills/` (namespaced `plugin:slug`)       | 5 (lowest) |

Identical `name` slugs are deduplicated by priority ; the higher-priority
scope wins. Within a single scope, files inside the same directory tree are
discovered recursively, but the subdirectory path does NOT affect identity —
only the `name:` frontmatter does (skills also fall back to the parent
directory name when `name` is omitted).

## Cross-kind interactions

- A **skill** body may call any tool the session has access to (Read, Edit,
  Bash, Agent, …). Skills cannot bypass `permissions` ; the `allowed-tools`
  field grants pre-approval but not capability.
- A **skill** can dispatch a **sub-agent** via the `Agent` tool, or run in a
  forked sub-agent context via `context: fork` + `agent: <type>`.
- A **sub-agent** can preload skills via its `skills:` frontmatter (full
  body injected at startup, not just the description).
- **Hooks** fire on Claude Code events (see `rule-hook.MD`). A hook can
  be declared globally in `settings.json` or scoped to a skill / sub-agent
  via the kind's `hooks:` frontmatter.
- **Rules** (CLAUDE.md) load on every session ; they are not invokable, only
  consulted. `.claude/rules/<n>.md` files can carry a `paths:` glob to load
  only when relevant files are touched.

## Naming conventions used by Smith

- `name:` slug = **kebab-case**, lowercase letters + digits + hyphens.
- Smith's own artefacts use the `smith-` prefix (`smith-init`,
  `smith-functional-doc-writer`, …).
- Bundle agents that are tool-runners keep their original slug without the
  Smith prefix (`mvn-runner`, `npm-runner`) — the bundle name (`mvn`,
  `npm`) namespaces them.

## When to pick which kind

| Need | Use |
|---|---|
| Pre-canned multi-step procedure the user types as `/<slug>` | **Skill** |
| Reusable instructions Claude auto-applies when relevant | **Skill** (with informative `description`) |
| Side task that would flood the main context (search results, logs) | **Sub-agent** |
| Read-only exploration without changing files | **Sub-agent** with `tools: Read, Glob, Grep` or `disallowedTools: Write, Edit` |
| Run-on-event automation (lint after edit, log after agent stop) | **Hook** |
| Standing project-wide constraints | **Rules** (CLAUDE.md or .claude/rules/) |

## Smith's mapping per kind

Smith's CLI uses Claude Code as its canonical reference provider :
- The `cli/.claude/skills/smith-*` skills are the user-facing CLI surface.
- The `cli/.claude/agents/smith-*-doc-writer.md` agents implement the
  `/smith-generate-docs` pipeline.
- The `cli/bundles/ia-stats/claude-code/hooks/ia-stats.hooks.json` block is
  a hook fragment to merge into the consumer project's `settings.json`.
