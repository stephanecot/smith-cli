# Template — `smith-angular-i18n-transloco`

Skill template authored for **Angular 21** projects. Adapted at install
time by `/smith-template-install --framework angular --version 21` into
a provider-native skill file under the consumer project's
`.claude/skills/`, `.github/prompts/`, or `.opencode/commands/`.

## What the adapted skill does

See `metadata.yml` for the one-line description and `template.md` for
the full body that ships into the consumer project.

## Per-provider overrides

Each `<provider>.yml` carries frontmatter overrides specific to that
provider (e.g. `model`, `allowed-tools`, `disable-model-invocation`).
Files start empty — fill them only when this skill needs a tweak the
provider's defaults don't cover.

## Placeholders

The body in `template.md` may use the placeholders listed in
`config.yaml` `adapter_placeholders` (e.g. `{{root_package}}`). The
installer substitutes them with project-specific values pulled from
`.smith/architecture.json`.
