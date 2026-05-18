---
name: smith-bundle-format
description: Source of truth for the layout of a Smith bundle under `cli/bundles/<name>/`. Documents the canonical directory tree (common/ + claude-code/ + github-copilot/), the `@smith-include` factorisation contract (skill bodies + agent bodies live ONCE under common/, per-provider files are real artefacts with frontmatter + a single include directive), the multi-skill / multi-agent pattern, and the canonical tag taxonomy used by `bundles/config.json`. Auto-load whenever the user asks how a bundle is laid out, where to put a new skill body, what an `@smith-include` directive means, or which tags are valid. Consumed by `/smith-bundle-add` (new bundle), `/smith-bundle-edit` (modify existing bundle), and `/smith-bundle-install` (resolves includes at install time).
when_to_use: User asks about bundle structure, common/ vs claude-code/ vs github-copilot/, how to factorise a bundle body, what the @smith-include directive does, what tags exist, or which file owns what. Also fires when an author / mutator skill needs the canonical layout before scaffolding.
user-invocable: false
---

# Smith bundle — format reference

This skill is the **single source of truth** for the layout of a Smith
bundle under `cli/bundles/<name>/`. Three other Smith skills depend on
it :

- `/smith-bundle-add`     — scaffolds a new bundle following this layout.
- `/smith-bundle-edit`    — modifies an existing bundle while preserving
  this layout.
- `/smith-bundle-install` — resolves the `@smith-include` directives
  documented below when copying a bundle into a consumer project.

## Canonical bundle layout

Every bundle MUST follow this layout. A bundle can ship **multiple
skills** and **multiple agents** ; each gets its own body file under
`common/` and its own per-provider wrapper under each provider folder.

```
cli/bundles/<name>/
├── config.yaml                        # declares everything (name, description, version, tags, providers, files{})
├── README.MD                          # human-readable intro
├── RELEASES.MD                        # changelog
├── common/
│   ├── skills/                        # one .md per skill — BODY ONLY, no frontmatter
│   │   ├── <skill1-slug>.md
│   │   └── <skill2-slug>.md
│   ├── agents/                        # one .md per agent — BODY ONLY, no frontmatter
│   │   ├── <agent1-slug>.md
│   │   └── <agent2-slug>.md
│   └── scripts/                       # optional — any executable byte-identical across providers (e.g. .js, .sh)
├── claude-code/
│   ├── skills/
│   │   └── <skill1-slug>/SKILL.md     # REAL Claude Code skill — frontmatter (per cli/providers/claude-code/rule-skill.MD)
│   │                                  # + a single body line : <!-- @smith-include: ../../../common/skills/<skill1-slug>.md -->
│   ├── agents/
│   │   └── <agent1-slug>.md           # REAL Claude Code sub-agent — frontmatter (per rule-agent.MD)
│   │                                  # + <!-- @smith-include: ../../common/agents/<agent1-slug>.md -->
│   └── hooks/                         # optional — provider-specific .hooks.json (no factorisation)
└── github-copilot/
    ├── skills/
    │   └── <skill1-slug>/SKILL.md     # REAL Copilot skill (Agent Skills standard) — frontmatter
    │                                  # + <!-- @smith-include: ../../../common/skills/<skill1-slug>.md -->
    ├── agents/
    │   └── <agent1-slug>.agent.md     # REAL Copilot chat-mode agent — frontmatter (per github-copilot/rule-agent.MD)
    │                                  # + <!-- @smith-include: ../../common/agents/<agent1-slug>.md -->
    └── tasks/                         # optional — VS Code task fragments .tasks.json (no factorisation)
```

## Factorisation contract — the `@smith-include` mechanism

- **Bodies live ONCE under `common/`** (`common/skills/<slug>.md`,
  `common/agents/<slug>.md`). They are pure markdown without YAML
  frontmatter — they are NOT functional skills/agents on their own.
- **Per-provider files are REAL functional artefacts**. Each carries
  the provider's appropriate YAML frontmatter (different fields per
  provider — `tools`, `model` for Claude Code sub-agents ; `target`,
  `mode`, `tools` for Copilot chat-mode agents ; etc.) followed by
  exactly one body line :
  ```
  <!-- @smith-include: <relative-path-to-common-file> -->
  ```
- **`/smith-bundle-install` resolves the directive at install time** :
  reads the per-provider wrapper, extracts its frontmatter, reads the
  referenced common body, and writes the assembled file (frontmatter
  + body) to the consumer's `.claude/skills|agents/` (or
  `.github/skills|agents/`).
- **Zero duplication** : the body is single-sourced in `common/`.
  Editing it once is enough for every provider variant.
- **`common/scripts/` and similar non-markdown assets** : ship as-is.
  Each provider's hooks / tasks reference them at install time
  (they're copied to `.claude/scripts/` or `.vscode/scripts/`).

## Multi-skill / multi-agent bundles

A bundle can declare more than one skill and more than one agent. The
pattern repeats : N skill bodies under `common/skills/`, N agent bodies
under `common/agents/`, and for each provider, N skill wrappers + N
agent wrappers. The `config.yaml` `files:` map lists every file.

## `config.yaml` shape

```yaml
name: <kebab-case-slug>
description: |
  Multi-line description — what the bundle does end-to-end.
  Mention the factorisation contract if relevant.
version: 0.1.0
tags: [<from taxonomy below>]
providers: [claude-code, github-copilot]   # any subset of the supported providers
files:
  common:
    - kind: skill-body
      path: common/skills/<slug>.md
      description: Shared body for the /<slug> slash command (no frontmatter).
    - kind: agent-body
      path: common/agents/<slug>.md
      description: Shared body for the <slug> agent (no frontmatter).
    - kind: script
      path: common/scripts/<file>
      description: Byte-identical executable shared across providers.
  claude-code:
    - kind: skill
      path: claude-code/skills/<slug>/SKILL.md
      description: REAL Claude Code skill — frontmatter + @smith-include.
    - kind: agent
      path: claude-code/agents/<slug>.md
      description: REAL Claude Code sub-agent — frontmatter + @smith-include.
    - kind: hook
      path: claude-code/hooks/<n>.hooks.json
      description: Hook fragment to merge into .claude/settings.json (provider-specific).
  github-copilot:
    - kind: skill
      path: github-copilot/skills/<slug>/SKILL.md
      description: REAL Copilot skill — frontmatter + @smith-include.
    - kind: agent
      path: github-copilot/agents/<slug>.agent.md
      description: REAL Copilot chat-mode agent — frontmatter + @smith-include.
    - kind: task
      path: github-copilot/tasks/<n>.tasks.json
      description: VS Code task fragment to merge into .vscode/tasks.json (provider-specific).
```

## Canonical tag taxonomy (v0.1)

The full vocabulary. Any other value is rejected. Extending the
taxonomy is a deliberate change — edit this skill, never patch
in-place from another skill.

### role
`build`, `test`, `lint`, `format`, `deploy`, `observability`, `docs`,
`scaffold`, `sdlc`, `release`, `security`.

### language
`java`, `kotlin`, `javascript`, `typescript`, `python`, `go`, `rust`,
`csharp`, `ruby`, `php`, `shell`.

### runtime
`jvm`, `nodejs`, `python3`, `dotnet`, `browser`.

### tier
`frontend`, `backend`, `fullstack`, `infra`, `cli`, `library`.

### provider
`claude-code`, `github-copilot`, `gemini-cli`, `opencode`.

### integration
`hooks`, `slash-command`, `mcp`, `sub-agent`.

The category labels (role / language / …) exist for guidance only. The
wire format is a flat `tags: [a, b, c]` list.

## Mutator contract

Any Smith skill that creates or modifies a bundle MUST :

1. **Read this skill** to know the canonical layout + tag taxonomy.
2. **Preserve unknown keys** in `config.yaml` — round-trip anything
   that the current code doesn't recognise.
3. **Update `cli/bundles/config.json`** (the bundle catalogue) after
   any change, by walking `cli/bundles/*/config.yaml` and regenerating
   the index from disk. Sort by `name` for deterministic output. Atomic
   write.
4. **Validate every tag** against the taxonomy above. Reject unknown
   tags ; propose the closest match (Levenshtein ≤ 2) when the user
   typed something close.
5. **Validate the layout** — every file declared in `files:` must
   exist on disk ; every provider wrapper must contain exactly one
   `@smith-include` body line pointing at a real `common/` file.
