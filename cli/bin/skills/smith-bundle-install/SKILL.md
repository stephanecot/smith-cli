---
name: smith-bundle-install
description: Installs a bundle from cli/bundles/<name>/ into the consumer project's .claude/ (or .github/ for Copilot). Copies files declared in the bundle's config.yaml for the target provider. Trigger with `/smith-bundle-install --name <bundle> --ia <provider>`. Requires /smith-init to have run.
---

# Skill — `/smith-bundle-install`

Copies a bundle from the Smith CLI catalogue into the consumer project, in
the layout the target provider expects.

## Pre-conditions

- `<consumer>/.smith/smith.yaml` must exist (the `/smith-init` marker).
  `<consumer>` is the **consumer project directory** — see "Consumer
  directory resolution" below.
- `--name <bundle>` must be a key listed in `cli/bundles/config.json`.
- `--ia <provider>` must be in the bundle's `config.yaml` `providers:` list.

## How to invoke

```
/smith-bundle-install --name <bundle> --ia <provider> [--consumer-dir <path>] [--no-config-write]
```

- `--no-config-write` — when set, the install performs every file
  copy, hook merge and path mapping as usual, but **does NOT mutate
  `<consumer>/.smith/config.json`**. Instead it prints the
  fully-built bundle entry (the JSON object that would have been
  upserted into `bundles[]`) to stdout so an orchestrator can collect
  it and write all entries serially in one pass. Used by
  `/smith-new-project` to avoid the race when several bundle
  installers run in parallel.

Example :

```
/smith-bundle-install --name mvn --ia claude-code
/smith-bundle-install --name ia-stats --ia claude-code --consumer-dir cli/samples/angular-sample
```

If either of `--name` / `--ia` is missing, ask via `AskUserQuestion`.

## Consumer directory resolution (READ THIS FIRST)

**Every destination path written by this skill is rooted at the
consumer project directory, NEVER at the LLM's current working
directory if those differ.** This is the difference between merging
`ia-stats` hooks into the sample-as-consumer
(`cli/samples/angular-sample/.claude/settings.json`) and accidentally
polluting the parent repo
(`.claude/settings.json` at the Smith CLI repo root).

Resolution rule, in this order :

1. If `--consumer-dir <path>` is passed, use it (resolved to absolute).
2. Else, walk up from the current working directory until a directory
   containing **`.smith/smith.yaml`** is found ; use that.
3. Else, refuse with `consumer-dir-not-found` and ask the user.

When the orchestrator (`/smith-new-project`) dispatches the
`smith-new-project-bundle-installer` sub-agent, that sub-agent passes
`--consumer-dir` explicitly so this resolution is unambiguous even
when the sub-agent's CWD is something else.

**All paths below labelled `<consumer>` resolve against this directory
and only this directory.** Never use a bare `.claude/settings.json` or
`./...` — always prefix with the resolved consumer dir (absolute path
preferred) so that an IDE / sub-agent running from a different CWD
still writes to the right place.

## What you do

1. **Look up the bundle** in `cli/bundles/config.json` (read-only). Bail if the
   name is unknown ; suggest the closest match by string distance.
2. **Read the bundle's `config.yaml`** to find the `files.<provider>:` list.
   Bail if the bundle does not declare support for the requested provider.
3. **Map source → destination paths.** Every destination is rooted at
   the resolved `<consumer>` directory (see "Consumer directory
   resolution" above). The `<bundle-root>` prefix is
   `cli/bundles/<bundle>/`.
   - `<bundle-root>/claude-code/skills/<slug>/SKILL.md` → `<consumer>/.claude/skills/<slug>/SKILL.md`
   - `<bundle-root>/claude-code/agents/<slug>.md`       → `<consumer>/.claude/agents/<slug>.md`
   - `<bundle-root>/claude-code/scripts/<name>.<ext>`   → `<consumer>/.claude/scripts/<name>.<ext>`
     (executable bit set in step 5 for `.py` / `.sh` / `.js`)
   - `<bundle-root>/common/scripts/<name>.<ext>`        → `<consumer>/.claude/scripts/<name>.<ext>`
     (Claude Code) or `<consumer>/.vscode/scripts/<name>.<ext>` (Copilot)
   - `<bundle-root>/claude-code/hooks/<name>.hooks.json` → **merge** into
     `<consumer>/.claude/settings.json` per the algorithm in step
     4-bis below. Never copied as-is, never printed for the user to
     merge by hand.
   - `<bundle-root>/github-copilot/skills/<slug>/SKILL.md` → `<consumer>/.github/prompts/<slug>.prompt.md`
     (per the provider's convention)
   - `<bundle-root>/github-copilot/agents/<slug>.agent.md` → `<consumer>/.github/chatmodes/<slug>.chatmode.md`
   - `<bundle-root>/github-copilot/tasks/<name>.tasks.json` → **merge** into
     `<consumer>/.vscode/tasks.json` per the algorithm in step 4-bis
     below.
4. **Install each file. Two categories — DIFFERENT TOOLS for each.**

   ### Category A — Wrapper files (`kind: skill` / `kind: agent`)

   These are markdown files whose body is the single line :

   ```
   <!-- @smith-include: <relative-path-to-common-body> -->
   ```

   **❌ FORBIDDEN TOOLS for wrapper files** : `Bash(cp …)`,
   `Bash(mv …)`, `Bash(cat … > …)`, `Bash(xcopy …)`,
   `PowerShell(Copy-Item …)`, or any other byte-for-byte file copy.
   Using any of these on a wrapper file is a **contract violation** —
   it leaks raw `@smith-include` directives into the consumer project
   and the verifier (`no-unresolved-smith-includes` check) will fail.

   **✅ MANDATORY procedure** (use the `Read` and `Write` tools, in
   that order, for each wrapper file — never shell out) :

   1. **`Read` the source wrapper** at the absolute path under
      `cli/bundles/<bundle>/<provider>/skills/<slug>/SKILL.md` (or
      `.../agents/<slug>.md`).
   2. **Split** the content :
      - `frontmatter` = everything from the leading `---` through the
        next `---` on its own line, inclusive of both delimiters.
      - `body` = everything after the closing `---` (lstrip blank
        lines).
   3. **Find the `@smith-include` directive** in `body`. There MUST
      be exactly one line matching the regex
      `<!--\s*@smith-include:\s*(\S+)\s*-->`. Refuse with a clear
      error if zero or >1 — the bundle is malformed.
   4. **Resolve the relative path** against the **wrapper's own
      directory** under `cli/bundles/<bundle>/`. Example : for
      `cli/bundles/ia-stats/claude-code/skills/ia-stats/SKILL.md`
      with directive
      `<!-- @smith-include: ../../../common/skills/ia-stats.md -->`,
      the target is
      `cli/bundles/ia-stats/common/skills/ia-stats.md`.
   5. **`Read` the common body** at the resolved path. Refuse with a
      clear error if the file does not exist.
   6. **Assemble** the destination content : `frontmatter` + newline
      + blank line + `common-body-trimmed` + final newline. The
      `<!-- @smith-include: ... -->` line is **stripped completely**
      — it must NOT appear in the output.
   7. **`Write`** the assembled content to the consumer destination
      (`.claude/skills/<slug>/SKILL.md` or `.claude/agents/<slug>.md`).
      The `Write` tool gives you atomic semantics. Refuse to
      overwrite an existing destination (no `--force` flag in v0.1).
   8. **Content verification (MANDATORY)** : after `Write`, **`Read`
      the destination back** and check **every one** of these :
      - The destination starts with `---` and contains a closing
        `---` on its own line (frontmatter survived).
      - The frontmatter contains at minimum `name:` and
        `description:` keys.
      - The destination contains the **first 100 characters** of the
        common-body content (verbatim substring match) — proves the
        inline actually happened.
      - **Zero** occurrences of the literal token `@smith-include`
        anywhere in the file.
      - The file size is reasonably > 0 and within ±20% of
        (`len(frontmatter) + len(common_body)`).

      If ANY check fails, abort the bundle install with a clear
      diagnostic naming the failing check + the destination path.
      Never silently let a partially-resolved or broken wrapper land
      in the consumer project.

   ### Category B — Plain-copy files (`kind: script`, `kind: rules`, README, …)

   Byte-for-byte copy is the right behaviour here. **`Bash(cp …)`** is
   acceptable for this category only (still atomic, still refuses
   overwrite). Or use `Read` + `Write` if you prefer — both work.

   **Content verification (MANDATORY here too)** : after the copy,
   `Read` the destination and check :
   - The destination size matches the source size exactly (byte
     count).
   - The first 200 bytes of the destination match the first 200 bytes
     of the source (verbatim).

   If either check fails, abort the install.

   ### Common to both categories

   **`common/` files themselves are NEVER copied to the consumer
   project.** They are a build-time concept (single-source factorised
   bodies). Only their content lands in the consumer — inlined into
   the wrappers via the procedure above.

4-bis. **Merge provider config — auto-wire the hooks / tasks.** A
   bundle's hooks (Claude Code) and tasks (Copilot) are NEVER copied
   as standalone files into the consumer project. They are **fragments
   that must be merged** into the provider's live config so the
   provider actually picks them up. Algorithm :

   - **Claude Code** : the source
     `cli/bundles/<name>/claude-code/hooks/<file>.hooks.json` is
     merged into **`<consumer>/.claude/settings.json`** (team-shared,
     committed) — where `<consumer>` is the resolved consumer
     directory from the pre-flight, **not** the LLM's CWD or any
     parent repository's `.claude/`. Never into `settings.local.json`
     (hooks are team-wide behaviour, not per-developer).
   - **GitHub Copilot** : the source
     `cli/bundles/<name>/github-copilot/tasks/<file>.tasks.json` is
     merged into **`<consumer>/.vscode/tasks.json`**, with the same
     consumer-rooted discipline.

   **Common path-safety guard (MANDATORY before reading or writing
   the merge target)** : compute the absolute path of the target as
   `<absolute consumer dir> + "/.claude/settings.json"` (or
   `"/.vscode/tasks.json"`) and confirm via `Bash(realpath …)` or
   equivalent that the resolved absolute path is **inside** the
   consumer directory (i.e. starts with the consumer absolute path).
   If it does not — abort with `path-escape-detected`. This catches
   symlink shenanigans, `..` segments in the consumer dir input, or
   confusion where the LLM walks up to a parent repo's `.claude/`.

   Merge procedure (same logic for both targets) :

   a. **Read the destination file** ; default to an empty skeleton if
      absent (`{}` for `settings.json`, `{"version":"2.0.0","tasks":[]}`
      for `tasks.json`).
   b. **Read the bundle fragment** and drop its `_comment` field
      (authoring guidance only).
   c. **Tag every fragment entry** with
      `"_smith_source": "<bundle-name>"` :
      - `settings.json::hooks.<event>[]` — each array entry gets the
        marker (alongside its `matcher` / `hooks` fields).
      - `tasks.json::tasks[]` — each task entry gets the marker.
   d. **Idempotent upsert** : in the destination array, **remove**
      every existing entry where `_smith_source == "<bundle-name>"`,
      then **append** the freshly-tagged fragment entries. This means
      re-installing the same bundle (or a newer version) replaces
      Smith-managed entries in place — never duplicates — and entries
      from OTHER bundles or hand-written by the user are left
      untouched (no `_smith_source` field or different value).
   e. **Preserve every other top-level key** in the destination
      (`permissions`, `model`, etc. for `settings.json` ; arbitrary
      keys for `tasks.json`).
   f. **Atomic write** (tempfile → fsync → rename) with stable JSON
      formatting (2-space indent, trailing newline).
   g. **Post-condition** : re-read the destination, confirm the
      merged events / tasks are present and tagged. Abort with a
      clear error if the file is malformed JSON after the write.

   Track the merge in the consumer-side `.smith/config.json` bundle
   entry's `merged_into[]` array (see step 6) so a future uninstall
   knows which files to scrub.

5. **Set the executable bit** on any `.py` / `.sh` / `.js` script that
   lands under `.claude/scripts/` (Claude Code) or `.vscode/scripts/`
   (Copilot).
6. **Record the install in `.smith/config.json`** at the consumer
   project root.

   **Behaviour depends on the `--no-config-write` flag** :
   - **Without `--no-config-write`** (default) : perform the upsert
     in-place as described below.
   - **With `--no-config-write`** : SKIP the file mutation and
     instead **emit the fully-built bundle entry as a JSON object on
     stdout**, prefixed by the line `BUNDLE_ENTRY:` so the calling
     orchestrator can collect it. Do not touch the file at all.
     This mode is used by `/smith-new-project` when several bundle
     installers run in parallel — the orchestrator collects every
     entry, then writes them all serially in one final pass, avoiding
     the read-write race that clobbers parallel upserts.

   In default mode :
   - The canonical shape of the file + the `bundles[]` entry shape are
     documented in the sibling skill **`smith-config-format`** ; consult
     its body and use the template at
     `${CLAUDE_SKILL_DIR}/../smith-config-format/template/config.template.json`
     as the source of truth for any key you might touch.
   - Read the current `.smith/config.json` (it must exist —
     `/smith-init` created it). In the `bundles[]` array, **upsert** an
     entry keyed by `name`, matching the shape in `smith-config-format`
     (kind / source / destination / installed_at). Re-installing the
     same bundle replaces the existing entry in place — never duplicates.
   - The bundle entry MUST also carry a **`merged_into: [<path>, ...]`**
     array listing every consumer-side config file the install merged
     into during step 4-bis (typically `.claude/settings.json` for
     Claude Code, `.vscode/tasks.json` for Copilot). Empty array
     when the bundle ships no hooks / tasks. The future uninstall
     skill reads this list to know where to scrub Smith-tagged
     entries.
   - **Preserve unknown keys** : round-trip anything in
     `config.json` that you don't explicitly touch.
   - **Update `generated_at`** to the current ISO-8601 UTC time on every
     successful write.
   - Atomic write (tempfile → fsync → rename).
   - **Do not touch `.smith/architecture.json`** — that file describes
     the project's tech stack, not what Smith installed. Format spec
     lives in the sibling skill `smith-architecture-format`.
7. **Tell the user what changed** — see "Reporting back" below. There is
   no longer a manual snippet to paste : step 4-bis already merged the
   hooks / tasks into the live provider config.

## What you do NOT do

- **Don't ever `cp` a wrapper file.** Files with `kind: skill` /
  `kind: agent` MUST go through the `Read` + parse + `Write` procedure
  in step 4 (Category A). `Bash(cp ...)`, `Bash(mv ...)`,
  `PowerShell(Copy-Item ...)` and friends are **forbidden** on these
  files — they preserve the `<!-- @smith-include: ... -->` directive
  literally, leaving raw build-time directives in the consumer
  project. The verifier's `no-unresolved-smith-includes` check
  catches this and fails the run.
- **Don't leave any `@smith-include` directive in the installed
  files.** Every wrapper's directive MUST be inlined before the
  destination is written. The directive is a build-time mechanism —
  its presence in the consumer's `.claude/` or `.github/` tree is a
  bug. The step-4 self-check exists precisely to catch this.
- **Don't copy `common/` files** to the consumer project. Their
  content lands inlined into the wrappers (skills / agents) or shipped
  to the provider's scripts dir if `kind: script` (see step 3 mapping).
  The `common/` tree itself stays inside `cli/bundles/<bundle>/`.
- **Don't print a hooks / tasks snippet** for the user to merge by
  hand. Step 4-bis performs the merge atomically using the
  `_smith_source` marker — that is now the only sanctioned path. If
  for some reason the merge cannot proceed (corrupt destination JSON,
  permission error), abort with a clear diagnostic rather than
  falling back to the old "here, do it yourself" snippet.
- **Don't touch entries in `settings.json` / `tasks.json` that don't
  carry `_smith_source == "<this-bundle>"`.** The merge is scoped : it
  only adds / replaces / removes entries tagged for this exact bundle.
  Anything hand-written by the user, or owned by another bundle, is
  preserved untouched.
- **Don't merge into `settings.local.json`.** Hooks are team-wide
  behaviour ; they belong in the committed `settings.json`. Per-dev
  overrides go in `settings.local.json` by hand.
- Don't modify `cli/bundles/config.json` (that's `/smith-bundle-add`'s job —
  it lists the catalogue). This skill only writes the consumer-side
  `.smith/config.json` (which lists what's installed in the consumer).
- Don't install transitive bundles. If a bundle depends on another, the
  user installs each one explicitly. Dependencies are reported in the
  bundle's README.

## Reporting back

```
✅ Bundle `<name>` installed for provider `<ia>`.
Files copied :
  - <source> → <destination>
  - ...
Provider config merged :
  - <merge-target>            (e.g. .claude/settings.json)
    + hooks.SubagentStop      (1 entry tagged _smith_source=<name>)
    + hooks.PostToolUse       (1 entry tagged _smith_source=<name>)
```

If the bundle ships no hooks / tasks, omit the "Provider config
merged" block entirely.
