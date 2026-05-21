# Bootstrap — FastAPI 0

Scaffolds a runnable **FastAPI 0.115+** service from scratch. Asks
the user a small set of structuring questions (package name, DB,
auth, Docker, CI), then generates the project tree.

## What ships here

```
bootstrap/fastapi/0/
├── config.yaml             # bootstrap metadata + tags + sidecars
├── README.md
├── CHANGELOG.md
├── skill/
│   ├── fastapi.md          # the orchestrator body
│   └── metadata.yml        # name: smith-fastapi-bootstrap
├── templates/              # real templates with placeholders
│   ├── pyproject.toml.tmpl
│   ├── main.py.tmpl
│   ├── .env.example.tmpl
│   └── Dockerfile.tmpl
└── scripts/
    └── smoke_check.sh      # runs uv sync + pytest as the smoke test
```

## Phase 0 questions (the bootstrap asks at run time)

| Hint key       | Default        | Options                          |
|----------------|----------------|----------------------------------|
| `package_name` | dir basename   | snake_case Python package name   |
| `database`     | `none`         | `none` / `sqlite` / `postgres`   |
| `auth`         | `none`         | `none` / `jwt`                   |
| `docker`       | `true`         | true / false                     |
| `ci`           | `github-actions` | `github-actions` / `none`     |

These default to sensible values when the orchestrator runs without
interactive answers (it passes them through `discovery_hints`).

## What gets generated

- `pyproject.toml` (PEP 621, dependencies tuned to the answers).
- `src/<package>/main.py` (FastAPI app with `lifespan` + one router).
- `src/<package>/config.py` (pydantic-settings).
- `src/<package>/routers/health.py` (always) + `users.py` (if auth=jwt).
- `src/<package>/auth/` (if auth=jwt).
- `src/<package>/db.py` (if database≠none).
- `tests/test_health.py` (always).
- `.env.example`.
- `Dockerfile` + `.dockerignore` (if docker=true).
- `.github/workflows/ci.yml` (if ci=github-actions).
- `README.md` + `.gitignore`.

## Smoke check

After scaffolding the tree, the skill runs :

```bash
uv sync --all-extras
uv run pytest -q
```

If both pass, the scaffold reports success.

## Pairs with

- `framework/python/3` (language standards) — install at Step 5.
- `framework/fastapi/0` (FastAPI conventions) — install at Step 5.
