---
name: smith-fastapi-bootstrap
description: Interactive scaffold of a new FastAPI 0.115+ service — package name, optional DB (sqlite/postgres) + JWT auth + Docker + GitHub Actions CI. Generates pyproject.toml + src tree + tests + .env, runs `uv sync && uv run pytest` as a smoke check.
model: medium
---

# Skill — Bootstrap a FastAPI service

Scaffolds a runnable FastAPI 0.115+ service from scratch.

## Phase 0 — gather inputs

Ask the user — or read pre-answered hints — for these 5 anchors :

| Hint key       | Default                            | Options                          |
|----------------|------------------------------------|----------------------------------|
| `package_name` | the cwd's basename, snake_cased    | any valid Python package name    |
| `database`     | `none`                             | `none` / `sqlite` / `postgres`   |
| `auth`         | `none`                             | `none` / `jwt`                   |
| `docker`       | `true`                             | `true` / `false`                 |
| `ci`           | `github-actions`                   | `github-actions` / `none`        |

**Zero interactive questions when running under `/smith-new-project`** —
the orchestrator pre-resolves every hint. Answer from defaults if a
hint is missing.

## Phase 1 — generate the project tree

Create at the consumer project root :

```
<consumer>/
├── pyproject.toml
├── README.md
├── .gitignore
├── .python-version            # "3.13"
├── .env.example
├── src/
│   └── <package_name>/
│       ├── __init__.py
│       ├── py.typed
│       ├── main.py
│       ├── config.py
│       └── routers/
│           ├── __init__.py
│           └── health.py
└── tests/
    ├── __init__.py
    └── test_health.py
```

Plus, conditionally :

- `src/<package_name>/db.py` + `alembic.ini` + `migrations/`         (if `database` ≠ `none`)
- `src/<package_name>/auth/` + `routers/users.py`                    (if `auth = jwt`)
- `Dockerfile` + `.dockerignore`                                     (if `docker = true`)
- `.github/workflows/ci.yml`                                         (if `ci = github-actions`)

## Phase 2 — fill the templates

Read each template under
`<consumer>/.smith/bootstraps/fastapi/templates/<file>.tmpl`,
substitute these placeholders, and write to the consumer at the
corresponding destination :

- `{{package_name}}`           → the user's `package_name`
- `{{description}}`            → the description passed by the
  orchestrator
- `{{python_version}}`         → "3.13" (or higher if detected)
- `{{has_db}}`                 → `true` / `false`
- `{{has_jwt}}`                → `true` / `false`
- `{{db_driver}}`              → `sqlite+aiosqlite` / `postgresql+asyncpg` / "" when no DB
- `{{db_default_url}}`         → `sqlite+aiosqlite:///./app.db` / `postgresql+asyncpg://user:pwd@localhost/<package>` / ""

Templates ship the **stack-gated sections** the adapter prunes :

- `pyproject.toml.tmpl` — has commented-out dependency blocks for
  SQLAlchemy + asyncpg + python-jose + passlib + alembic. Uncomment
  the rows matching the user's answers, drop the rest entirely.
- `main.py.tmpl` — has a `lifespan` that conditionally opens / closes
  the DB engine. Drop the DB block when `has_db = false`.
- `.env.example.tmpl` — lists `DATABASE_URL`, `JWT_SECRET`,
  `LOG_LEVEL`. Strip the lines for absent techs.
- `Dockerfile.tmpl` — multi-stage `uv` build + non-root user.

## Phase 3 — install deps + run smoke check

```bash
uv sync --all-extras
bash <consumer>/.smith/bootstraps/fastapi/scripts/smoke_check.sh
```

`smoke_check.sh` runs `uv run pytest -q` against the freshly
generated `tests/test_health.py`. It MUST pass — failures here mean
the scaffold is broken, not the user's code.

## Phase 4 — print the next-steps brief

```
✅ FastAPI service scaffolded at <consumer>/.
   Package : src/<package_name>/

Next steps :
  uv sync
  uv run uvicorn <package_name>.main:app --reload
  → http://localhost:8000/docs

Recommended Smith skills to install :
  /smith-template-install --framework python    --version 3
  /smith-template-install --framework fastapi   --version 0
```

## What you do NOT do

- **Don't ask interactive questions when `discovery_hints` covers
  them.** The orchestrator (`/smith-new-project`) pre-resolves
  everything in Step 2 ; ask only when invoked directly outside the
  workflow.
- **Don't author files outside the consumer project root.** No
  edits to global config (`~/.uv/`, `/etc/`).
- **Don't run `uv publish`.** Publishing belongs to the developer +
  CI on tag pushes.
- **Don't install runtime servers** (Postgres, Redis). The user
  brings them via Docker Compose or a managed service.
- **Don't generate business logic.** This is a structural scaffold
  only — the user fills in domain code afterwards.
