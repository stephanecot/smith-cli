---
name: smith-fastapi-standards
description: FastAPI {{framework_version}} conventions — modular routers, endpoint signature style, response models, HTTP status codes, error responses. Apply when adding endpoints or routers.
---

# Skill — FastAPI {{framework_version}} standards

Conventions for endpoints, routers, and HTTP behaviour. Auto-loaded
when editing FastAPI endpoint code.

## Router structure

- **One router per resource**, in its own module under
  `src/{{root_package}}/routers/<resource>.py`.
- Routers carry a `prefix` + `tags` matching the resource :
  ```python
  router = APIRouter(prefix="/users", tags=["users"])
  ```
- `app.include_router(...)` lives **only** in
  `src/{{root_package}}/main.py`. Routers don't include other
  routers (no recursion).
- Sub-resources use nested paths in the same router, not separate
  router files : `GET /users/{user_id}/projects` lives in
  `routers/users.py`, not `routers/projects.py` (unless the project
  resource has its own top-level path too).

## Endpoint signatures

```python
@router.get("/{user_id}", response_model=UserOut, status_code=200)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_auth),
) -> UserOut:
    user = await users.find_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user-not-found")
    return UserOut.model_validate(user)
```

Rules :
- **Always `async def`** — even for endpoints that don't await
  anything. Mixing sync + async handlers fragments the event loop.
- **Type-hint every parameter + the return.** The return hint matches
  `response_model=` (defensive — both must agree).
- **Path / query / body extraction is explicit.** Path params come
  from the route ; query params are `Annotated[str, Query(...)]` ;
  body is `Annotated[Schema, Body(...)]`. Dependencies are
  `= Depends(...)`.
- **Dependencies last in the signature.** Path → query → body →
  dependencies. Helps readability.

## Path conventions

- `/<plural-resource>` for collections (`/users`, `/projects`).
- `/<plural-resource>/{id}` for items.
- `/<plural-resource>/{id}/<sub-resource>` for nested.
- **kebab-case** in URLs (`/billing-accounts`) — never camelCase or
  snake_case.
- Query params : kebab-case in the URL, snake_case in the Python
  parameter (`Query(alias="sort-by")`).

## HTTP status codes

| Operation                       | Status                                      |
|---------------------------------|---------------------------------------------|
| Read OK                         | `200 OK`                                    |
| Create OK                       | `201 Created` + `Location` header           |
| Update OK (no body)             | `204 No Content`                            |
| Update OK (return updated)      | `200 OK`                                    |
| Delete OK                       | `204 No Content`                            |
| Long-running started            | `202 Accepted`                              |
| Client validation failure       | `422 Unprocessable Entity` (FastAPI default for Pydantic errors) |
| Resource not found              | `404 Not Found`                             |
| Auth missing                    | `401 Unauthorized`                          |
| Auth present, wrong rights      | `403 Forbidden`                             |
| Idempotent retry conflict       | `409 Conflict`                              |
| Rate limit                      | `429 Too Many Requests`                     |
| Server bug                      | `500 Internal Server Error` (let FastAPI render it) |

Declare `status_code=` on every endpoint decorator — don't rely on
the default `200`.

## Error responses

- **Use `HTTPException`** with a short, kebab-case `detail` token —
  not a sentence. Sentence-style messages drift between locales ;
  tokens are stable for clients to switch on :
  ```python
  raise HTTPException(status_code=404, detail="user-not-found")
  ```
- For richer error payloads (multiple field errors, error code +
  trace ID), define a `Problem` response model and a custom exception
  handler in `main.py` :
  ```python
  @app.exception_handler(BusinessError)
  async def _business_handler(req, exc):
      return JSONResponse(status_code=exc.status, content=Problem(...).model_dump())
  ```
- **Never leak internal exceptions.** A 500 should render the
  `Problem` shape, not the Python traceback.

## Dependencies

- **Shared deps** (DB session, current user, settings) live in
  `src/{{root_package}}/deps.py`.
- **Use `Annotated` for reusable dependency types** :
  ```python
  DbDep = Annotated[AsyncSession, Depends(get_db)]
  AuthDep = Annotated[User, Depends(require_auth)]
  ```
  Then endpoints just say `db: DbDep, current: AuthDep` — no repeat
  of `Depends(...)` boilerplate.
- **`yield`-style dependencies for resources** (DB session, file
  handles) so cleanup is guaranteed.

## App composition (`main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from {{root_package}}.routers import users, projects

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await db.connect()
    yield
    # shutdown
    await db.disconnect()

app = FastAPI(
    title="{{root_package}}",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url=None,           # disable redoc, keep swagger only
)

app.include_router(users.router)
app.include_router(projects.router)
```

- **`lifespan` not `@app.on_event(...)`.** The latter is deprecated
  since FastAPI 0.93.
- **`docs_url`** : keep `/docs` (Swagger UI). Remove redoc to avoid
  shipping two interfaces.

## What you do NOT do

- **No business logic in the endpoint function.** The endpoint
  validates input + dispatches to a service function under
  `src/{{root_package}}/services/`. Endpoints stay ≤ 20 lines.
- **No raw SQL in endpoints.** Always through the ORM / repository
  layer.
- **No global state mutated at request time** (counters, caches).
  Use dependencies for per-request state, `app.state` for app-scope
  immutable state (e.g. a precompiled regex).
- **No print().** Use `logging` (the std lib logger or `structlog`).
