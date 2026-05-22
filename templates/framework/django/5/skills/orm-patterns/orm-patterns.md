# Skill — Django ORM patterns

ORM idioms for Django {{framework_version}}. Auto-loaded when writing
models or queries.

## Model conventions

```python
import uuid
from django.db import models

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user"            # explicit table name ; no plural / app prefix
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.email
```

- **UUID primary keys by default.** No incrementing integers in
  customer-facing IDs — they leak business volume + are easy to
  guess. Use `BigAutoField` only when you genuinely need an ordered
  sequence (e.g. an append-only event log).
- **`db_table = "user"`** (singular, snake_case). Django's default
  plural `users_user` is opinionated noise — set it explicitly.
- **`created_at` + `updated_at` on every model** that's not a pure
  junction table. Use `auto_now_add=True` for created, `auto_now=True`
  for updated.
- **`Meta.ordering` deliberately.** Default ordering affects every
  unqualified `.objects.all()` — pick the one users expect (usually
  newest-first).
- **`Meta.indexes` for every column you filter on.** Don't rely on
  `db_index=True` per-field — `Meta.indexes` is more visible at
  review time.

## Querysets

- **`select_related` for FK / OneToOne** (single JOIN) :
  ```python
  User.objects.select_related("profile").get(id=user_id)
  ```
- **`prefetch_related` for reverse / M2M** (extra query + Python-side
  join) :
  ```python
  User.objects.prefetch_related("projects", "projects__members")
  ```
- **`only(...)` / `defer(...)` only when you've profiled.** They make
  queries faster only when columns are heavy AND unused — otherwise
  they hurt (extra round-trip when a deferred column is accessed).
- **`.values()` / `.values_list("col", flat=True)`** when you need
  a dict / scalar — bypasses ORM instantiation overhead.

## N+1 prevention

The single biggest perf issue. Every list view that touches related
data needs `select_related` / `prefetch_related` :

```python
# BAD : one query per user.profile access
for u in User.objects.all():
    print(u.profile.bio)            # N+1 !

# GOOD :
for u in User.objects.select_related("profile").all():
    print(u.profile.bio)            # one JOIN, one query
```

Use `django-debug-toolbar` in dev to spot N+1 patterns. CI can run a
lightweight check via `django.db.connection.queries`.

## Transactions

```python
from django.db import transaction

@transaction.atomic
def create_user_with_project(payload: ...) -> User:
    user = User.objects.create(...)
    Project.objects.create(owner=user, ...)
    return user
```

- **`@transaction.atomic` on service functions** that touch ≥ 2 rows
  in different tables. Never on the view — keep the transaction
  scope tight.
- **Don't `select_for_update()` without a `transaction.atomic` block** —
  outside a transaction it's a no-op.
- **`atomic` is reentrant** : nested calls use savepoints. Safe to
  compose service functions.

## Model managers

For non-trivial queries that repeat, define a manager :

```python
class ActiveUserManager(models.Manager):
    def get_queryset(self) -> models.QuerySet:
        return super().get_queryset().filter(is_active=True)

class User(models.Model):
    ...
    objects = models.Manager()           # default
    active  = ActiveUserManager()        # User.active.all() → only active users
```

- **`objects` stays the default unfiltered manager.** Don't override
  it — admin + tests rely on it.
- **Custom managers for cross-cutting filters.** Each gets a clear
  domain name (`active`, `with_unpaid_invoices`).

## Signals — use sparingly

- **Prefer overriding `save()` or service functions** over `pre_save`
  / `post_save` signals. Signals are spooky-at-a-distance — hard to
  trace, easy to break in tests.
- **Acceptable signal uses** : cross-app reactive behaviour where the
  consumer doesn't want to import the producer (e.g. an audit log
  app listening to all `post_save`).
- **Connect signals in `apps.py::ready()`**, never at module import
  time.

## Migrations

- **Always include a forward + reverse path** for data migrations
  (`RunPython(forward, reverse)`).
- **Backfill data in a separate migration** from schema changes. Two
  migrations : (1) add nullable column, (2) backfill + make non-null.
  Single migration = downtime + risky rollback.
- **`indexes` on large tables** : use `AddIndexConcurrently` (PG) to
  avoid lock-blocking writes :
  ```python
  from django.contrib.postgres.operations import AddIndexConcurrently
  ```
- **`null=True` is permanent debt.** Pick a default if at all
  possible.

## Index choices

| Column kind                        | Index                                       |
|------------------------------------|---------------------------------------------|
| Foreign key                        | Automatic ; don't add a second.             |
| Unique constraint                  | `unique=True` (creates the index).          |
| Date-range filters (created_at)    | `models.Index(fields=["created_at"])`.      |
| Multi-column equality              | `models.Index(fields=["a", "b"])` — order matters ! |
| Case-insensitive lookup (`iexact`) | Functional index (PG) :   `models.Index(Lower("email"), name="user_email_lower_idx")` |
| Full-text search (PG)              | `GinIndex(SearchVector(...))` from `django.contrib.postgres`. |

## Anti-patterns

- **No `for x in queryset.all()` followed by `.save()`.** Use
  `update()` for bulk changes, or `bulk_update` for per-row
  changes. The naive loop is N round-trips.
- **No `.count() > 0`.** Use `.exists()` — single 1-row query.
- **No `len(queryset)` to check emptiness.** Same — `.exists()`.
- **No `Model.objects.get(...)` without try/except** unless you've
  proven the row exists. Use `.first()` or `get_object_or_404` in
  views.
- **Don't ignore the `Meta.app_label`** when the app sits in a
  non-default location — Django will fail to import otherwise.
