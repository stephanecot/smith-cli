---
name: smith-python-typing
description: Strict type hints + static checker config for Python {{framework_version}} — annotation style, Protocol vs ABC, generics, runtime type guards, mypy / pyright settings. Apply when writing types or reviewing type hints.
---

# Skill — Python typing conventions

Strict static typing for Python {{framework_version}}. Auto-loaded when
adding type hints or reviewing typed code.

## The rule

**Every public callable carries full type hints** (parameters + return).
Private helpers (`_leading_underscore`) may skip hints when the
inference from the caller is obvious — but err on the side of
annotating.

Modules that ship to consumers (libraries, public APIs) annotate
**100 %** — including helpers — because their hints flow into the
user's static checker.

## Style

- **Python 3.12+ syntax.** `list[int]`, `dict[str, X]`, `tuple[A, B]`
  — never `List`, `Dict`, `Tuple` from `typing`.
- **`X | None` over `Optional[X]`.** Same for `X | Y` over
  `Union[X, Y]`.
- **`type[X]` for "the class itself"**, not `Type[X]`.
- Built-in `Self` (3.11+) for fluent return types : `def chain(self) -> Self: ...`
- **`TYPE_CHECKING` guard for forward refs.** Imports that exist only
  for hints :
  ```python
  from typing import TYPE_CHECKING
  if TYPE_CHECKING:
      from {{root_package}}.heavy_module import HeavyClass
  ```

## When to use what

| Use case                                    | Pick                                    |
|---------------------------------------------|-----------------------------------------|
| Sequence of homogeneous items, read-only    | `Sequence[X]` / `Iterable[X]`           |
| Mapping read-only                           | `Mapping[K, V]`                         |
| Concrete owner-mutated container            | `list[X]`, `dict[K, V]`                 |
| Static duck typing (structural)             | `Protocol`                              |
| Closed enum of known values                 | `Literal["a", "b"]` or `enum.Enum`      |
| Type-safe sentinel "missing" vs `None`      | `Missing = NewType("Missing", object)`  |
| Generic class                               | `class Cache[T]: ...` (PEP 695, 3.12+)  |
| Generic function                            | `def head[T](xs: list[T]) -> T: ...`    |

## Protocols vs ABCs

- **Protocols** (structural) for inputs the caller controls — "any
  object that has a `.read() -> bytes`". No `isinstance` cost, no
  forced inheritance.
- **ABCs** (nominal) only when you need `isinstance` checks at runtime
  or to share method implementations.

## Runtime guards

- `typing.cast(X, value)` for "trust me" coercions — leaves no
  runtime cost. Use sparingly ; prefer narrowing via `isinstance` or
  `is None` checks.
- **Use `assert isinstance(...)` to narrow** when the static checker
  can't follow. The assertion both narrows the type AND fails fast at
  runtime if the invariant breaks.
- For Pydantic / dataclass validation, prefer `model.field_name`
  access over `cast` — Pydantic already proved the type.

## NewType for opaque IDs

- `UserId = NewType("UserId", int)` — same runtime cost as `int` but
  the checker rejects passing a `UserId` where a `ProjectId` is
  expected.
- Use everywhere primitive obsession would otherwise creep in.

## Configuration

`pyproject.toml` :

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unused_configs = true
disallow_any_unimported = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_return_any = true
no_implicit_reexport = true
show_error_codes = true

[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false   # tests may skip return annotations
```

For pyright instead :

```toml
[tool.pyright]
include = ["src"]
pythonVersion = "3.12"
typeCheckingMode = "strict"
reportMissingImports = "error"
reportUnnecessaryTypeIgnoreComment = "warning"
```

## Anti-patterns

- **No `Any` outside boundary code** (parsing untyped JSON, calling
  legacy untyped libs). When you must use `Any`, narrow with
  `isinstance` at the first opportunity.
- **No `# type: ignore` without a code.** Always `# type: ignore[arg-type]`
  with the specific error code, never bare.
- **No "stringly-typed" interfaces.** A status returned as
  `Literal["ok", "fail"]` is fine ; as a bare `str` is not.
- **Don't annotate `self` / `cls`.** The checker infers them.
- **Don't over-genericise.** A function that's only called with `str`
  doesn't need `def foo[T](x: T) -> T:`.
