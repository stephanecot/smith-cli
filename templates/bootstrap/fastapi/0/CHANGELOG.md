# Changelog — FastAPI 0 bootstrap

All notable changes to this bootstrap are recorded here.

## [0.1.0] — initial

- Interactive scaffold of a FastAPI 0.115+ service.
- Options : DB (none / sqlite / postgres), auth (none / JWT), Docker
  (yes/no), CI (GitHub Actions / none).
- Templates ship under `templates/` ; helper smoke check under
  `scripts/`.
- Smoke check : `uv sync --all-extras && uv run pytest -q`.
