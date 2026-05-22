# Template — FastAPI 0.115+

Skill templates for **FastAPI 0.115+** services. These build on top
of `framework/python/3` (language-level conventions) and codify
FastAPI-specific patterns the AI follows when writing endpoints,
schemas, dependencies, and auth.

## What ships here

| Skill              | Purpose                                                              |
|--------------------|----------------------------------------------------------------------|
| `standards`        | Router structure, endpoint signatures, response models, status codes. |
| `pydantic-models`  | Schema patterns (Input vs Output), validators, settings via Pydantic. |
| `async-patterns`   | async/await + SQLAlchemy `ext.asyncio` session + background tasks.    |
| `auth-jwt`         | JWT/OAuth2 flow with `python-jose` + `passlib` ; security depends.    |

## Stack targeted

- FastAPI 0.115+ (modern lifespan, async-by-default).
- Pydantic v2.
- Python 3.12+ (signals : `Annotated`, PEP 695 generics).
- Optional : SQLAlchemy 2.x + asyncpg, Redis, `python-jose`, `passlib`.

## Pairs with

- `framework/python/3` for Python language standards.
- `bootstrap/fastapi/0` for initial project scaffold (pyproject,
  `app/main.py`, first router, tests, Docker).
