# Skill — async patterns for FastAPI

How async/await flows through this codebase. Auto-loaded when
writing async services, DB sessions, or background work.

## The golden rule

**Don't block the event loop.** Every endpoint is `async def` ; every
function it calls must be `async def` OR cheap (CPU-only, no I/O, no
sleeps). Synchronous I/O inside an async endpoint stalls the entire
worker.

If you must call a blocking library (PIL, hashlib, cryptography),
push it off the loop :

```python
from anyio import to_thread

result = await to_thread.run_sync(blocking_fn, arg1, arg2)
```

## SQLAlchemy `ext.asyncio` setup

`src/{{root_package}}/db.py` :

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

engine = create_async_engine(
    settings.database_url,             # e.g. "postgresql+asyncpg://user:pwd@host/db"
    echo=False,                         # True only in dev
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,                 # ping connections before use
)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
```

`expire_on_commit=False` matters : after a commit you can still
serialise the ORM instance into a Pydantic Out model without a
re-fetch.

## Session-per-request dependency

```python
from collections.abc import AsyncIterator

async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- **One session per request.** Yield in a dependency ; FastAPI
  closes it on response return.
- **Commit on success, rollback on exception** — automatic via the
  `try` / `except` in the dependency. Service functions never call
  `commit()` themselves.
- **No nested sessions.** If a helper needs DB access, it takes
  `db: AsyncSession` as a parameter — never opens its own.

Usage in endpoints :

```python
DbDep = Annotated[AsyncSession, Depends(get_db)]

@router.post("", response_model=UserOut, status_code=201)
async def create_user(payload: UserCreate, db: DbDep) -> UserOut:
    user = await users_service.create(db, payload)
    return UserOut.model_validate(user)
```

## Queries

- **Use `select(...)` + `session.scalars(...)`** — not the legacy
  `session.query(...)` API.
- **`scalar_one_or_none()`** for "0 or 1" lookups. Never use
  `.first()` (silently masks duplicates).
- **`scalars().all()`** for collections — never `.fetchall()` on the
  raw result for ORM rows.

```python
stmt = select(User).where(User.email == email).options(selectinload(User.projects))
result = await db.execute(stmt)
user = result.scalar_one_or_none()
```

- **Eager-load relationships needed by the response** with
  `selectinload(...)` or `joinedload(...)`. Lazy-load on a closed
  session = `MissingGreenlet` error.

## Background tasks

For short, fire-and-forget work after returning the response :

```python
from fastapi import BackgroundTasks

@router.post("/welcome")
async def welcome(payload: SignUp, bg: BackgroundTasks, db: DbDep) -> dict:
    user = await users_service.create(db, payload)
    bg.add_task(send_welcome_email, user.email)
    return {"id": user.id}
```

- `BackgroundTasks` runs **after** the response is sent, on the same
  worker.
- Use only for ≤ 1s tasks (sending an email, queueing a follow-up).
- For longer work — image processing, batch ingest, anything > 5s —
  push to a real queue : Celery, RQ, or arq (async). The endpoint
  enqueues + returns immediately with a job id.

## Concurrency inside a request

Use `anyio.create_task_group()` when an endpoint genuinely needs to
fan-out concurrent I/O (e.g. fetch 3 APIs in parallel) :

```python
import anyio

async with anyio.create_task_group() as tg:
    tg.start_soon(fetch_a)
    tg.start_soon(fetch_b)
    tg.start_soon(fetch_c)
# all complete when the `async with` exits ; first error cancels the rest
```

- **Structured concurrency** : if one task fails, the group cancels
  the others — no leaked tasks.
- Never use bare `asyncio.create_task(...)` in an endpoint — the task
  outlives the request and can leak.

## HTTP client

- **`httpx.AsyncClient`** with a long-lived instance (created in
  `lifespan`, closed on shutdown). Don't spin up a client per request
  — connection pooling is the whole point.

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(10.0, connect=5.0))
    yield
    await app.state.http.aclose()
```

- **Always set a timeout.** A 30s default global timeout in production
  prevents a slow upstream from holding a worker hostage.

## Testing async code

- **`pytest-asyncio` with `asyncio_mode = "auto"`** in
  `pyproject.toml`. Every `async def test_...` runs in an event
  loop.
- **`httpx.AsyncClient` + `ASGITransport` for endpoint tests** :
  ```python
  from httpx import ASGITransport, AsyncClient

  async def test_create_user():
      transport = ASGITransport(app=app)
      async with AsyncClient(transport=transport, base_url="http://test") as client:
          resp = await client.post("/users", json={...})
      assert resp.status_code == 201
  ```
- **Per-test transaction rollback** for DB isolation (see
  `tests-coverage` skill for the fixture).

## Anti-patterns

- **No `time.sleep()` in async code.** Use `await asyncio.sleep(...)`.
- **No sync DB drivers** (`psycopg2`, `mysqlclient`). Use the
  async-native ones (`asyncpg`, `aiomysql`).
- **No `requests` library.** Use `httpx.AsyncClient`.
- **No mixing sync + async ORMs.** Choose `ext.asyncio` and stay
  there.
- **Don't `await` inside a sync function** — Python rejects this at
  parse time. The whole call chain must be `async def`.
