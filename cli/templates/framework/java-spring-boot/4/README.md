# Template — Java + Spring Boot 4

Skill templates authored for **Java 24 + Spring Boot 4** projects.
Adapted at install time by `/smith-new-project` (Step 5) into a
provider-native skill file under the consumer project's
`.claude/skills/`, `.github/prompts/`, or `.opencode/commands/`.

## What ships here

See `config.yaml::skills[]` for the full list and per-skill versions.
Each `skills/<slug>/` directory carries :

- `template.md` — body with `{{placeholder}}` markers + stack-gated
  sections.
- `metadata.yml` — provider-agnostic metadata (`name`, `description`,
  optionally `model` + `user-invocable`).

Provider-native frontmatter is composed at release-build time via
`cli/providers/<provider>/provider.yaml::build.skill_property_map`.

## Targeted stack

- Java 24, Spring Boot 4.
- Optional : Liquibase, REST controllers.
- `mvn -B verify` smoke check after scaffold.
