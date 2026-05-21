# Changelog — python-lib bootstrap

All notable changes to this bootstrap are recorded here.

## [0.1.0] — initial

- Interactive scaffold of a pip-installable Python library.
- PEP 621 `pyproject.toml` + hatchling backend + src/ layout.
- Options : license (MIT / Apache-2.0 / none), `py.typed` (PEP 561
  marker, default on), CI (GitHub Actions / none).
- Ships LICENSE texts as `assets/` ; templated files under
  `templates/`.
- Smoke check : `uv sync && uv run pytest` (test_smoke.py imports
  the package + asserts `__version__`).
