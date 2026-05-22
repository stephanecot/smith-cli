---
name: smith-django-standards
description: Django {{framework_version}} project layout + conventions — project / app split, settings management, URL routing, view types, template paths. Apply when adding apps, views, or restructuring routes.
---

# Skill — Django {{framework_version}} standards

Conventions for project / app structure, settings, URL routing, and
view organisation. Auto-loaded on Django file edits.

## Project layout

```
{{root_package}}/                        # repo root
├── manage.py
├── pyproject.toml
├── src/
│   ├── config/                  # the Django "project" (settings, root urls, wsgi/asgi)
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   ├── prod.py
│   │   │   └── test.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── apps/                    # all installed Django apps under one folder
│       ├── users/
│       ├── billing/
│       └── ...
└── tests/                       # repo-level tests (per-app tests inside the app)
```

- **Project package = `config`** (or any neutral name). Never name
  the project after the company / product — it'll outlive both.
- **All apps under `src/apps/`**, never at the repo root. Cleaner
  imports + clearer "app vs library" distinction.
- **`src/` layout** : like every Python project, importables live
  under `src/` so tests import the installed package.

## App layout

```
src/apps/users/
├── __init__.py
├── apps.py
├── models.py          # or models/ package if > 5 models
├── admin.py
├── urls.py            # app-local URL include
├── views.py           # or views/ package
├── serializers.py     # if DRF in use
├── services.py        # business logic, not in views or models
├── migrations/
└── tests/
    ├── __init__.py
    ├── test_models.py
    ├── test_views.py
    └── conftest.py
```

- **One app = one bounded context.** Don't create a `core` app that
  becomes a catch-all. Split by domain.
- **`services.py` for business logic.** Views handle HTTP /
  serialisation ; models handle persistence ; services handle the
  in-between (orchestration, transactions, side effects). Keeps views
  short + testable.

## Settings split

`src/config/settings/base.py` holds everything not env-specific.
`dev.py`, `prod.py`, `test.py` import `* from .base` and override.

```python
# base.py
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    # ...
    "apps.users",
    "apps.billing",
]

# prod.py
from .base import *  # noqa: F401, F403

DEBUG = False
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
DATABASES = {"default": env.db("DATABASE_URL")}
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
```

- **Env via `django-environ`** or `pydantic-settings`. Never hardcode
  secrets or env-specific values.
- **Pick a setting at startup** via `DJANGO_SETTINGS_MODULE=config.settings.dev`
  (env var, never in code).
- **`test.py` mirrors prod** for DB + cache, but uses a fast hashing
  scheme (`PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]`)
  to speed up the suite.

## URL routing

```python
# src/config/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.api_v1_urls")),     # or per-app includes
]

# src/apps/users/urls.py
from django.urls import path
from . import views

app_name = "users"
urlpatterns = [
    path("",          views.UserListView.as_view(),   name="list"),
    path("<uuid:id>/", views.UserDetailView.as_view(), name="detail"),
]
```

- **Always set `app_name`** on app-local `urls.py` so reverse
  resolves are namespaced (`reverse("users:detail", id=...)`).
- **kebab-case in URLs**, snake_case in view names. Django URL paths
  end with `/` — keep that consistent.
- **`<uuid:id>` / `<int:pk>` converters** instead of regex. More
  readable + type-checked.

## Views

Two flavours :
- **Class-Based Views (CBV)** for CRUD-shaped endpoints — inherit
  from generic views (`ListView`, `DetailView`, `CreateView`).
- **Function-Based Views (FBV)** for one-shot, non-CRUD operations
  (e.g. `webhook_handler`, `download_report`).

For REST APIs, use DRF viewsets — see the `rest-framework` skill.

```python
class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    pk_url_kwarg = "id"
    template_name = "users/detail.html"
    context_object_name = "user"
```

- **`LoginRequiredMixin`** / `PermissionRequiredMixin` for auth in
  CBVs. Use `@login_required` / `@permission_required` decorators for
  FBVs.
- **Don't put business logic in the view.** Delegate to `services.py`.
  Views are HTTP adapters.

## Migrations

- **One migration per change**, descriptive name :
  `0042_add_user_locked_at.py`. The `--name` flag controls this.
- **Never edit a migration that has shipped.** Make a new one.
- **Squash migrations periodically** (`manage.py squashmigrations`) on
  apps with > 50 migrations.
- **Migrations are code.** They get reviewed, tested, and rolled back
  like any other code.

## Imports

Three groups :
1. Stdlib.
2. Third-party (`django`, `rest_framework`).
3. First-party (`config.*`, `apps.*`).

`from django.contrib.auth.models import User` — but if you have a
custom user model (and you should), import from
`apps.users.models import User`.

## Anti-patterns

- **No business logic in `models.py`.** A model has fields + simple
  derived properties. Multi-step operations go in `services.py`.
- **No fat views.** A view is HTTP-in / HTTP-out + delegate.
- **No `INSTALLED_APPS` modifications in app modules.** Settings stay
  in `config/settings/`.
- **No raw HTML in views.** Use templates ; if returning JSON, use DRF
  serializers.
- **No `request.user` in services.** Services take `user: User`
  explicitly — that's how you keep them testable + reusable across
  request / non-request contexts (management commands, Celery tasks).
