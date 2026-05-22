---
name: smith-bundle-format
description: Source of truth for the layout of a Smith bundle under `bundles/<name>/`. Documents the canonical directory tree (config.yaml + skills/<slug>/{<slug>.md, metadata.yml} + hooks/<provider>/), the per-skill metadata shape (generic name + description + model + user-invocable resolved per provider at build time), and the canonical tag taxonomy used by `bundles/index.yaml`. Auto-load whenever the user asks how a bundle is laid out, where to put a new skill body, or which tags are valid. Consumed by `/smith-bundle-add`, `/smith-bundle-edit`, and `/smith-build`.
when_to_use: User asks about bundle structure, skills/<slug>/ layout, metadata.yml shape, hooks/<provider>/ folder, what tags exist, or which file owns what. Also fires when an author / mutator skill needs the canonical layout before scaffolding.
user-invocable: false
---

# Smith bundle — format reference

This skill is the **single source of truth** for the layout of a Smith
bundle under `bundles/<name>/`. Three other Smith skills depend on
it :

- `/smith-bundle-add`  — scaffolds a new bundle following this layout.
- `/smith-bundle-edit` — modifies an existing bundle while preserving
  this layout.
- `/smith-build`       — assembles the per-provider artefacts from
  this layout when packaging a release under
  `releases/<provider>/.smith/bundles/`.

## Canonical bundle layout

Every bundle MUST follow this layout. A bundle can ship **multiple
skills** ; each skill is a directory under `skills/` with a fixed
2-file shape (body + metadata). Hooks are provider-specific from the
start (no shared body) and live under `hooks/<provider>/`.

```
bundles/<name>/
├── config.yaml                          # bundle-level metadata (name, description, version, tags, providers)
├── README.MD                            # human-readable intro
├── RELEASES.MD                          # changelog
├── skills/
│   └── <skill-slug>/
│       ├── <skill-slug>.md              # BODY ONLY — no frontmatter
│       ├── metadata.yml                 # GENERIC metadata + optional skill properties
│       └── assets/                      # OPTIONAL — runtime resources the skill ships with
│           └── ...                      # any tree: server.js, web/, package.json, …
└── hooks/                               # optional — provider-specific event automation
    ├── claude-code/
    │   ├── <name>.hooks.json            # hook fragment for .claude/settings.json
    │   └── <script>.<ext>               # optional sidecar script the hook invokes
    └── github-copilot/
        ├── <name>.tasks.json            # VS Code task fragment for .vscode/tasks.json
        └── <script>.<ext>               # optional sidecar script the task invokes
```

No more per-provider yml files under `skills/<slug>/`. Provider-
specific frontmatter is composed at **build time** from `metadata.yml`
via the mapping declared in
`providers/<provider>/provider.yaml::build.skill_property_map`.

### Optional `skills/<slug>/assets/` bucket

A skill that ships runtime resources (a Node script, a web UI, an
HTML template, …) drops them under `skills/<slug>/assets/`. The
tree is **opaque to Smith** — any layout the skill body knows how
to consume is valid.

Install destination (provider-agnostic) :
`<consumer>/.smith/skills/<slug>/assets/...`. The path mirrors the
source tree byte-for-byte. The skill body references it by the
relative path `.smith/skills/<slug>/assets/…` from the project root.

Rationale for landing under `.smith/` rather than next to the
installed SKILL.md :

- `github-copilot` and `opencode` skills install as a single flat
  file (`.github/prompts/<slug>.prompt.md` /
  `.opencode/commands/<slug>.md`) — there is no sibling folder to
  drop assets into.
- The `.smith/` convention works identically across every
  provider and keeps the consumer's provider-runtime tree clean.
- Bootstrap-template sidecars already use the same `.smith/`-rooted
  pattern (`<consumer>/.smith/bootstraps/<name>/{assets,templates,scripts}/`).

The orchestrators (`/smith-new-project`, `/smith-convert-project`)
and `/smith-bundle-install` copy this folder verbatim on install
when present. Empty / missing → no-op.

## Per-skill `metadata.yml`

Each `skills/<slug>/` directory holds exactly **1 YAML file + 1 body
file** :

- **`<slug>.md`** — the skill body. **No YAML frontmatter.** Just the
  markdown the LLM sees when the skill loads. `/smith-build` prepends
  a generated frontmatter at release time.
- **`metadata.yml`** — provider-agnostic metadata. Carries :
  ```yaml
  name: <slug>                     # required ; the skill's identifier
  description: <one-line>          # required ; what the skill does + when to invoke
  model: <tier>                    # optional ; abstract tier (small / medium / large)
  user-invocable: <bool>           # optional ; whether the user can invoke the skill directly
  ```

  `name` + `description` are passed verbatim to the destination
  frontmatter for every provider. The other properties are GENERIC —
  the build script translates each to the provider's native
  frontmatter key via
  `providers/<provider>/provider.yaml::build.skill_property_map`.
  A property mapped to `null` for a provider (e.g. `user-invocable`
  on github-copilot / opencode) is silently dropped from that
  provider's release.

  **Model tier abstraction.** When `model:` is set, it MUST use one
  of the abstract tiers `small`, `medium`, `large` — never a concrete
  model identifier (`haiku`, `Claude Sonnet 4.5`,
  `anthropic/claude-opus-4-7`, ...). Concrete identifiers drift over
  time ; tiers do not. Each provider's runtime resolves the tier to a
  native model at load time.

  **No `version:` here** — the per-skill version lives in
  `config.yaml::skills[].version` so the bundle catalogue can list
  every shipped skill + version in one place. metadata.yml is for
  fields that get injected into the destination frontmatter ; version
  is bundle bookkeeping.

  Today the build script knows two generic property slugs : `model`
  and `user-invocable`. Adding new properties later requires
  declaring them in the corresponding `skill_property_map` of every
  provider's `provider.yaml::build`.

## Per-provider hooks

`hooks/<provider>/` ships event automation in the provider's native
format. The release-build keeps the directory structure flattened :
`hooks/<provider>/<file>` lands at `hooks/<file>` in the release (the
release tree is already provider-scoped).

- **`hooks/claude-code/<name>.hooks.json`** — hook fragment merged
  into the consumer's `.claude/settings.json` at install time.
  Sidecar scripts in the same folder land at the provider's hook
  directory.
- **`hooks/github-copilot/<name>.tasks.json`** — VS Code tasks
  fragment merged into the consumer's `.vscode/tasks.json` (Copilot
  has no in-process event hooks).
- **`hooks/opencode/<name>.ts`** — plugin file landing under
  `.opencode/plugins/`.

Each provider folder is independent. A script needed by multiple
providers is duplicated (one copy per `hooks/<provider>/` folder) —
there is no shared `common/` folder.

## Build-time assembly

`/smith-build` produces the destination skill file by **composing the
frontmatter** :

1. Read `providers/<provider>/provider.yaml::build` for the
   provider's `skill_property_map`.
2. Read the skill's `metadata.yml`.
3. Emit `name` + `description` verbatim.
4. Walk `skill_property_map` ; for each generic key present in
   `metadata.yml` AND mapped to a non-null native key, emit
   `{native_key: <value>}`. Properties mapped to `null` are dropped.
5. Prepend `--- <frontmatter> ---` to the contents of `<slug>.md` and
   write the assembled file to
   `releases/<provider>/.smith/bundles/<name>/skills/<slug>/SKILL.md`.

Hooks are NOT assembled — they are copied verbatim from
`hooks/<provider>/` to `<release>/.smith/bundles/<name>/hooks/`.

## `config.yaml` shape

```yaml
name: <kebab-case-slug>             # bundle name, equals the directory name
description: |
  Multi-line description of what the bundle does end-to-end.
version: 0.1.0                      # bundle-level semver (independent of per-skill / per-hook versions)
core: false                         # optional ; default false. See "Core bundles" below.
tags: [<from taxonomy below>]
providers: [claude-code, github-copilot, opencode]   # subset of supported providers
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
  on disk at `hooks/<provider>/<name>.<ext>`. The set of providers
  that ship the hook is inferred from the directory layout — no
  redundant `providers:` field in the YAML entry.
- The `providers:` field at the bundle level is stripped at release
  time (the release is already provider-scoped).
- `core:` is OPTIONAL. Absent ≡ `false`. When `true`, the bundle is
  treated as a **base bundle** — see the next section.

## Core bundles

A bundle with `core: true` is a **base bundle** : it is installed
on every consumer project regardless of stack tags or user
selection. Today the only core bundle is `ia-stats` (the per-agent
usage tracker) ; the list will grow as Smith ships more
project-level infrastructure.

Contract :

- `/smith-bundle-install`, `/smith-new-project`, and
  `/smith-convert-project` MUST install every core bundle even
  when the tag-intersection filter would have rejected it.
- The user CAN opt a core bundle out only by explicit instruction
  (`/smith-bundle-install --skip ia-stats`) — the default flow
  always picks it up.
- `core: true` overrides the tag-intersection logic ; it does NOT
  override the `providers:` filter (a core bundle that doesn't
  ship for the active provider is still skipped at build time —
  not at install time).
- `/smith-bundle-list` MUST display the core flag so the user
  knows which bundles will be auto-installed.

The `core:` field is propagated verbatim from `config.yaml` into
`bundles/index.yaml` by the mutator skills, and from there into
`<release>/.smith/bundles/index.yaml` by `/smith-build` (no
special handling — it rides along with the other catalog fields).

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

**No `common` / `core` tag.** The always-installed semantics live in
the first-class `core: true` property at the bundle level (see
"Core bundles" above) — not in the tag taxonomy.

**No provider tags.** Provider identity already lives in `config.yaml`
`providers:` — don't duplicate it in `tags:`.

The category labels (role / language / …) exist for guidance only.
The wire format is a flat `tags: [a, b, c]` list.

## Mutator contract

Any Smith skill that creates or modifies a bundle MUST :

1. **Read this skill** to know the canonical layout + tag taxonomy.
2. **Preserve unknown keys** in `config.yaml` and in any per-skill
   `metadata.yml` — round-trip anything that the current code doesn't
   recognise.
3. **Update `bundles/index.yaml`** (the bundle catalogue) after
   any change, by walking `bundles/*/config.yaml` and regenerating
   the index from disk. Sort by `name` for deterministic output.
   Atomic write.
4. **Validate every tag** against the taxonomy above. Reject unknown
   tags ; propose the closest match (Levenshtein ≤ 2) when the user
   typed something close.
5. **Validate the per-skill layout** — every `skills/<slug>/`
   directory MUST contain exactly `<slug>.md` + `metadata.yml`. No
   stray `<provider>.yml` files (the build-time mapping replaced
   them).
6. **Validate the version index** — every entry in
   `config.yaml::skills[]` MUST correspond to a real
   `skills/<slug>/` directory and vice-versa. Every `hooks[]` entry
   MUST correspond to at least one fragment file under
   `hooks/<provider>/<name>.<ext>` ; every such file MUST have a
   matching `hooks[]` listing.
7. **Bundle agents are out of scope.** This layout intentionally has
   no `agents/` folder. Skills run inline or dispatch built-in agents
   via the provider's native tool calls ; bundles do not ship their
   own agent artefacts.
