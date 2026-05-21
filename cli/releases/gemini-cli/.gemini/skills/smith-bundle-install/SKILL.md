---
name: smith-bundle-install
description: Installs a bundle from cli/bundles/<name>/ into the consumer project. Assembles each skill at install time by composing the frontmatter from cli/bundles/<name>/skills/<slug>/metadata.yml + <provider>.yml, validated against cli/providers/<provider>/format-skill.yaml, then prepending it to the skill body. Hooks under cli/bundles/<name>/hooks/<provider>/ are merged into the consumer's provider config; sidecar scripts in the same folder are copied to the provider's scripts directory. Trigger with `/smith-bundle-install --name <bundle> --ia <provider>`. Requires /smith-init to have run.
---

# Skill — `/smith-bundle-install`

Copies a bundle from the Smith CLI catalogue into the consumer project,
in the layout the target provider expects. The skill **assembles** each
skill file at install time — it never copies a `SKILL.md` byte-for-byte.

## Pre-conditions

- `<consumer>/.smith/smith.yaml` must exist (the `/smith-init` marker).
  `<consumer>` is the **consumer project directory** — see "Consumer
  directory resolution" below.
- `--name <bundle>` must be a key listed in `cli/bundles/index.yaml`.
- `--ia <provider>` must be in the bundle's `config.yaml` `providers:`
  list AND a known Smith provider (`cli/providers/<provider>/` exists).

## How to invoke

```
/smith-bundle-install --name <bundle> --ia <provider> [--consumer-dir <path>] [--no-config-write]
```

- `--no-config-write` — when set, perform every file write, hook merge,
  and path mapping as usual, but **do NOT mutate
  `<consumer>/.smith/config.json`**. Instead print the fully-built
  bundle entry to stdout (prefixed `BUNDLE_ENTRY:`) so an orchestrator
  can collect entries from parallel installers and serialise the
  writes.

Example :

```
/smith-bundle-install --name mvn --ia claude-code
/smith-bundle-install --name ia-stats --ia claude-code --consumer-dir cli/samples/angular-sample
```

If either of `--name` / `--ia` is missing, ask via `AskUserQuestion`.

## Consumer directory resolution (READ THIS FIRST)

**Every destination path written by this skill is rooted at the
consumer project directory, NEVER at the LLM's current working
directory if those differ.**

Resolution rule, in this order :

1. If `--consumer-dir <path>` is passed, use it (resolved to absolute).
2. Else, walk up from the current working directory until a directory
   containing **`.smith/smith.yaml`** is found; use that.
3. Else, refuse with `consumer-dir-not-found` and ask the user.

**All paths below labelled `<consumer>` resolve against this directory
and only this directory.**

## What you do

1. **Look up the bundle** in `cli/bundles/index.yaml` (read-only). Bail
   if the name is unknown; suggest the closest match by string distance.

2. **Read the bundle's `config.yaml`** and confirm `<provider>` is in
   `providers:`. Bail if not. Also load `config.yaml.skills[]` and
   `config.yaml.hooks[]` — these arrays are the **version index** for
   the install. Every skill / hook version recorded in
   `.smith/config.json` below comes from
   `config.yaml.skills[name=<slug>].version` /
   `config.yaml.hooks[name=<n>].version` (never from `metadata.yml`,
   which no longer carries a version).

   The per-hook `providers:` field has been **removed** — to know
   whether a hook ships for `<provider>`, look on disk: a hook is
   installed for `<provider>` iff a file exists at
   `cli/bundles/<bundle>/hooks/<provider>/<n>.<ext>`. The
   `config.yaml.hooks[]` array is just the name + version listing.

3. **Load the provider's format spec** :
   - `cli/providers/<provider>/provider.yaml` — to find
     `kinds.skill.consumer_path` (e.g.
     `.claude/skills/<slug>/SKILL.md` for Claude Code,
     `.github/prompts/<slug>.prompt.md` for Copilot).
   - `cli/providers/<provider>/format-skill.yaml` — to know the set of
     valid frontmatter fields. The list of allowed field names comes
     from the `frontmatter[].field` entries; required vs optional
     comes from `frontmatter[].required`.

4. **Walk `cli/bundles/<bundle>/skills/`** and assemble one skill at a
   time. For each `skills/<slug>/` directory :

   ### Skill assembly — MANDATORY procedure

   1. **`Read`** `skills/<slug>/<slug>.md` → `body` (already body-only,
      no frontmatter to strip).
   2. **`Read`** `skills/<slug>/metadata.yml` → `meta` dict. Required
      keys : `name`, `description`. **No `version:`** — that field
      lives in `config.yaml.skills[name=<slug>].version`. If
      `metadata.yml` still carries `version:` (stale bundle), drop it
      silently with a warning rather than letting it leak into the
      frontmatter.
   3. **`Read`** `skills/<slug>/<provider>.yml` → `override` dict.
      May be an empty file → treat as `{}`.
   4. **Compose the frontmatter dict** :
      - Start from `meta`.
      - Overlay every key from `override`. `override` wins on
        collisions.
      - **Filename-encoded identity exception** : if `name` is
        present but the provider's `format-skill.yaml` does NOT
        declare `name` as a frontmatter field (e.g. OpenCode encodes
        the slug in the filename, not the frontmatter), DROP `name`
        from the composed dict — silently, no warning. `name` is
        still used to compute the destination path in step 6; it
        just doesn't appear in the YAML header.
      - **Resolve the model tier** : if `model` is present and its
        value is one of `small` / `medium` / `large`, replace it
        with the provider-native model identifier picked up from
        the workflow's tier→model mapping (see "Model tier
        resolution" below). If `model` is already a concrete
        identifier (legacy bundles or explicit override), leave it
        untouched but emit a `model-tier-skipped` warning — bundles
        SHOULD use tiers.
      - **Validate every remaining key** in the final dict against
        the provider's frontmatter spec. A key is valid iff it
        appears in `format-skill.yaml` `frontmatter[].field`. Reject
        any unknown key with `unknown-frontmatter-field` naming the
        bundle, slug, provider, and the offending key. Abort the
        install.

   ### Model tier resolution

   Bundles abstract over the model identifier via three tiers :
   `small` (fast, cheap, simple tasks), `medium` (default, balanced),
   `large` (heavy reasoning).

   Resolution priority :

   1. **Consumer-side mapping** at
      `<consumer>/.smith/smith.yaml` under the `model_tiers:` key
      (written by `/smith-init`). Shape :
      ```yaml
      model_tiers:
        small:  "<provider-native id>"
        medium: "<provider-native id>"
        large:  "<provider-native id>"
      ```
      The mapping is **per-project, single-provider** — `/smith-init`
      already filled it with the right defaults for the active
      provider; the maintainer edits this file by hand to pin a
      different snapshot.
   2. **Built-in defaults** (used only when `.smith/smith.yaml` is
      missing or a tier is absent from the `model_tiers:` map) :
      | Tier   | claude-code | github-copilot         | opencode                            |
      |--------|-------------|------------------------|-------------------------------------|
      | small  | `haiku`     | `Claude Haiku 4.5`     | `anthropic/claude-haiku-4-5`        |
      | medium | `sonnet`    | `Claude Sonnet 4.5`    | `anthropic/claude-sonnet-4-6`       |
      | large  | `opus`      | `Claude Opus 4.7`      | `anthropic/claude-opus-4-7`         |

      These defaults MUST stay in sync with the table embedded in
      `/smith-init`'s SKILL.md (`/smith-init` writes them into
      `smith.yaml` at init time; this skill mirrors them as a
      fallback for projects initialised before the table was bumped).
   5. **Serialise** the frontmatter to YAML between `---` fences. Use
      stable key ordering (`name` first, `description` second, then
      everything else alphabetically). One blank line, then `body`.
   6. **Resolve the destination path** by substituting `<slug>` into
      the provider's `kinds.skill.consumer_path`. Example for
      `claude-code` and slug `mvn` :
      `<consumer>/.claude/skills/mvn/SKILL.md`.
   7. **`Write`** the assembled content. The `Write` tool gives atomic
      semantics. Refuse to overwrite an existing destination (no
      `--force` flag in v0.2).
   8. **Post-condition (MANDATORY)** : re-read the destination and
      verify :
      - Starts with `---` and contains a closing `---` on its own
        line (frontmatter survived).
      - Frontmatter contains at minimum `name:` and `description:`.
      - Frontmatter parses as YAML.
      - The body (everything after the closing `---`) matches the
        source `<slug>.md` byte-for-byte (modulo a leading blank
        line).

      If ANY check fails, abort the bundle install with a clear
      diagnostic naming the failing check + the destination path.

5. **Walk `cli/bundles/<bundle>/hooks/<provider>/`** and process each
   file. For each file :

   ### Hook fragment (`.hooks.json` for claude-code, `.tasks.json` for github-copilot)

   - **Never copied as standalone.** Merged into the consumer's
     provider config per the merge protocol in step 5-bis.

   ### Sidecar script (everything else — `.js` / `.sh` / `.py` / ...)

   - Copy byte-for-byte to the provider's scripts directory :
     - `claude-code` → `<consumer>/.claude/scripts/<file>`
     - `github-copilot` → `<consumer>/.vscode/scripts/<file>`
   - Set the executable bit on `.py` / `.sh` / `.js` extensions.
   - Refuse to overwrite an existing file unless its byte content
     matches exactly (idempotent re-install).

5-bis. **Merge each `.hooks.json` / `.tasks.json` fragment** into the
   consumer's provider config. Algorithm (same for both providers,
   different targets) :

   - **Claude Code** target : `<consumer>/.claude/settings.json`
     (team-shared, committed) — never `settings.local.json`.
   - **GitHub Copilot** target : `<consumer>/.vscode/tasks.json`.

   **Path-safety guard (MANDATORY before reading or writing the merge
   target)** : compute the absolute path of the target and confirm via
   `Bash(realpath …)` that it resolves INSIDE the consumer directory
   (starts with the consumer absolute path). If not, abort with
   `path-escape-detected`.

   Merge procedure :

   a. **Read the destination file**; default to an empty skeleton if
      absent (`{}` for `settings.json`,
      `{"version":"2.0.0","tasks":[]}` for `tasks.json`).
   b. **Read the bundle fragment** and drop its `_comment` field
      (authoring guidance only).
   c. **Tag every fragment entry** with
      `"_smith_source": "<bundle-name>"` :
      - `settings.json::hooks.<event>[]` — each array entry gets the
        marker (alongside its `matcher` / `hooks` fields).
      - `tasks.json::tasks[]` — each task entry gets the marker.
   d. **Idempotent upsert** : in the destination array, **remove**
      every existing entry tagged `_smith_source == "<bundle-name>"`,
      then **append** the freshly-tagged fragment entries. Entries
      from OTHER bundles or hand-written by the user are left
      untouched (different or absent `_smith_source` value).
   e. **Preserve every other top-level key** in the destination
      (`permissions`, `model`, etc. for `settings.json`; arbitrary
      keys for `tasks.json`).
   f. **Atomic write** (tempfile → fsync → rename) with stable JSON
      formatting (2-space indent, trailing newline).
   g. **Post-condition** : re-read the destination, confirm the
      merged events / tasks are present and tagged. Abort with a
      clear error if the file is malformed JSON after the write.

   Track every merged path in the consumer-side `.smith/config.json`
   bundle entry's `merged_into[]` array (see step 7) so a future
   uninstall knows which files to scrub.

6. **Set the executable bit** on any `.py` / `.sh` / `.js` script
   landed under `.claude/scripts/` or `.vscode/scripts/`.

7. **Record the install in `.smith/config.json`** at the consumer
   project root.

   **Behaviour depends on the `--no-config-write` flag** :
   - **Without `--no-config-write`** (default) : perform the upsert
     in-place as described below.
   - **With `--no-config-write`** : SKIP the file mutation and
     instead **emit the fully-built bundle entry as a JSON object on
     stdout**, prefixed by `BUNDLE_ENTRY:`. Do not touch the file.

   In default mode :
   - The canonical shape of the file + `bundles[]` entry shape are
     documented in `smith-config-format`.
   - Read the current `.smith/config.json` (it must exist —
     `/smith-init` created it). In the `bundles[]` array, **upsert**
     an entry keyed by `name`. Re-installing replaces in place.
   - The entry carries :
     - `version` — the bundle's top-level version from
       `cli/bundles/<name>/config.yaml.version`.
     - `skills[]` — for every installed skill, a `{name, version}`
       record where `version` comes from
       `cli/bundles/<name>/config.yaml.skills[name=<slug>].version`
       (NEVER from `metadata.yml`).
     - `hooks[]` — for every installed hook, a `{name, version}`
       record where `version` comes from
       `cli/bundles/<name>/config.yaml.hooks[name=<n>].version`.
     - `merged_into: [<path>, ...]` — every consumer-side config
       file the install merged into during step 5-bis. Empty when
       the bundle ships no hooks.
   - **Preserve unknown keys** : round-trip anything you don't touch.
   - **Update `generated_at`** to the current ISO-8601 UTC time.
   - Atomic write.

8. **Report back** — see "Reporting back" below.

## What you do NOT do

- **Don't `cp` a `SKILL.md` byte-for-byte from a bundle.** Bundles no
  longer ship `SKILL.md` files; they ship a body + metadata + provider
  override, and this skill ASSEMBLES the final `SKILL.md` at install
  time. Any direct copy from `cli/bundles/<name>/skills/<slug>/...` to
  the consumer is wrong.
- **Don't accept unknown frontmatter keys in `<provider>.yml`.** Every
  key must be in the provider's
  `cli/providers/<provider>/format-skill.yaml` `frontmatter[].field`
  list. Unknown keys mean the bundle author made a mistake — abort.
- **Don't install agent files from a bundle.** v0.2 bundles do not
  ship agents. If you find an `agents/` folder in the bundle, ignore
  it and surface a warning — it's stale.
- **Don't print a hooks / tasks snippet** for the user to merge by
  hand. Step 5-bis performs the merge atomically using the
  `_smith_source` marker — that is the only sanctioned path. If the
  merge cannot proceed (corrupt destination JSON, permission error),
  abort with a clear diagnostic rather than falling back to a
  "do-it-yourself" snippet.
- **Don't touch entries in `settings.json` / `tasks.json` that don't
  carry `_smith_source == "<this-bundle>"`.** The merge is scoped : it
  only adds / replaces / removes entries tagged for this exact bundle.
- **Don't merge into `settings.local.json`.** Hooks are team-wide
  behaviour; they belong in the committed `settings.json`.
- **Don't modify `cli/bundles/index.yaml`** (that's
  `/smith-bundle-add` / `/smith-bundle-edit`'s job — it lists the
  catalogue). This skill only writes the consumer-side
  `.smith/config.json` (what's installed in the consumer).
- **Don't install transitive bundles.** If a bundle depends on
  another, the user installs each one explicitly.

## Reporting back

```
✅ Bundle `<name>` installed for provider `<ia>`.
Skills assembled :
  - <slug1> → <destination>
  - <slug2> → <destination>
Scripts copied :
  - <file> → <destination>
Provider config merged :
  - <merge-target>            (e.g. .claude/settings.json)
    + hooks.SubagentStop      (1 entry tagged _smith_source=<name>)
    + hooks.PostToolUse       (1 entry tagged _smith_source=<name>)
```

If the bundle ships no hooks / tasks, omit the "Provider config
merged" block entirely. If it ships no scripts, omit "Scripts
copied".
