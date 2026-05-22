# acme-todo — sample consumer project

Invented showcase project demonstrating what a `.smith/` directory
looks like after `/smith-new-project` has run, plus the JSON
snapshot the `dashboard-ai` bundle produces. The data is synthetic
— there is no actual application code in this folder. Use it to
preview Smith's outputs without running the pipeline yourself.

## What's inside `.smith/`

| File | What it represents |
|---|---|
| `smith.yaml`                  | `/smith-init` marker — init datetime + provider + enabled flag + model-tier mapping. |
| `architecture.json`           | **What the project IS** — detected languages, runtimes, frameworks, build / test / infra tools, databases ; each entry carries a `tags[]` list. Written once by `/smith-init`. |
| `config.json`                 | **What Smith DID** — provider, spec paths, AGENTS.md pointer, adapted skills, installed bundles. Upserted by `/smith-bundle-install` + `/smith-template-install`. |
| `FUNCTIONAL_SPECIFICATION.MD` | Functional spec written by `smith-functional-doc-writer`. |
| `TECHNICAL_SPECIFICATION.MD`  | Architecture brief written by `smith-technical-doc-writer`. |
| `dashboard.json`              | Snapshot produced by the `dashboard-ai` bundle's Node server at startup. Lists every installed skill / agent / bundle with the provider-correct invocation command, plus the full project descriptor. The dashboard UI reads `/api/dashboard` (live) from the same server ; this snapshot file is the offline / scriptable view. |

The fictional `AGENTS.md` brief is also at this folder's root
(it would live at the same path for every supported provider).

## Open the dashboard

After installing the `dashboard-ai` bundle :

```bash
/dashboard-ai          # generate dashboard.json + launch the Node server
```

The UI auto-opens in your browser. To inspect the raw snapshot
without running the server, just open `.smith/dashboard.json` —
it is the data contract the UI renders from.
