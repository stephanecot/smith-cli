# Skill — JWT authentication for FastAPI

JWT-based auth flow for FastAPI services. Auto-loaded when wiring
auth, login endpoints, or role-based authorisation.

## Stack

- **`python-jose[cryptography]`** for JWT encode / decode.
- **`passlib[bcrypt]`** for password hashing.
- **OAuth2 Password Bearer flow** for `POST /auth/login` →
  `{access_token, token_type, refresh_token}`.
- **Algorithm : HS256** for symmetric setups, **RS256** when you need
  to verify in services that don't share the secret.

## Module layout

```
src/{{root_package}}/auth/
├── __init__.py
├── hashing.py          # password hash + verify
├── jwt.py              # encode + decode helpers
├── dependencies.py     # require_auth, require_role, current_user
└── router.py           # /auth/login, /auth/refresh
```

## Password hashing

```python
# auth/hashing.py
from passlib.context import CryptContext

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return _pwd.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)
```

- **bcrypt with cost 12+.** passlib picks a sensible default ;
  override only if benchmarks show login is the bottleneck.
- **Never store plain passwords.** Never log them either — use
  `SecretStr` in the input schema so they don't leak into stack
  traces or pydantic dumps.

## JWT helpers

```python
# auth/jwt.py
from datetime import datetime, timedelta, timezone
from uuid import UUID
from jose import jwt, JWTError
from pydantic import BaseModel

ACCESS_TTL  = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=14)

class TokenPayload(BaseModel):
    sub: UUID            # user id
    typ: str             # "access" | "refresh"
    exp: datetime
    iat: datetime

def encode(sub: UUID, typ: str, ttl: timedelta, secret: str) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {"sub": str(sub), "typ": typ, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, secret, algorithm="HS256")

def decode(token: str, secret: str) -> TokenPayload:
    raw = jwt.decode(token, secret, algorithms=["HS256"])
    return TokenPayload.model_validate(raw)
```

- **Always set `exp` + `iat`.** Tokens without `exp` are forever
  tokens — a security incident waiting.
- **Type the token kind (`typ`)** : refresh tokens must NOT be
  accepted on routes that expect access tokens. Check `payload.typ`
  in the dependency.
- **Short access TTL (5-15 min)** + **longer refresh TTL (7-14 days)**.

## Login + refresh endpoints

```python
# auth/router.py
from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated

router = APIRouter(prefix="/auth", tags=["auth"])

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=TokenOut)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbDep,
    settings: SettingsDep,
) -> TokenOut:
    user = await users_service.find_by_email(db, form.username)
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid-credentials")
    return TokenOut(
        access_token=encode(user.id, "access", ACCESS_TTL, settings.jwt_secret.get_secret_value()),
        refresh_token=encode(user.id, "refresh", REFRESH_TTL, settings.jwt_secret.get_secret_value()),
    )

@router.post("/refresh", response_model=TokenOut)
async def refresh(refresh_token: str, db: DbDep, settings: SettingsDep) -> TokenOut:
    try:
        payload = decode(refresh_token, settings.jwt_secret.get_secret_value())
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid-token") from e
    if payload.typ != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="wrong-token-type")
    # rotate : new access + new refresh
    return TokenOut(
        access_token=encode(payload.sub, "access", ACCESS_TTL, settings.jwt_secret.get_secret_value()),
        refresh_token=encode(payload.sub, "refresh", REFRESH_TTL, settings.jwt_secret.get_secret_value()),
    )
```

- **`OAuth2PasswordRequestForm`** parses the `application/x-www-form-urlencoded`
  body Swagger UI sends. Field names are `username` + `password`.
- **Refresh tokens rotate.** On `/auth/refresh`, issue a new refresh
  + invalidate the old one (with a `jti` blocklist if revocation
  matters — add a `denylist` Redis set keyed on `payload.jti`).
- **No "remember me" stored in the JWT.** Long sessions = longer
  refresh TTL, never longer access TTL.

## Auth dependency

```python
# auth/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

_bearer = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def require_auth(
    token: Annotated[str, Depends(_bearer)],
    db: DbDep,
    settings: SettingsDep,
) -> User:
    try:
        payload = decode(token, settings.jwt_secret.get_secret_value())
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="invalid-token") from e
    if payload.typ != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="wrong-token-type")
    user = await users_service.find_by_id(db, payload.sub)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="user-disabled")
    return user

AuthDep = Annotated[User, Depends(require_auth)]
```

Then endpoints use `current: AuthDep` to require a logged-in user.

## Role-based access

```python
def require_role(*roles: str):
    async def _dep(current: AuthDep) -> User:
        if current.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="role-missing")
        return current
    return _dep

AdminDep = Annotated[User, Depends(require_role("admin"))]
```

- **`401` for missing / invalid auth, `403` for "logged in but
  wrong rights".** Don't conflate them.

## Anti-patterns

- **No raw `Authorization` header parsing.** Use `OAuth2PasswordBearer`
  — it integrates with Swagger UI's "Authorize" button.
- **No JWT for session-style "logged in" flags.** JWTs are stateless ;
  if you need server-side revocation, use a Redis denylist keyed on
  the token's `jti`, or move to opaque session tokens.
- **No HS256 across services that don't share the secret.** Switch to
  RS256 (asymmetric) — gateway has the private key, services hold
  the public key.
- **No secrets in code.** `jwt_secret` lives in env vars, loaded via
  `pydantic-settings`.
- **Don't return the access token in a `Set-Cookie` unless** you
  understand CSRF. Bearer-in-Authorization-header is the default —
  cookies only when you must (browser app, no JS auth helper).
