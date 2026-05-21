# Skill — Python packaging (pyproject.toml + src/ layout)

Single source of truth for how this project declares its package,
dependencies, and build artefacts. Auto-loaded when editing
`pyproject.toml` or adding a dependency.

## The basics

- **`pyproject.toml` only.** No `setup.py`, no `setup.cfg`. PEP 621
  metadata everywhere.
- **`src/` layout.** Importable code lives at
  `src/{{root_package}}/...`. Tests at `tests/`. This forces tests to
  import the *installed* package, catching missing files in the wheel.
- **`uv` for dependency management.** Lockfile committed
  (`uv.lock`) ; `uv sync` rehydrates the dev venv.

## `pyproject.toml` skeleton

```toml
[project]
name = "{{root_package}}"
version = "0.1.0"
description = "<one-line>"
authors = [{ name = "Your Name", email = "you@example.com" }]
readme = "README.md"
license = { text = "MIT" }       # or { file = "LICENSE" }
requires-python = ">={{framework_version}}.12"
dependencies = [
  # runtime deps only — pinned ranges, never single versions
  # e.g. "httpx>=0.27,<1.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "pytest-cov>=5",
  "ruff>=0.5",
  "mypy>=1.10",
]

[project.scripts]
{{root_package}} = "{{root_package}}.cli:main"   # if this is a CLI

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{{root_package}}"]
```

`hatchling` is the recommended backend (PEP 517, zero-config). If
you need extension modules or a custom build script, switch to
`setuptools` or `meson-python`.

## Dependency rules

- **Runtime deps stay minimal.** Every `dependencies[]` entry must be
  imported in `src/{{root_package}}/`. Dev-only deps (linters,
  formatters, test tools) go under `[project.optional-dependencies] dev`.
- **Pin to a range, not a single version.** `httpx>=0.27,<1.0` lets
  patch + minor updates flow ; `httpx==0.27.0` doesn't.
- **No `git+` deps in `dependencies[]`.** PyPI only for the published
  artefact. Pre-release deps go through `extra-index-url` or a
  vendored fork.
- **No transitive pins.** Pin only what you directly import. Let `uv`
  resolve the transitive graph.

## Versioning

- **SemVer** : `MAJOR.MINOR.PATCH`. Breaking change → major. Backward-
  compatible feature → minor. Bug fix → patch.
- **Version source = `pyproject.toml`.** Don't duplicate in
  `__init__.py` ; expose it dynamically :
  ```python
  from importlib.metadata import version
  __version__ = version("{{root_package}}")
  ```
- **Tags match the version.** `git tag v0.1.0` matches
  `version = "0.1.0"`. CI rejects mismatches.

## Build + publish

```bash
# Build wheel + sdist into dist/
uv build

# Smoke-test the wheel in a clean venv
uv tool install --from dist/{{root_package}}-0.1.0-py3-none-any.whl {{root_package}}

# Publish (after CI has tagged + tested)
uv publish --token "$PYPI_TOKEN"
```

Never publish from a developer's laptop on a regular basis — only CI
on tag pushes.

## Project structure

```
{{root_package}}/                        # repo root
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .python-version          # for pyenv / uv (e.g. "3.13")
├── uv.lock
├── src/
│   └── {{root_package}}/
│       ├── __init__.py
│       ├── py.typed         # marker — ships type hints to consumers (PEP 561)
│       └── ...
├── tests/
│   ├── __init__.py
│   └── ...
└── docs/                    # optional ; mkdocs or sphinx
```

The `py.typed` empty file matters : without it, downstream type
checkers ignore your hints.

## CI essentials

A minimal GitHub Actions workflow :

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --all-extras
      - run: uv run ruff check src tests
      - run: uv run mypy src
      - run: uv run pytest --cov --cov-fail-under=80
```

## Anti-patterns

- **No `requirements.txt` for application deps.** Use `pyproject.toml`
  + `uv.lock`. `requirements*.txt` is for deployment artefacts only,
  generated from `uv export`.
- **No mixing `setup.py` and `pyproject.toml`.** Pick one ; PEP 621
  is the answer.
- **No editable installs in CI.** `uv sync` installs in editable mode
  for dev ; CI installs the built wheel (matches what users get).
- **Don't commit the venv.** `.venv/` in `.gitignore`.
