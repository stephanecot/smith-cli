# Template — Angular 21

Skill templates authored for **Angular 21** projects. Adapted at
install time by `/smith-new-project` (Step 5) into a provider-native
skill file under the consumer project's `.claude/skills/`,
`.github/prompts/`, or `.opencode/commands/`.

## What ships here

See `config.yaml::skills[]` for the full list and per-skill versions.
Each `skills/<slug>/` directory carries :

- `template.md` — body with `{{placeholder}}` markers + stack-gated
  sections (consumer-side adapter resolves them against the project
  stack at install time).
- `metadata.yml` — provider-agnostic metadata (`name`, `description`,
  optionally `model` + `user-invocable`). Provider-native frontmatter
  is composed at release-build time via
  `providers/<provider>/provider.yaml::build.skill_property_map`.

## Adapter placeholders

The bodies may use the placeholders declared in
`config.yaml::adapter_placeholders` (e.g. `{{root_package}}`,
`{{framework_version}}`). The release ships them as-is ; the
consumer-side adapter substitutes them with project-specific values
pulled from `.smith/architecture.json`.

## Targeted stack

- Angular 21 (zoneless, signals, standalone APIs).
- TypeScript 5+.
- Optional : Tailwind v4, Vitest, Transloco i18n, OpenAPI client.
