---
name: dashboard-ai
description: Launches a local web dashboard summarising what Smith has done in this project — installed skills, installed agents, installed bundles, project stack, narrative specs — with the provider-correct invocation command for every skill. Reads `.smith/architecture.json` + `.smith/config.json` + the consumer's installed-skills + installed-agents inventory ; writes `.smith/dashboard.json` (the data contract) ; launches `node .smith/skills/dashboard-ai/assets/server.js` on a free port. Zero npm install, no build step, no external runtime beyond Node ≥18. Trigger with `/dashboard-ai`. Requires `/smith-init` and `/smith-bundle-install --name dashboard-ai`.
---

# Skill — `/dashboard-ai`

Launches the project dashboard. The skill body does almost
nothing — every piece of provider knowledge, skill enumeration,
agent enumeration, and invocation composition lives in the Node
script under `assets/server.js`, which discovers everything by
**scanning the consumer's filesystem at request time**.

This skill is provider-agnostic by construction : there is no
list of providers, no list of bin / bundle / template skills,
no per-provider table in this body. Re-shipping a new release
with new providers or new skills does NOT require re-generating
this skill.

## Pre-conditions

The skill refuses to run unless every file below exists. If any
is missing, halt with a one-line diagnostic naming it.

| Path | Why it must exist |
|---|---|
| `<consumer>/.smith/smith.yaml`           | `/smith-init` marker. |
| `<consumer>/.smith/architecture.json`    | Project identity. |
| `<consumer>/.smith/config.json`          | Smith state (installed bundles + adapted skills). |
| `<consumer>/.smith/paths.yaml`           | Provider templates — written by the installer. Without it, the server cannot locate skills / agents nor compose invocations. |
| `<consumer>/.smith/skills/dashboard-ai/assets/server.js` | The Node entry point. Missing → re-run `/smith-bundle-install --name dashboard-ai`. |
| `node` on `PATH` (≥ 18)                  | Runtime. |

## How to invoke

```
/dashboard-ai [--port <n>] [--no-open]
```

- `--port <n>` — port for the HTTP server (default : first free
  port in `4173..4199`).
- `--no-open` — print the URL but do not auto-open the browser.

## What you do

### Step 1 — Pre-flight

Verify every path in the pre-conditions table. Fail fast on the
first missing one. **Do not** open the JSON files, do not
enumerate skills, do not look at providers. That work belongs to
the Node script.

### Step 2 — Resolve a free port

Default range `4173..4199`. If `--port <n>` was passed, use that
port (the script will fail with `EADDRINUSE` if it's busy — let
it propagate).

### Step 3 — Launch the server

Spawn the Node process :

```bash
node <consumer>/.smith/skills/dashboard-ai/assets/server.js \
  --root <consumer> \
  --port <port>
```

Capture stdout until the server prints :

```
Dashboard ready → http://127.0.0.1:<port>
```

That single line is the contract. If the server exits before
printing it, surface stderr to the user and stop.

### Step 4 — Open the browser

Unless `--no-open` was passed, open the URL with the platform
default :

- macOS  : `open <url>`
- Linux  : `xdg-open <url>`
- Windows: `start "" <url>`

### Step 5 — Report

```
✅ Dashboard ready : http://127.0.0.1:<port>
Snapshot written : .smith/dashboard.json
Stop with Ctrl-C in the shell that ran /dashboard-ai.
```

## What you do NOT do

- **Don't** open `.smith/*` files from this body. The Node
  server reads them itself at every request, so the dashboard
  always reflects the current state.
- **Don't** enumerate any provider directory. The Node server
  discovers skills + agents by walking the path templates it
  reads from `paths.yaml` — no list of providers, no list of
  conventions, no fallback table belongs in this body.
- **Don't** compose invocation strings here. The Node server
  pulls the templates from `paths.yaml` and substitutes the
  slug. The body never sees a `/`, `@`, or any other invocation
  syntax.
- **Don't** maintain a list of "bin" / "adapted" / "bundle"
  skill names. The Node server classifies every discovered
  skill by cross-referencing the consumer's `config.json` ;
  this body is unaware of which skills exist.
- **Don't** mutate the consumer source code. The server is
  read-only except on the snapshot file it writes once at
  startup (`.smith/dashboard.json`).
- **Don't** keep the server alive across `/dashboard-ai`
  invocations. Each run starts a fresh process ; Ctrl-C in the
  host shell stops it.
