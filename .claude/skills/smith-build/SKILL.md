---
name: smith-build
description: Builds one runnable Smith release per AI provider under `cli/releases/<provider>/`. For each provider in `cli/providers/<provider>/` it assembles a drop-in tree containing the provider runtime root (`.claude/` / `.github/` / `.opencode/`) populated with every skill + agent from `cli/bin/`, plus pre-built `bundles/` and `templates/` trees where every skill's frontmatter is already composed for the target provider. Bundles + templates are **built at release time** (no longer at `/smith-new-project` time) ; their `config.yaml` files are preserved so downstream installers can still pick a subset. The build itself is deterministic — this skill is a thin orchestrator that invokes the sibling `build.py` script. CLI-maintainer command. Trigger with `/smith-build [--provider <slug>] [--clean]`.
---

# Skill — `/smith-build`

Thin orchestrator. The actual release-build logic is **fully
deterministic** (file walking + YAML frontmatter assembly + verbatim
copies), so it lives in the sibling Python script
`${CLAUDE_SKILL_DIR}/build.py` — no LLM reasoning required at runtime.

## How to invoke

```
/smith-build                        # build every provider in cli/providers/
/smith-build --provider claude-code # build a single provider
/smith-build --clean                # explicit clean (default behaviour anyway)
```

## Pre-conditions

- Working directory is the Smith CLI repo root (the parent of `cli/`).
- `python3` is available and `PyYAML` is installed
  (`python3 -c "import yaml"` succeeds).
- `cli/providers/`, `cli/bin/skills/`, `cli/bin/agents/` exist.

If any pre-condition fails, surface a one-line message and stop —
do not attempt to bootstrap dependencies.

## Procedure

1. **Forward the args.** Take `--provider` / `--clean` from the user
   invocation verbatim and pass them to the script.
2. **Run the script** from the repo root :

   ```
   python3 cli/bin/skills/smith-build/build.py [--provider <slug>] [--clean]
   ```

3. **Surface the script's stdout / stderr verbatim.** The script
   prints a per-provider summary line and the location of every
   `release.yaml` manifest. No reformatting needed.
4. **On non-zero exit code**, report the failure to the user with the
   stderr tail. Do not attempt to retry.

## Release layout produced by the script

Same shape for every provider. Example for `claude-code` :

```
cli/releases/claude-code/
├── .claude/
│   ├── skills/<slug>/SKILL.md       (verbatim copy from cli/bin/skills/)
│   └── agents/<slug>.md             (frontmatter composed from metadata.yml + body)
├── bundles/
│   ├── config.json                  (verbatim copy of cli/bundles/config.json)
│   └── <bundle>/
│       ├── config.yaml              (verbatim from cli/bundles/<bundle>/config.yaml)
│       ├── skills/<slug>/SKILL.md   (metadata.yml + claude-code.yml + body)
│       └── hooks/<provider>/...     (verbatim copy when present)
├── templates/
│   ├── index.json                   (verbatim copy of cli/templates/index.json)
│   └── <fw>/<ver>/
│       ├── config.yaml              (verbatim)
│       └── skills/<slug>/SKILL.md   (metadata.yml + claude-code.yml + template.md)
└── release.yaml                     (build manifest)
```

For `github-copilot` the runtime root becomes `.github/` with
`prompts/` (skills) + `agents/`. For `opencode` it becomes
`.opencode/` with `commands/` (skills) + `agents/`. Bundle + template
trees are structurally identical across providers — only the assembled
SKILL.md frontmatter differs.

## Known limitations (surfaced as manifest warnings)

- **Template adapter placeholders stay untouched.** Bodies carry
  `{{language}}` / `{{framework_version}}` / `{{root_package}}` /
  `{{Feature}}` markers ; they are resolved consumer-side at install
  time by `smith-single-template-adapter` against the project's stack.
- **Companion files alongside `cli/bin/skills/<slug>/`** (e.g.
  `build.py`) only travel with the `claude-code` release — that's the
  only provider whose skill path is a folder. Copilot + opencode use
  flat single-file skill paths, so they receive `SKILL.md` only.

## What you do NOT do

- **Don't** re-implement the build logic in this skill body. The
  script is the single source of truth ; this file just wires the
  slash command to it.
- **Don't** mutate any file under `cli/bin/`, `cli/bundles/`,
  `cli/templates/`, or `cli/providers/` — the script enforces this
  but the skill must not work around it.
- **Don't** call `/smith-bundle-install` or `/smith-template-install`
  from this skill. Those are consumer-side ; this skill produces the
  artefacts they will later read.
