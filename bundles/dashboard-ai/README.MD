# dashboard-ai

Web dashboard for a Smith-managed project. Read-only on `.smith/`,
zero-dependency runtime.

## Why

Smith's built-in skills are great for one-shot questions in the
terminal. They are not great when the user wants to **see** what
Smith has done to the project at a glance — which skills are
installed, what they do, how to invoke each one for the active
provider.

`/dashboard-ai` solves that by :

1. Launching a tiny Node HTTP server that serves a React UI
   loaded from CDN. No npm install, no bundler, no build step.
2. The server discovers everything **by scanning the
   consumer's filesystem** at request time — skill + agent
   directories are derived from the path templates in
   `.smith/paths.yaml`, invocation commands are derived from
   the invocation templates in the same file. No provider list
   is hardcoded anywhere ; the bundle works for any provider
   declared in its `paths.yaml`.
3. At startup, the server snapshots the current state to
   `.smith/dashboard.json` for offline inspection / scripting.

## Installation

```
/smith-bundle-install --name dashboard-ai
```

This drops :

- The skill body at the provider's native skill path (resolved
  from `.smith/paths.yaml::skill`).
- The runtime assets under `.smith/skills/dashboard-ai/assets/`
  (server + web UI).

## Usage

```
/dashboard-ai          # generate dashboard.json + launch server, print URL
/dashboard-ai --port 4173
/dashboard-ai --no-open  # skip the browser auto-open
```

## Tags

`observability`, `docs`, `slash-command`.
