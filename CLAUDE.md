<!-- ORCHESTRATOR START -->
Workflow: features and bugfixes flow through `/orchestrator <description>`. Each feature
gets its own folder under `docs/features/NNN-slug/` containing `plan.md`, `specs.md` and
`report.md`. The active feature is tracked at `.smith/feature.json`.

Active feature: **004 — Project page git attach & agentify, plus QoL fixes** (terminée).

- Plan:    `docs/features/004-project-git-agentify/plan.md`
- Tasks:   `docs/features/004-project-git-agentify/tasks.md`

Previous features (read-only history, kept as inheritance reference for the app shell, admin
pages, workspace management, projects, audit history and the role / catalog primitives):
- `docs/features/003-projects/plan.md`
- `docs/features/002-workspace-management/plan.md`
- `docs/features/001-app-shell-admin/plan.md`

For technologies, project structure, dependency direction, quality gates and the dual-id
(UUID v7) discipline, read the active plan first ; then drill into the linked artefacts.
Integration tests live exclusively in `backend/smith-integration/`; the other backend
modules ship pure unit tests only.
<!-- ORCHESTRATOR END -->
