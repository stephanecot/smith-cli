# dashboard-ai — releases

## 0.1.0

- Initial release. Replaces the legacy static-HTML `/smith-dashboard`
  skill with a dynamic Node + React-via-CDN web UI.
- Skill body : composes `.smith/dashboard.json` (project + skills +
  agents + bundles + invocation commands per provider), then
  launches `node assets/server.js`.
- Provider-aware invocation generation : `/<slug>`, `@<slug>`,
  VS Code task name, depending on the active provider.
- Zero-dependency runtime : Node ≥18 + a browser.
