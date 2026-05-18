---
name: smith-build
description: Internal CLI-maintainer skill — produces a Smith CLI release under cli/releases/ from the shippable surface at cli/bin/ (skills + agents). Body to be filled in a later iteration ; this is a placeholder so the slash command is reserved and discoverable. CLI-maintainer command (operates on cli/ itself, not on a consumer project).
---

# Skill — `/smith-build`

**Status : placeholder.** The body is intentionally empty for now —
fill it when the release process is designed.

## Intended scope (to be implemented)

Package the shippable surface of the Smith CLI into a release archive
that consumer projects can install. Source tree :

```
cli/bin/
├── skills/    # consumer-facing skills (init, help, dashboard, …)
└── agents/    # pipeline agents (doc writers, template customizer, …)
```

Output : `cli/releases/smith-cli-<version>.zip` (or `.tar.gz`) +
`cli/releases/smith-cli-<version>.sha256`.

## Out of scope

- CLI-maintainer skills under `cli/.claude/skills/` (`smith-bundle-add`,
  `smith-provider-add`, `smith-template-add`, `smith-build`) are NOT
  shipped — they are dev-time only.
- `cli/bundles/` and `cli/templates/` ship separately on demand via
  `/smith-bundle-install` and `/smith-template-install`, NOT as part of
  the core CLI release archive.
- `cli/providers/`, `cli/samples/`, `cli/PLAN.md`, `cli/README.MD` —
  reference / documentation surface ; not bundled in the release.

## How to invoke (placeholder)

```
/smith-build [--version <semver>]
```

For now : prints a one-line message acknowledging the command and the
intended behaviour. No archive is produced.
