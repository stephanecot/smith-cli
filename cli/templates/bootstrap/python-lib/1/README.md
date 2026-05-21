# Bootstrap — Python library

Scaffolds a **pip-installable Python library** from scratch. Asks for
package name, license, typed-library marker (PEP 561), CI provider ;
generates `pyproject.toml` (PEP 621 + `hatchling`) + `src/` layout +
tests + CHANGELOG + LICENSE + GitHub Actions CI.

## What ships here

```
bootstrap/python-lib/1/
├── config.yaml
├── README.md
├── CHANGELOG.md
├── skill/
│   ├── python-lib.md
│   └── metadata.yml        # name: smith-python-lib-bootstrap
├── assets/                 # license texts copied verbatim
│   ├── LICENSE-MIT
│   └── LICENSE-Apache-2.0
├── templates/              # real templates with placeholders
│   ├── pyproject.toml.tmpl
│   ├── README.md.tmpl
│   ├── __init__.py.tmpl
│   ├── test_smoke.py.tmpl
│   └── ci.yml.tmpl
└── scripts/
    └── smoke_check.sh
```

## Phase 0 questions

| Hint key       | Default                            | Options                          |
|----------------|------------------------------------|----------------------------------|
| `package_name` | dir basename, snake_cased          | any valid Python package name    |
| `license`      | `MIT`                              | `MIT` / `Apache-2.0` / `none`    |
| `typed`        | `true`                             | true / false (drops `py.typed`)  |
| `ci`           | `github-actions`                   | `github-actions` / `none`        |
| `author_name`  | git user.name                      | string                           |
| `author_email` | git user.email                     | string                           |

## What gets generated

- `pyproject.toml` (PEP 621 + hatchling).
- `src/<package>/__init__.py` with `__version__` from `importlib.metadata`.
- `src/<package>/py.typed`             (if `typed=true`).
- `tests/test_smoke.py` (asserts `import <package>` works).
- `LICENSE`                            (if `license≠none`).
- `README.md` with badges + usage skeleton.
- `CHANGELOG.md`.
- `.gitignore` + `.python-version`.
- `.github/workflows/ci.yml`           (if `ci=github-actions`).

## Smoke check

```bash
uv sync --all-extras
uv run pytest -q
```

`test_smoke.py` is intentionally trivial — it imports the package +
asserts `__version__` matches `pyproject.toml`. If that fails the
scaffold is broken.

## Pairs with

- `framework/python/3` (language standards) — install at Step 5.
