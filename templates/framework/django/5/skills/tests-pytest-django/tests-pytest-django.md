# Skill — pytest-django patterns

Test conventions for Django {{framework_version}} using
`pytest-django`. Auto-loaded when writing tests for Django code.

## Setup

`pyproject.toml` :

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "config.settings.test"
python_files          = ["test_*.py"]
testpaths             = ["src/apps", "tests"]
addopts = [
  "--reuse-db",          # don't drop / recreate the test DB every run
  "--strict-markers",
  "--strict-config",
]
markers = [
  "slow: tests > 1s",
  "integration: hits real infra",
]
```

- **`--reuse-db`** is a huge speedup on a multi-app project. Use
  `--create-db` once after schema changes to refresh.
- **`config.settings.test`** uses `sqlite` or a fast-hash PG with
  `PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]`
  to keep the suite quick.

## The `db` marker

Tests that touch the database need `@pytest.mark.django_db` :

```python
import pytest

@pytest.mark.django_db
def test_user_create():
    user = User.objects.create(email="a@example.com", display_name="Alice")
    assert User.objects.filter(email="a@example.com").exists()
```

- **`pytestmark = pytest.mark.django_db`** at the top of a module to
  apply to every test in the file — cleaner than decorating each.
- **`@pytest.mark.django_db(transaction=True)`** when the test
  exercises something that itself uses `transaction.atomic`. Default
  is a wrapped transaction that rolls back per-test.

## Built-in fixtures

| Fixture          | Use                                                          |
|------------------|--------------------------------------------------------------|
| `client`         | Anonymous `Client` (Django test client).                     |
| `admin_client`   | Authenticated as a superuser.                                |
| `admin_user`     | A pre-created superuser User instance.                       |
| `django_user_model` | The active `AUTH_USER_MODEL` class (custom-safe).         |
| `settings`       | Override settings per-test : `settings.DEBUG = True`.        |
| `mailoutbox`     | List of `EmailMessage` sent during the test.                 |
| `live_server`    | Real running server URL (Selenium / Playwright e2e).         |

Example :

```python
def test_login_endpoint(client, django_user_model):
    user = django_user_model.objects.create_user(email="a@x", password="pw")
    resp = client.post("/auth/login/", {"username": "a@x", "password": "pw"})
    assert resp.status_code == 302       # redirect after login
```

## Factory-boy for fixtures

Don't hand-craft `User.objects.create(...)` calls in every test.
Use `factory-boy` :

```python
# src/apps/users/tests/factories.py
import factory
from apps.users.models import User

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email        = factory.Sequence(lambda n: f"user-{n}@example.com")
    display_name = factory.Faker("name")
    is_active    = True
```

Usage :

```python
def test_user_list(client):
    UserFactory.create_batch(5)
    resp = client.get("/users/")
    assert len(resp.json()) == 5
```

- **`.create()`** writes to the DB. **`.build()`** returns an unsaved
  instance — useful for unit tests that don't need persistence.
- **`.create_batch(n)`** for collections.
- **Sub-factories** for related models : `owner = SubFactory(UserFactory)`.
- Define one factory per model, near the model — co-located in
  `src/apps/<app>/tests/factories.py`.

## Parametrise

Same as language-level `tests-coverage` skill — `@pytest.mark.parametrize`
with `ids=` for table-driven tests :

```python
@pytest.mark.django_db
@pytest.mark.parametrize(
    "role, can_edit",
    [("admin", True), ("member", False), ("guest", False)],
    ids=["admin-yes", "member-no", "guest-no"],
)
def test_edit_permission(role, can_edit):
    user = UserFactory(role=role)
    assert user.can_edit_project() is can_edit
```

## Override settings per-test

```python
def test_with_debug_on(settings):
    settings.DEBUG = True
    # test uses DEBUG=True ; revert is automatic at teardown
```

Or with the decorator :

```python
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_email():
    send_mail(...)
    assert len(mail.outbox) == 1
```

## Coverage

`pyproject.toml` adds the Django-specific bits :

```toml
[tool.coverage.run]
branch = true
source = ["src/apps", "src/config"]
omit = [
  "*/migrations/*",
  "*/tests/*",
  "*/admin.py",          # admin is hard to unit-test ; covered by e2e
  "src/config/asgi.py",
  "src/config/wsgi.py",
]
```

Target 80 % on `src/apps/`, 95 % on `src/apps/<critical>/services.py`.

## Performance

- **`--reuse-db`** + **`--no-migrations`** : skip running migrations
  on every CI start once the schema is stable. Combine with a
  schema-snapshot fixture for first-run setup.
- **`pytest -x`** stops at the first failure — useful during dev.
- **`pytest -k name_or_substring`** runs only matching tests.
- **`pytest --lf`** reruns the last failures only.

## Anti-patterns

- **No `unittest.TestCase` subclasses.** Use plain functions — they
  integrate with fixtures and parametrise cleanly.
- **No DB fixtures in module scope** unless `transaction=True` — your
  module-scope fixture data leaks across tests.
- **No `setUp` / `tearDown`** — fixtures + `yield` cover the same
  ground better.
- **Don't test the admin.** Cover business logic in services + views ;
  trust Django to render `ModelAdmin`.
- **Don't mock the ORM.** Mocking `QuerySet.filter` is brittle.
  Hit the test DB — that's what it's for.
