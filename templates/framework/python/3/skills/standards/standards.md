# Skill — Python {{framework_version}} coding standards

Conventions every contributor (human or AI) follows when writing or
reviewing Python code in this project. Auto-loaded on Python file
edits.

## Layout

- **`src/` layout.** Importable packages live under `src/{{root_package}}/`.
  Top-level scripts go in `scripts/` (not packaged). Tests live under
  `tests/` outside the import path.
- **One module = one concept.** Module names are snake_case, short,
  noun-based (`user.py`, not `user_utils.py`). Sub-packages for cohesive
  feature sets (`{{root_package}}/auth/`, `{{root_package}}/billing/`).
- **`__init__.py` is for the public API.** Re-export what callers
  outside the module should see ; keep everything else private (leading
  underscore).

## Naming

- `snake_case` for functions, methods, variables, modules, packages.
- `PascalCase` for classes + type aliases.
- `SCREAMING_SNAKE` for module-level constants.
- Leading underscore (`_internal`) for module-private symbols.
- No Hungarian prefixes (`str_name`, `b_flag`). The type system does
  that.
- Avoid abbreviations except the universally understood ones
  (`db`, `id`, `url`, `cfg`). Prefer `customer_id` over `c_id`.

## Imports

Three groups, separated by blank lines, in this order :

1. Standard library (`os`, `pathlib`, `typing`).
2. Third-party (`fastapi`, `pydantic`, `sqlalchemy`).
3. First-party (`{{root_package}}.x`, `{{root_package}}.y`).

Within each group, sort alphabetically. **Absolute imports only** —
no `from . import foo`. Use `from {{root_package}}.auth import jwt`
instead.

Star imports (`from x import *`) are banned outside `__init__.py`
re-exports.

## Functions + classes

- **Single responsibility.** A function does one thing ; if you need
  `and` in the docstring summary, split.
- **Pure where possible.** Prefer functions that take their inputs as
  arguments and return values, no module-level state.
- **Type-hint every public callable.** See the `typing` skill for the
  full rules.
- **Docstrings on public symbols.** Google-style, single triple-quote
  block. Skip docstrings on private helpers if the name + signature
  is self-evident.
- **Dataclasses for data containers.** `@dataclass(frozen=True,
  slots=True)` when the type carries no behaviour. Use Pydantic only
  for validation at boundaries (API input, config loading) — never
  for purely internal types.
- **Composition over inheritance.** Inherit only when you need
  polymorphism or framework hooks (e.g. `pydantic.BaseModel`). Otherwise
  hold a reference + delegate.

## Error handling

- **Raise specific exceptions.** Define module-level
  `class FooNotFound(LookupError):` and raise that — never bare
  `Exception` or `RuntimeError`.
- **No catch-all.** `except Exception:` is allowed only at the
  outermost boundary (CLI entry, ASGI middleware) to convert into a
  user-facing error. Inside the codebase, catch only what you handle.
- **No silent except.** Every `except` block either re-raises, logs,
  or returns a sentinel — never `pass`.
- **EAFP > LBYL** for Pythonic flow : `try: x[k]` + `except KeyError`
  beats `if k in x: x[k]`. Exception : when the check is cheap and
  the failure is expected (validation gates).
- **Use `match` for typed enum-style dispatch** (Python 3.10+) over
  long `if isinstance` chains.

## Formatting + line length

- 100 columns max (matches `ruff` default + leaves room for diffs).
- 4-space indent, no tabs.
- One statement per line ; no inline `if x: do()`.
- Trailing commas in multi-line lists / dicts / call sites — keeps
  diffs minimal.

`ruff format` is the canonical formatter — see the `linting` skill.

## When in doubt

Open the closest existing module that already does what you need.
Match its conventions over inventing new ones — consistency in
patterns matters more than a marginally cleaner local style.
