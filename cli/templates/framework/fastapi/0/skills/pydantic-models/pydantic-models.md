# Skill — Pydantic v2 schemas for FastAPI

Patterns for Pydantic v2 models used as FastAPI input / output
schemas + application settings. Auto-loaded when defining or
reviewing schemas.

## Layout

- **Schemas per resource**, in
  `src/{{root_package}}/schemas/<resource>.py`.
- Three flavours per resource :
  - `*Base` — shared fields (used as a base for both Input + Output).
  - `*Create` / `*Update` — Input shapes (what the client sends).
  - `*Out` — Output shape (what the API returns).
- **Never reuse the same model for input + output.** Even when they
  look identical, separate them — they will diverge.

```python
class UserBase(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)

class UserCreate(UserBase):
    password: SecretStr           # never on Out

class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=80)

class UserOut(UserBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)   # for ORM objects → schema
```

## `ConfigDict`

Set `model_config = ConfigDict(...)` (Pydantic v2 syntax — not
`class Config:`). Common settings :

```python
model_config = ConfigDict(
    from_attributes=True,        # accept ORM instances + .attr access
    str_strip_whitespace=True,   # trim every str input
    populate_by_name=True,       # allow both field name + alias on input
    extra="forbid",              # reject unknown keys (default for Inputs)
    json_schema_extra={
        "example": {
            "email": "alice@example.com",
            "display_name": "Alice",
        },
    },
)
```

- **`extra="forbid"`** on Inputs — catches client typos early
  (`{"emial": ...}` → 422 instead of being silently ignored).
- **`extra="ignore"`** on Outs — defensive against the ORM
  exposing fields you didn't whitelist.

## Field validators

- **Built-in constraints first.** `Field(min_length=..., gt=...,
  pattern=r"...")` handles 80 % of cases declaratively.
- **`@field_validator` for cross-cutting logic** :
  ```python
  @field_validator("email")
  @classmethod
  def _normalise_email(cls, v: str) -> str:
      return v.strip().lower()
  ```
- **`@model_validator(mode="after")` for cross-field checks** :
  ```python
  @model_validator(mode="after")
  def _check_dates(self) -> Self:
      if self.start > self.end:
          raise ValueError("start-after-end")
      return self
  ```
- **Raise `ValueError` with a kebab-case token** — FastAPI surfaces
  it in the 422 response so clients can switch on it stably.

## Types worth knowing

| Use case                             | Pick                                            |
|--------------------------------------|-------------------------------------------------|
| Email                                | `pydantic.EmailStr`                             |
| URL                                  | `pydantic.HttpUrl` / `AnyHttpUrl`                |
| UUID                                 | `uuid.UUID`                                     |
| ISO timestamp                        | `datetime` (Pydantic parses ISO-8601)            |
| Money / decimals                     | `decimal.Decimal` + `Field(max_digits=, decimal_places=)` |
| Secret (never logged)                | `pydantic.SecretStr`                            |
| Strictly enum value                  | `enum.StrEnum` (3.11+) or `Literal["a", "b"]`   |
| File upload                          | `fastapi.UploadFile`                            |

## Settings via `pydantic-settings`

```python
# src/{{root_package}}/config.py
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        extra="ignore",
    )
    database_url: str
    jwt_secret: SecretStr
    log_level: str = "INFO"

# usage : depend on a settings cache
from functools import lru_cache
@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
```

- **One settings class for the whole app.** No global config dict.
- **`env_prefix=`** so env vars are namespaced (`APP_DATABASE_URL`).
- **Inject via `Annotated[Settings, Depends(get_settings)]`** — never
  read `os.environ` directly outside `config.py`.

## Validation errors

FastAPI auto-renders Pydantic errors as 422 with a structured
payload :

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "email"],
      "msg": "Field required",
      "input": {...}
    }
  ]
}
```

For consumer-friendly errors, override the handler in `main.py` :

```python
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def _validation(req, exc):
    return JSONResponse(
        status_code=422,
        content={"errors": [{"field": ".".join(map(str, e["loc"])), "code": e["type"]} for e in exc.errors()]},
    )
```

## Anti-patterns

- **No `class Config:`.** Pydantic v2 uses `model_config`.
- **No `.dict()` / `.json()`.** They're deprecated. Use
  `.model_dump()` / `.model_dump_json()`.
- **No `parse_obj_as`.** Use `TypeAdapter(SomeType).validate_python(data)`.
- **Don't reuse ORM models as schemas.** Even with `from_attributes=True`,
  keep them separate so internal changes don't leak as API breaks.
- **Don't put business logic in validators.** Validators normalise +
  reject. Logic belongs in services.
