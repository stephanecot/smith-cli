---
name: smith-bundle-format
description: Source of truth for the layout of a Smith bundle under `cli/bundles/<name>/`. Documents the canonical directory tree (config.yaml + skills/<slug>/{<slug>.md, metadata.yml, <provider>.yml} + hooks/<provider>/), the per-skill metadata split (common metadata.yml vs per-provider <provider>.yml), and the canonical tag taxonomy used by `bundles/config.json`. Auto-load whenever the user asks how a bundle is laid out, where to put a new skill body, where provider-specific frontmatter overrides live, or which tags are valid. Consumed by `/smith-bundle-add`, `/smith-bundle-edit`, and `/smith-bundle-install`.
when_to_use: User asks about bundle structure, skills/<slug>/ layout, metadata.yml vs <provider>.yml, hooks/<provider>/ folder, what tags exist, or which file owns what. Also fires when an author / mutator skill needs the canonical layout before scaffolding.
user-invocable: false
---

# Smith bundle — format reference

This skill is the **single source of truth** for the layout of a Smith
bundle under `cli/bundles/<name>/`. Three other Smith skills depend on
it :

- `/smith-bundle-add`     — scaffolds a new bundle following this layout.
- `/smith-bundle-edit`    — modifies an existing bundle while preserving
  this layout.
- `/smith-bundle-install` — assembles the per-provider artefacts from
  this layout when copying a bundle into a consumer project.

## Canonical bundle layout

Every bundle MUST follow this layout. A bundle can ship **multiple
skills** ; each skill is a directory under `skills/` with a fixed
4-file shape. Hooks are provider-specific from the start (no shared
body) and live under `hooks/<provider>/`.

```
cli/bundles/<name>/
├── config.yaml                          # bundle-level metadata (name, description, version, tags, providers)
├── README.MD                            # human-readable intro
├── RELEASES.MD                          # changelog
├── skills/
│   └── <skill-slug>/
│       ├── <skill-slug>.md              # BODY ONLY — no frontmatter
│       ├── metadata.yml                 # COMMON metadata (name, description, version)
│       ├── claude-code.yml              # provider-specific frontmatter overrides (empty by default)
│       └── github-copilot.yml           # provider-specific frontmatter overrides (empty by default)
└── hooks/                               # optional — provider-specific event automation
    ├── claude-code/
    │   ├── <name>.hooks.json            # hook fragment for .claude/settings.json
    │   └── <script>.<ext>               # optional sidecar script the hook invokes
    └── github-copilot/
        ├── <name>.tasks.json            # VS Code task fragment for .vscode/tasks.json
        └── <script>.<ext>               # optional sidecar script the task invokes
```

## Per-skill metadata split

Each `skills/<slug>/` directory holds exactly **3 YAML files + 1 body
file** :

- **`<slug>.md`** — the skill body. **No YAML frontmatter.** Just the
  markdown the LLM sees when the skill loads. `/smith-bundle-install`
  prepends a generated frontmatter at install time.
- **`metadata.yml`** — common metadata that every provider needs (the
  parts that map to the destination frontmatter) :
  ```yaml
  name: <slug>                     # required; the skill's identifier
  description: <one-line>          # required; what the skill does + when to invoke
  ```
  **No `version:` here** — the per-skill version lives in
  `config.yaml` `skills[].version` so the bundle catalogue can list
  every shipped skill + version in one place. metadata.yml is for
  fields that get injected into the destination frontmatter; version
  is bundle bookkeeping, not destination frontmatter.
- **`<provider>.yml`** — provider-specific frontmatter overrides
  (e.g. `claude-code.yml`, `github-copilot.yml`, `opencode.yml`). One
  file per provider the bundle supports. **Empty by default.** The
  maintainer adds whatever frontmatter fields the matching provider
  understands when they want to tune the skill for that provider :

  ```yaml
  # Example claude-code.yml — see cli/providers/claude-code/format-skill.yaml for valid keys
  user-invocable: false
  model: small
  allowed-tools: Read Grep Bash(git *)
  ```

  Any key in this file MUST be a valid field per the provider's
  `cli/providers/<provider>/format-skill.yaml`. Unknown keys make
  `/smith-bundle-install` fail.

  **Model tier abstraction.** The `model:` field in a `<provider>.yml`
  MUST use one of the abstract tiers `small`, `medium`, `large` —
  never a concrete model identifier (`haiku`, `Claude Sonnet 4.5`,
  `anthropic/claude-opus-4-7`, ...). Concrete identifiers drift over
  time as providers release new versions; tiers do not. The installer
  (`/smith-bundle-install`) resolves the tier to the provider-native
  model at write-time, using the workflow's tier→model mapping
  (TBD — `/smith-workflow-config` will own it). If no workflow
  mapping is configured, the installer falls back to a built-in
  default (small=haiku class, medium=sonnet class, large=opus
  class, with the provider-appropriate identifier shape).

## Per-provider hooks

`hooks/<provider>/` ships event automation in the provider's native
format :

- **`hooks/claude-code/<name>.hooks.json`** — a hook fragment that
  `/smith-bundle-install` merges into the consumer's
  `.claude/settings.json` under the `hooks` key. Sidecar scripts in
  the same folder are copied to `.claude/scripts/`.
- **`hooks/github-copilot/<name>.tasks.json`** — a VS Code tasks
  fragment merged into the consumer's `.vscode/tasks.json` (Copilot
  has no in-process event hooks). Sidecar scripts in the same folder
  are copied to `.vscode/scripts/`.

Each provider folder is independent. A script needed by both Claude
Code AND Copilot is duplicated (one copy in
`hooks/claude-code/`, one in `hooks/github-copilot/`) — there is no
shared `common/` folder anymore.

## Install-time assembly

`/smith-bundle-install` produces the destination skill file by
**composing the frontmatter** :

1. Read `cli/providers/<provider>/format-skill.yaml` to know the set
   of valid frontmatter fields for that provider.
2. Read `metadata.yml` for the common fields (`name`, `description`,
   `version`).
3. Read `<provider>.yml` for provider-specific overrides.
4. Build a frontmatter object — `metadata.yml` keys are baseline,
   `<provider>.yml` keys take precedence on collisions, every key MUST
   be in the provider's valid field set.
5. Prepend `--- <frontmatter> ---` to the contents of `<slug>.md` and
   write the assembled file to the consumer at the path declared by
   the provider's `consumer_path` (e.g.
   `.claude/skills/<slug>/SKILL.md` for Claude Code,
   `.github/prompts/<slug>.prompt.md` for Copilot).
6. **Validate** the assembled file's frontmatter against
   `cli/providers/specs/format-skill.schema.json` indirectly — every
   field must satisfy the schema constraints declared in
   `format-skill.yaml`.

Hooks are NOT assembled — they are copied as-is and merged into the
consumer's settings/tasks file per the merge protocol in
`/smith-bundle-install`.

## `config.yaml` shape

```yaml
name: <kebab-case-slug>             # bundle name, equals the directory name
description: |
  Multi-line description of what the bundle does end-to-end.
version: 0.1.0                      # bundle-level semver (independent of per-skill / per-hook versions)
tags: [<from taxonomy below>]
providers: [claude-code, github-copilot]   # subset of supported providers
skills:
  - name: <slug>                    # MUST match a skills/<slug>/ directory on disk
    version: 0.1.0                  # semver, owned at the bundle level (single source of truth)
hooks:
  - name: <hook-name>               # MUST match a hooks/<provider>/<hook-name>.<ext> on disk for at least one provider
    version: 0.1.0                  # semver, owned at the bundle level
```

- `skills:` is REQUIRED. Empty array `[]` is invalid — a bundle with
  zero skills serves no purpose.
- `hooks:` is REQUIRED. Empty array `[]` is valid (a skill-only
  bundle).
- Every `skills[].name` MUST correspond to a `skills/<slug>/`
  directory on disk.
- Every `hooks[].name` MUST correspond to at least one fragment file
  on disk at `hooks/<provider>/<name>.<ext>`. The **set of providers
  that ship the hook is inferred from the directory layout** — no
  redundant `providers:` field in the YAML entry. To install the hook
  for a given provider, the file simply has to exist under
  `hooks/<that-provider>/`.
- The bundle's old `files:` map is **gone** — the structure is
  self-describing from the directory walk, and the listing above is
  the version index.

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

### integration
`hooks`, `slash-command`, `mcp`.

### lifecycle
`common` — special marker. Bundles carrying this tag are **always
installed** during the workflow (`/smith-new-project` and friends),
regardless of which bundles the user explicitly selects. Use it for
foundational bundles that every project should ship by default
(observability, base conventions, etc.). The auto-install behaviour
is enforced by the workflow skills, not by `/smith-bundle-install`
itself — running `/smith-bundle-install --name X` always installs
exactly `X`, common-tagged or not.

**No provider tags.** Provider identity already lives in `config.yaml`
`providers:` — don't duplicate it in `tags:`. Mutators MUST reject any
tag whose value matches a provider slug under `cli/providers/`.

The category labels (role / language / …) exist for guidance only. The
wire format is a flat `tags: [a, b, c]` list.

## Mutator contract

Any Smith skill that creates or modifies a bundle MUST :

1. **Read this skill** to know the canonical layout + tag taxonomy.
2. **Preserve unknown keys** in `config.yaml` and in any per-skill
   YAML — round-trip anything that the current code doesn't recognise.
3. **Update `cli/bundles/config.json`** (the bundle catalogue) after
   any change, by walking `cli/bundles/*/config.yaml` and regenerating
   the index from disk. Sort by `name` for deterministic output. Atomic
   write.
4. **Validate every tag** against the taxonomy above. Reject unknown
   tags; propose the closest match (Levenshtein ≤ 2) when the user
   typed something close.
5. **Validate the per-skill layout** — every `skills/<slug>/`
   directory MUST contain `<slug>.md` + `metadata.yml` + one
   `<provider>.yml` per provider listed in `config.yaml` `providers:`.
6. **Validate every `<provider>.yml`** — keys MUST be a subset of the
   fields declared in `cli/providers/<provider>/format-skill.yaml`
   `frontmatter[]`. Reject unknown fields.
7. **Validate every `hooks/<provider>/<file>.json`** against the
   provider's expectations (hooks for Claude Code, tasks for
   Copilot). The exact JSON shape is out of scope here — just confirm
   the file parses and the destination provider supports it.
8. **Validate the version index** — every entry in
   `config.yaml` `skills[]` MUST correspond to a real
   `skills/<slug>/` directory and vice-versa (no orphan listings, no
   undeclared directories). Every `hooks[]` entry MUST correspond to
   at least one fragment file under `hooks/<provider>/<name>.<ext>`
   (any provider qualifies), and every such file MUST have a
   matching `hooks[]` listing — no orphan files, no undeclared
   entries. The set of providers is inferred from the directory
   layout, not from a `providers:` sub-field.
8. **Bundle agents are out of scope.** This v0.2 layout intentionally
   has no `agents/` folder. Skills run inline or dispatch built-in
   agents via the provider's native tool calls; bundles do not ship
   their own agent artefacts.
