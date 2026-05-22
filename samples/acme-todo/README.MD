# acme-todo — sample consumer project

Invented showcase project demonstrating what a `.smith/` directory looks
like after `/smith-init` has run, plus the dashboard `/smith-dashboard`
renders from it. The data is synthetic — there is no actual application
code in this folder. Use it to preview Smith's outputs without running
the pipeline yourself.

## What's inside `.smith/`

| File | What it represents |
|---|---|
| `FUNCTIONAL_SPECIFICATION.MD` | Functional spec written by `smith-functional-doc-writer` (Phase 1). |
| `TECHNICAL_SPECIFICATION.MD` | Architecture brief written by `smith-technical-doc-writer` (Phase 1). |
| `architecture.json` | **What the project IS** — detected languages, runtimes, frameworks, build / test / infra tools, databases ; each entry carries a `tags[]` list. Written once by `/smith-init`. Not touched by `/smith-bundle-install` or `/smith-generate-docs`. |
| `config.json` | **What Smith DID** — provider, spec paths, AGENTS.md pointer, list of installed bundles (version + tags + files). Upserted by `/smith-bundle-install`. |
| `dashboard.html` | Static HTML overview rendered from both JSONs by `/smith-dashboard`. Open in a browser. |

The fictional `CLAUDE.md` Phase-3 brief is also at this folder's root
(would be `AGENTS.md` for the github-copilot provider).

## Open the dashboard

```bash
open .smith/dashboard.html        # macOS
xdg-open .smith/dashboard.html    # Linux
```
