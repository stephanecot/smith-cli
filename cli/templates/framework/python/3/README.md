# Template — Python 3

Language-level skill templates for **Python 3.12+** projects. These
skills apply to **any** Python codebase — library, CLI, FastAPI /
Django / Flask service, data project — and codify the conventions
the AI follows when writing or reviewing Python code.

## What ships here

| Skill            | Purpose                                                                   |
|------------------|---------------------------------------------------------------------------|
| `standards`      | PEP 8 + idiomatic Python (naming, structure, imports, error handling).    |
| `tests-coverage` | `pytest` patterns + coverage targets + parametrisation conventions.       |
| `typing`         | Strict type hints + mypy / pyright config + protocols vs ABCs.            |
| `packaging`      | `pyproject.toml` PEP 621, `src/` layout, build + publish (`uv`, `build`). |
| `linting`        | `ruff` (formatter + linter unifié) — config + pre-commit setup.           |

Each skill is filterable by `tags[]` ; install only the ones relevant
to the project at `/smith-new-project` time.

## Stack targeted

- Python 3.12+ (3.13 default).
- src/ layout + `pyproject.toml` (PEP 621).
- pytest 8+ for tests.
- ruff for linting + formatting (replaces black + isort + flake8).
- mypy or pyright for static typing.

## Adapter placeholders

The bodies use these placeholders, resolved at install time against
the consumer's `.smith/architecture.json` :

- `{{language}}` → `python`
- `{{runtime}}` → `python3`
- `{{framework_version}}` → `3` (or the precise 3.x.y if detected)
- `{{root_package}}` → the project's top-level package name
