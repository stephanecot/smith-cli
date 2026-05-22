# Skill — Bootstrap a Python library

Scaffolds a pip-installable Python library (PEP 621 + `src/` layout +
`hatchling` backend) from scratch.

## Phase 0 — gather inputs

Ask the user — or read pre-answered hints — for these anchors :

| Hint key       | Default                                 | Options                          |
|----------------|-----------------------------------------|----------------------------------|
| `package_name` | cwd basename, snake_cased               | any valid Python package name    |
| `license`      | `MIT`                                   | `MIT` / `Apache-2.0` / `none`    |
| `typed`        | `true`                                  | `true` / `false`                 |
| `ci`           | `github-actions`                        | `github-actions` / `none`        |
| `author_name`  | `git config user.name`                  | string                           |
| `author_email` | `git config user.email`                 | string                           |

Zero interactive questions when running under `/smith-new-project` —
the orchestrator pre-resolves every hint.

## Phase 1 — generate the tree

At the consumer project root :

```
<consumer>/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── .gitignore
├── .python-version            # "3.13"
├── LICENSE                    # if license ≠ none
├── src/
│   └── <package_name>/
│       ├── __init__.py
│       └── py.typed           # empty file ; only if typed=true
└── tests/
    ├── __init__.py
    └── test_smoke.py
```

Plus, if `ci = github-actions` :

```
.github/
└── workflows/
    └── ci.yml
```

## Phase 2 — fill the templates

For each template under
`<consumer>/.smith/bootstraps/python-lib/templates/<file>.tmpl`,
substitute the following placeholders + write to the consumer at the
matching destination :

- `{{package_name}}`       → user's package name
- `{{description}}`        → description from the orchestrator
- `{{python_version}}`     → "3.13" (or detected `python --version`)
- `{{author_name}}`        → from git or user input
- `{{author_email}}`       → from git or user input
- `{{license_id}}`         → `MIT` / `Apache-2.0` (SPDX) — or skip
  the field when `license=none`
- `{{license_text_url}}`   → SPDX badge URL for the README header
- `{{typed_marker}}`       → `py.typed` line in pyproject when
  `typed=true`, drop otherwise

## Phase 3 — copy the LICENSE asset

When `license ≠ none`, copy the matching file from
`<consumer>/.smith/bootstraps/python-lib/assets/LICENSE-<id>` to
`<consumer>/LICENSE`. Substitute `{{author_name}}` + the current year
inside the LICENSE text.

The `assets/` folder ships verbatim license texts (MIT, Apache-2.0).
Don't generate license text on the fly — copy from the asset.

## Phase 4 — install + smoke check

```bash
uv sync --all-extras
bash <consumer>/.smith/bootstraps/python-lib/scripts/smoke_check.sh
```

`smoke_check.sh` runs `uv run pytest -q` against the generated
`tests/test_smoke.py`, which :
1. Imports the package : `import <package_name>`.
2. Asserts `<package_name>.__version__ == "0.1.0"`.
3. Confirms `py.typed` exists when `typed=true`.

A failure here means the scaffold is broken, not user code.

## Phase 5 — print the brief

```
✅ Python library scaffolded at <consumer>/.
   Package : src/<package_name>/
   License : <license_id> (or "none")
   Typed   : <true|false>

Next steps :
  uv sync
  uv run pytest

Recommended :
  /smith-template-install --framework python --version 3
```

## What you do NOT do

- **Don't generate runtime code** beyond a trivial `__init__.py` with
  `__version__`. The library author writes the actual library.
- **Don't pre-fill `dependencies = [...]`** with anything. The library
  author adds deps as they need them.
- **Don't write the LICENSE text from memory.** Copy the asset
  verbatim — license texts are legally precise.
- **Don't ask the user to choose a build backend.** `hatchling` is
  the recommended default and the only one this bootstrap supports.
  Users who need `setuptools` / `meson-python` / `poetry` can swap
  later.
- **Don't publish to PyPI.** Publishing is on tag pushes from CI, not
  from this scaffold.
