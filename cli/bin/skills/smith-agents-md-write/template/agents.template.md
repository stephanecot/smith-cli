<!-- managed by smith — last touched by /smith-new-project. Keep this file
     ≤100 lines. Longer guidance belongs in `.smith/FUNCTIONAL_SPECIFICATION.MD`
     and `.smith/TECHNICAL_SPECIFICATION.MD` (generated on demand by
     /smith-generate-docs). -->

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

## Smith CLI in this repo

This repository was bootstrapped via `/smith-new-project` and is now
managed by Smith. The single source of truth for tooling and project
state lives under `.smith/` :

- `.smith/smith.yaml`           — init marker (provider + enabled flag).
- `.smith/config.json`    — Smith state (installed bundles + adapted skills + spec paths).
- `.smith/architecture.json`  — project identity + detected stack with tags.
- `.smith/FUNCTIONAL_SPECIFICATION.MD` — functional spec (run `/smith-generate-docs` to produce).
- `.smith/TECHNICAL_SPECIFICATION.MD`  — technical spec (run `/smith-generate-docs` to produce).
- `.smith/report/`              — markdown reports written by `/smith-*` workflows.

AI provider currently targeted : **{{provider}}**.

## Bundles installed

{{bundles_list_or_none}}

## Templates installed

{{templates_list_or_none}}

## Source scaffold

{{bootstrap_summary_or_none}}

## Where to go next

- `/smith-generate-docs` — write the functional + technical specs.
- `/smith-dashboard`     — render a one-page HTML overview at `.smith/dashboard.html`.
- `/smith-help`          — full Smith CLI command map.

## Coding conventions

- Follow the conventions documented by each installed framework template
  (`.claude/skills/smith-<framework>-<slug>/SKILL.md` for Claude Code,
  `.github/prompts/smith-<framework>-<slug>.prompt.md` for Copilot).
- For build / test / lint, prefer the runner bundles that were
  installed in this repo (see "Bundles installed" above).
- Keep `.smith/` files atomic — never partially-write JSON / YAML.

## Don't

- Don't edit `.smith/config.json` or `.smith/architecture.json`
  by hand. They are owned by Smith skills (`/smith-bundle-install`,
  `/smith-template-install`, `/smith-new-project`).
- Don't delete `AGENTS.md` — it's how Smith-aware AI tools find this
  brief on every turn.
