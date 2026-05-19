# Template — `smith-java-spring-boot-bootstrap`

Skill template authored for **Java 24 + Spring Boot 4** projects.
Adapted at install time by
`/smith-template-install --framework java-spring-boot --version 4`
into a provider-native skill file under the consumer project's
`.claude/skills/`, `.github/prompts/`, or `.opencode/commands/`.

## What the adapted skill does

See `metadata.yml` for the one-line description and `template.md` for
the full body that ships into the consumer project.

## Per-provider overrides

Each `<provider>.yml` carries frontmatter overrides specific to that
provider. Files start empty — fill them only when this skill needs a
tweak the provider's defaults don't cover.

## Placeholders

The body in `template.md` may use the placeholders listed in
`config.yaml` `adapter_placeholders` (e.g. `{{root_package}}`). The
installer substitutes them with project-specific values pulled from
`.smith/architecture.json`.
