---
kind: skill
provider: claude-code
title: Skill (.claude/skills/<slug>/SKILL.md)
path: .claude/skills/<slug>/SKILL.md
example: example/example-skill.md
---

# Rules — Claude Code skill (`.claude/skills/<slug>/SKILL.md`)

A skill is a reusable instruction set the user can invoke with `/<slug>`
or that Claude auto-loads when its `description` matches the conversation.
Skills follow the [Agent Skills](https://agentskills.io) open standard with
Claude Code-specific extensions.

## File path & discovery

- Project scope : `<repo>/.claude/skills/<slug>/SKILL.md`
- User scope : `~/.claude/skills/<slug>/SKILL.md`
- Plugin scope : `<plugin>/skills/<slug>/SKILL.md` (namespaced `plugin:slug`)
- Enterprise scope : managed-settings directory
- Each skill is its own **directory** ; `SKILL.md` is the entrypoint, and
  supporting files (templates, scripts, reference docs) live alongside it.
- Slug = directory name. If frontmatter `name:` is omitted, the directory
  name becomes the skill name.
- Live change detection : adding/editing a skill takes effect within the
  current session without restart (top-level new dirs require a restart).

## Frontmatter — every supported field

| Field                      | Required    | Default          | Allowed values                                                | Meaning |
|----------------------------|-------------|------------------|---------------------------------------------------------------|---------|
| `name`                     | No          | directory name   | lowercase + digits + hyphens, max 64 chars                    | Display slug. Filename `SKILL.md` is fixed. |
| `description`              | Recommended | first paragraph  | one-line string                                               | Trigger description Claude uses to decide when to auto-load. Combined with `when_to_use`, capped at 1,536 chars in the listing — front-load the key use case. |
| `when_to_use`              | No          | —                | string                                                        | Extra triggers (phrases, example requests). Appended to `description` in the listing. |
| `argument-hint`            | No          | —                | string                                                        | Hint shown during autocomplete, e.g. `[issue-number]`. |
| `arguments`                | No          | —                | YAML list or space-separated string                           | Named positional arguments for `$name` substitution. |
| `disable-model-invocation` | No          | `false`          | boolean                                                       | `true` blocks Claude from auto-loading ; only user `/<slug>` works. |
| `user-invocable`           | No          | `true`           | boolean                                                       | `false` hides the skill from the `/` menu (background knowledge only). |
| `allowed-tools`            | No          | —                | YAML list or space-separated tool names                       | Pre-approves listed tools while the skill is active. Does NOT restrict — denylists still apply via permissions. Syntax `Bash(git *)` for pattern-scoped pre-approval. |
| `model`                    | No          | session model    | same as Agent's `model`                                       | Per-skill model override for the rest of the current turn. Resets on next prompt. |
| `effort`                   | No          | session effort   | `low` / `medium` / `high` / `xhigh` / `max`                   | Per-skill effort override. |
| `context`                  | No          | inline           | `fork`                                                        | `fork` runs the skill in a forked sub-agent context (isolated, no conversation history). |
| `agent`                    | No          | `general-purpose`| sub-agent type name                                           | Which sub-agent type to use when `context: fork`. Examples : `Explore`, `Plan`, or a custom slug. |
| `hooks`                    | No          | —                | object keyed by event name (see `rule-hook.MD`)               | Hooks scoped to this skill's lifetime. |
| `paths`                    | No          | —                | YAML list of glob patterns                                    | Auto-load this skill only when working with files matching the patterns. Same syntax as memory `paths:`. |
| `shell`                    | No          | `bash`           | `bash` / `powershell`                                         | Shell for `` !`<command>` `` injection. PowerShell requires `CLAUDE_CODE_USE_POWERSHELL_TOOL=1`. |

## Body conventions

- Markdown prose. The body is injected into the active conversation when
  the skill is invoked, and **stays in context** for the rest of the
  session (auto-compaction keeps the most recent 5 000 tokens per skill,
  combined budget 25 000 tokens).
- Keep it concise — every line is a recurring token cost.
- Use **standing instructions**, not one-time steps : the skill body does
  not re-run on later turns.
- Reference supporting files explicitly so Claude knows when to load them :
  `See [reference.md](reference.md) for the full API.`

## String substitutions inside the body

| Variable                | Expands to |
|-------------------------|------------|
| `$ARGUMENTS`            | All arguments passed (verbatim). If omitted from the body, appended as `ARGUMENTS: <value>`. |
| `$ARGUMENTS[N]`         | The Nth argument (0-based, shell-quoted). |
| `$N`                    | Shorthand for `$ARGUMENTS[N]`. |
| `$<name>`               | Named argument declared in `arguments:` frontmatter. |
| `${CLAUDE_SESSION_ID}`  | Current session ID. |
| `${CLAUDE_EFFORT}`      | Active effort level. |
| `${CLAUDE_SKILL_DIR}`   | Absolute path of the skill's directory (use in shell injection for bundled scripts). |

## Dynamic context injection

- ` ` `` `!`<command>` `` ` ` (inline backtick-bang) runs the shell command
  before Claude sees the skill, and the output replaces the placeholder.
- Triple-backtick + `!` opens a multi-line shell block :
  ```
  ```!
  node --version
  git status --short
  ```
  ```
- This is preprocessing on the user's machine — Claude does not see the
  command, only the output.
- Disabled globally with the `disableSkillShellExecution: true` setting
  (useful in managed-settings environments).

## Forked context (`context: fork`)

When `context: fork` is set, the skill body becomes the **task prompt** for
a brand-new sub-agent ; the parent conversation is invisible to it. The
`agent:` field picks which sub-agent type (built-in `Explore` / `Plan` /
`general-purpose` or any custom agent from `.claude/agents/`).

Only useful for skills with explicit tasks. Don't fork a reference-style
skill ("use these conventions") — the sub-agent has no work to do without
an actionable prompt.

## Skeleton

```markdown
---
name: {{skill-slug}}
description: {{What it does + when to use it. Pack triggers (verbs, file types, paths).}}
# when_to_use: {{extra trigger phrases}}
# argument-hint: "[issue-number]"
# arguments: [issue, branch]
# disable-model-invocation: true     # only user can trigger
# user-invocable: false               # only Claude can trigger
allowed-tools: Read Grep Bash(git *) # pre-approves these
# model: sonnet
# context: fork
# agent: Explore
# paths: ["src/**/*.ts"]
---

# Skill — `/{{skill-slug}}`

## Why this skill exists
{{One paragraph. What problem it solves. What it replaces in the parent session.}}

## How to invoke
The user types `/{{skill-slug}} [args]`. {{State arg grammar inline.}}

## What you do
1. {{step}}
2. {{step}}

## What you do NOT do
- {{anti-pattern with reason}}

## Reporting back
One-line verdict (✅ / ❌) so the calling session decides the next move
without re-reading the work product.
```
