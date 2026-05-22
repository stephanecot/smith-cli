# Template — Django 5

Skill templates for **Django 5.x** projects. These build on top of
`framework/python/3` (language-level conventions) and codify
Django-specific patterns the AI follows when writing models, views,
tests, and DRF endpoints.

## What ships here

| Skill                 | Purpose                                                          |
|-----------------------|------------------------------------------------------------------|
| `standards`           | Project + app structure, settings split, URL routing patterns.    |
| `orm-patterns`        | Querysets, select_related, transactions, signals, migrations.     |
| `tests-pytest-django` | pytest-django config + database fixtures + parametrise patterns.  |
| `rest-framework`      | DRF serializers, viewsets, permissions, pagination, throttling.   |

## Stack targeted

- Django 5.x (5.0+).
- Python 3.12+ (modern features : `Annotated`, PEP 695 generics).
- PostgreSQL as the default DB (other DBs work but most idioms shown
  here favour PG features).
- Optional : Django REST Framework, django-filter, django-cors-headers.

## Pairs with

- `framework/python/3` for Python language standards.
