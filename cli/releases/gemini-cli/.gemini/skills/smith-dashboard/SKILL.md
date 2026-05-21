---
name: smith-dashboard
description: Generates a self-contained static HTML dashboard at .smith/dashboard.html by combining .smith/architecture.json (tech stack) + .smith/config.json (adapted skills + installed bundles + spec paths). Single-page overview of the project's Smith state with frameworks, build/test/infra tools, skills with their source template, bundles with version + tags + files, and links to the spec files. Uses a fixed HTML template so the rendering stays consistent across regenerations. Trigger with `/smith-dashboard`. Requires /smith-init to have run.
---

# Skill — `/smith-dashboard`

Renders a one-page static HTML dashboard summarising everything Smith
knows about the consumer project. Read-only on
`.smith/architecture.json` + `.smith/config.json` ;
write-only on `.smith/dashboard.html`. **No script, no dependencies.**
You do the rendering inline by string-substituting the template at
`${CLAUDE_SKILL_DIR}/templates/dashboard.template.html`.

## Pre-conditions

- `.smith/FUNCTIONAL_SPECIFICATION.MD` must exist (`/smith-init` marker).
- `.smith/architecture.json` must exist (tech stack).
- `.smith/config.json` must exist (Smith outputs + skills + bundles).
  If either is missing, halt and tell the user to re-run `/smith-init`.

## How to invoke

```
/smith-dashboard
```

No arguments. Re-running overwrites the previous `dashboard.html`.

## What you do

1. **Read both JSON files** from the consumer project's root —
   `.smith/architecture.json` (call it `pc`) and `.smith/config.json`
   (call it `sc`).
2. **Read the template** at `${CLAUDE_SKILL_DIR}/templates/dashboard.template.html`.
3. **Build the substitution map** — for each placeholder below, compute
   the value from the right file ; default to `"—"` (em-dash) when missing.
   HTML-escape every value (`&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`,
   `"` → `&quot;`).

   | Placeholder | Source | Notes |
   |---|---|---|
   | `{{project_name}}` | `pc.project.name` | |
   | `{{project_summary}}` | `pc.project.summary` | If absent, render `"Smith-managed project."`. |
   | `{{project_languages}}` | `pc.project.languages[]` | Join `"<name> <version>"` with `", "`. |
   | `{{project_runtimes}}` | `pc.project.runtimes[]` | Same join. |
   | `{{project_frameworks}}` | `pc.project.frameworks[]` | Same join. |
   | `{{project_build_tools}}` | `pc.project.build_tools[]` | Same join. |
   | `{{project_test_tools}}` | `pc.project.test_tools[]` | Same join. |
   | `{{project_infra_tools}}` | `pc.project.infra_tools[]` | Same join. |
   | `{{project_databases}}` | `pc.project.databases[]` | Same join. |
   | `{{provider}}` | `sc.provider` | |
   | `{{smith_cli_version}}` | `sc.smith_cli_version` | |
   | `{{generated_at}}` | `sc.generated_at` | |
   | `{{git_sha}}` | `pc.project.git_sha` | |
   | `{{skills_count}}` | `len(sc.skills)` | |
   | `{{skills_table}}` | derived from `sc.skills[]` | See section below. |
   | `{{bundles_count}}` | `len(sc.bundles)` | |
   | `{{bundles_cards}}` | derived from `sc.bundles[]` | See section below. |
   | `{{spec_functional}}` | `sc.specifications.functional` | |
   | `{{spec_technical}}` | `sc.specifications.technical` | |
   | `{{spec_generation_report}}` | `sc.specifications.generation_report` | |
   | `{{ai_memory_file}}` | `sc.ai_memory_file` | |

4. **Render `{{skills_table}}`** — if `skills[]` is empty, emit
   `<p class="empty">No skills installed yet — bundles ship skills via /smith-bundle-install.</p>`.
   Otherwise emit :
   ```html
   <table>
     <thead><tr><th>Name</th><th>From template</th><th>Installed at</th><th>Adapted at</th></tr></thead>
     <tbody>
       <tr><td><code>{name}</code></td><td><code>{from_template}</code></td><td><code>{path}</code></td><td>{adapted_at}</td></tr>
       ...
     </tbody>
   </table>
   ```

5. **Render `{{bundles_cards}}`** — if `bundles[]` is empty, emit
   `<div class="card"><p class="empty">No bundles installed yet. Run /smith-bundle-install to add one.</p></div>`.
   Otherwise emit one `<div class="bundle-card">` per bundle :
   ```html
   <div class="bundle-card">
     <h3>{name} <span class="tag tag-green">v{version}</span></h3>
     <p class="desc">Provider: <code>{provider}</code> · Installed: {installed_at}</p>
     <div>
       <span class="tag tag-accent">{tag1}</span>
       <span class="tag tag-accent">{tag2}</span>
       ...
     </div>
     <ul class="files">
       <li><span class="tag tag-steel">{kind}</span> {destination_or_source}</li>
       ...
     </ul>
   </div>
   ```

6. **String-substitute** every placeholder in the template with its
   computed value. Two runs against the same `architecture.json` +
   `config.json` MUST produce byte-identical HTML.

7. **Write `.smith/dashboard.html`** atomically (write to
   `.smith/dashboard.html.tmp`, then `mv` over the final path). Use the
   `Write` tool for the final file — never edit a partial output.

8. **Report back** :
   ```
   ✅ Dashboard rendered → .smith/dashboard.html
   {{N}} adapted skills • {{M}} installed bundles • last init {{date}}.
   Open with `open .smith/dashboard.html` (macOS) or your browser.
   ```

## What you do NOT do

- Don't invoke any external tool, language runtime, or package manager.
  The rendering happens entirely through your `Read` + `Write` capabilities.
- Don't edit `.smith/architecture.json` or `.smith/config.json` —
  the mutator skills (`/smith-init`, `/smith-bundle-install`,
  `/smith-bundle-install`) own them.
- Don't add data to the dashboard that isn't already in those two files.
  If you'd like to display a new field, add it to the right JSON first
  via the mutator skill that writes it, then update the template + this
  skill's substitution map.
- Don't auto-open the file — print the path and let the user click.

## Why a fixed template (and no script)

The HTML template is hand-authored, self-contained (inlined CSS, no JS
dependencies), and designed for a stable visual rendering across every
regeneration. By delegating the substitution to your skill body (rather
than a Python or shell script), the bundle stays dependency-free :
nothing to install, nothing to maintain.

## How to extend

Open `template/dashboard.template.html` and add a new section using the
`{{placeholder}}` convention. Then update the substitution map above so
the skill knows how to populate it from `index.json`.
