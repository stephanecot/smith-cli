---
name: smith-init
description: Bootstrap a project for Smith CLI — creates the .smith/ directory with project-config.json (project identity + detected stack with tags) and smith-config.json (provider + ai_memory_file + bundles slot), then writes an AGENTS.md at the project root from a one-line description. Idempotent — if any of the three files already exists, it stays untouched. Required marker for every other /smith-* skill (each one checks for the JSONs). Trigger with `/smith-init "<description>"`.
---

# Skill — `/smith-init`

Bootstraps Smith on the consumer project. Three files at most, created
only when missing :

1. `.smith/project-config.json` — project identity + detected stack
   (languages, runtimes, frameworks, build / test / infra tools,
   databases — each with `tags[]`).
2. `.smith/smith-config.json` — Smith state shell (provider + spec
   paths + AGENTS.md pointer + empty `bundles[]` slot).
3. `AGENTS.md` at the project root — minimal AI brief seeded from the
   description argument.

That's it. **No documentation generation** — that's `/smith-generate-docs`.
**No template adaptation** — that capability was removed.

The exact shape of the three files comes from three sources :

- **`.smith/project-config.json`** is owned by the sibling skill
  **`smith-project-config-format`** — single source of truth for that
  file's shape. Template lives at
  `${CLAUDE_SKILL_DIR}/../smith-project-config-format/template/project-config.template.json`.
- **`.smith/smith-config.json`** is owned by the sibling skill
  **`smith-config-format`** — single source of truth for that file's
  shape. Template lives at
  `${CLAUDE_SKILL_DIR}/../smith-config-format/template/smith-config.template.json`.
- **`AGENTS.md`** is owned by **this skill** (it's not a config — it's a
  Smith-init-only artefact, never re-written by other skills). Its
  template lives at `${CLAUDE_SKILL_DIR}/template/agents.template.md`.

Each template carries `{{placeholder}}` markers that you substitute with
detected / provided values before writing. Do NOT add or remove top-level
keys / sections — the templates are the contract. For per-field
semantics, consult the `smith-project-config-format` SKILL body (for
`project-config.json`) and the `smith-config-format` SKILL body (for
`smith-config.json`).

## How to invoke

```
/smith-init "<one-line description of the project>"
[--provider claude-code|github-copilot]
[--name <project-name>]
```

- `<description>` — required. One-line natural-language summary of the
  project. Lands in `config.json` and `AGENTS.md`.
- `--provider` — optional, defaults to `claude-code`. Selects the AI tool
  Smith targets. Recorded in `config.json`.
- `--name` — optional. If omitted, infer from `package.json` /
  `pom.xml` / the directory name.

If `<description>` is missing, ask via `AskUserQuestion`.

## What you do

### Step 0 — Pre-flight

1. Verify the consumer project's root is a git working tree (so the
   user can review the generated files in a commit). If not, warn but
   continue — git is recommended, not mandatory.
2. Detect the project name :
   - `--name` flag wins.
   - else `name` field from `package.json` at the root, or `artifactId`
     from `pom.xml`, or `name` from `Cargo.toml`, in that order.
   - else the working directory's base name.

### Step 1 — Create `.smith/` + `project-config.json` (idempotent)

If `.smith/project-config.json` **already exists**, **do not touch it** —
log `SKIPPED .smith/project-config.json (already present)` and move on
to step 2.

Otherwise create the `.smith/` directory if missing, then **detect the
stack** by reading the project's dependency manifests :
- `package.json` / `package-lock.json` for nodejs frameworks (angular,
  react, vue, nextjs, …) + test tools (vitest, jest, playwright, …) +
  build tools (npm, vite, …).
- `pom.xml` / `build.gradle[.kts]` for jvm frameworks (spring-boot,
  micronaut, quarkus, …) + test tools (junit, testcontainers, …) +
  build tools (maven, gradle).
- `requirements.txt` / `pyproject.toml` for python.
- `Cargo.toml`, `go.mod`, `Gemfile`, …
- Top-level `docker-compose.yml`, `Dockerfile`, `terraform/`, `.github/workflows/`
  for `infra_tools`.
- Top-level config / connection strings for `databases`.

**Limit to main frameworks** — do not include fine-grained libraries
(rxjs, lombok, mapstruct, JDBC drivers, …). The intent is a curated
catalogue, not a `package-lock.json` clone.

Tag every entry with kebab-case keywords using the same taxonomy as
`/smith-bundle-add` (role / language / runtime / tier / provider /
integration). Example : Spring Boot → `[java, backend, rest, jpa]`.

Read `${CLAUDE_SKILL_DIR}/../smith-project-config-format/template/project-config.template.json` and
fill every `{{placeholder}}`. Drop the `_comment` field (it's authoring
guidance only). For categories with no detection, set the array to `[]`
rather than fabricating placeholder entries. Atomic write
(tempfile → fsync → rename).

### Step 2 — Create `.smith/smith-config.json` (idempotent)

If `.smith/smith-config.json` **already exists**, **do not touch it** —
log `SKIPPED .smith/smith-config.json (already present)` and move on
to step 3.

Read `${CLAUDE_SKILL_DIR}/../smith-config-format/template/smith-config.template.json` and fill
every `{{placeholder}}`. Drop the `_comment` field. The
`specifications.*` paths point at files **that do not yet exist** —
they will be created by `/smith-generate-docs`. `bundles[]` is empty ;
`/smith-bundle-install` upserts into it later. Atomic write.

### Step 3 — Create `AGENTS.md` at the project root (idempotent)

If `AGENTS.md` **already exists**, **do not touch it** — log
`SKIPPED AGENTS.md (already present)` and move on to step 4.

Read `${CLAUDE_SKILL_DIR}/template/agents.template.md` and fill every
`{{placeholder}}`. Keep the leading HTML comment (it's the
`managed by smith` marker — useful for the refusal check on later
reruns). Atomic write.

This file is kept deliberately short. `/smith-generate-docs` fleshes
out the project narrative under `.smith/`. Users who run a Smith-aware
AI tool from the project root will get this brief on every turn — keep
it cheap in tokens.

### Step 4 — Report back

```
✅ Smith initialised in {{N}}ms.
.smith/project-config.json : <created|skipped>
.smith/smith-config.json   : <created|skipped>
AGENTS.md                  : <created|skipped>

Next : /smith-generate-docs to write the project specs.
```

## What you do NOT do

- **Don't** generate any documentation. That's `/smith-generate-docs`.
- **Don't** adapt any template into a skill. That capability was removed.
- **Don't** overwrite an existing JSON or `AGENTS.md`. Re-running on a
  project that's already initialised is a safe no-op.
- **Don't** dispatch any sub-agent. Stack detection is a quick local
  scan ; keep this skill shell-light and filesystem-only.

## Why this skill is minimal

The previous version of `/smith-init` did everything : pre-flight,
three-phase doc generation, template adaptation, manifest writing. That
made it heavy, slow, and a bad mental model — bootstrap and content
generation are two separable concerns. The split lets users iterate on
docs (`/smith-generate-docs`) without re-bootstrapping, and lets
automation scripts call `/smith-init` confidently on already-initialised
projects.
