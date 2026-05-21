---
name: smith-python-tests-coverage
description: pytest patterns for Python {{framework_version}} — fixture scoping, parametrize idioms, assertion style, coverage targets, pytest-cov config. Apply when writing tests or reviewing test coverage.
---

# Skill — pytest + coverage conventions

Test conventions for Python {{framework_version}} projects. Auto-loaded
on tests/ edits or when reviewing coverage.

## Layout

- Tests live under `tests/` at the repo root — outside `src/` so
  imports go through the installed package, not relative paths.
- Mirror the source tree : `src/{{root_package}}/auth/jwt.py` →
  `tests/auth/test_jwt.py`.
- One test module per source module. No "test_utils everything"
  catch-all.

## Naming

- File names start with `test_` (pytest discovery rule).
- Function names start with `test_` ; class names start with `Test`.
- Test names describe the **expected behaviour** in past tense, not
  the implementation : `test_jwt_decodes_valid_token` not
  `test_decode_function`.

## Fixtures

- **Scope deliberately.** Default to `scope="function"` ; widen only
  when the setup is genuinely expensive AND the fixture has no
  per-test mutable state. Database connections : `scope="session"`
  with a per-test transaction rollback fixture stacked on top.
- **`conftest.py` for cross-module fixtures.** Per-module fixtures
  stay in the test module.
- **Factory fixtures over generators of stateful objects.** Yield a
  callable that builds the object on demand : `def build_user(...): ...`
  → tests parametrise the factory instead of mutating a shared instance.
- **Use `tmp_path` + `monkeypatch`** built-ins instead of hand-rolling
  temp dirs or env-var save/restore.

## Parametrise

- `@pytest.mark.parametrize` for table-driven tests. One `id=` per
  row when the row values aren't self-documenting :
  ```python
  @pytest.mark.parametrize(
      "raw, expected",
      [
          ("",           ""),
          ("a b",        "a-b"),
          ("Café Olé",   "cafe-ole"),
      ],
      ids=["empty", "spaces", "accents"],
  )
  def test_slugify(raw, expected):
      assert slugify(raw) == expected
  ```
- Don't loop in a test ; one assertion per logical case. Loops hide
  which row failed.

## Assertions

- Plain `assert` — pytest rewrites them for rich diff output.
- `assert actual == expected` — actual first (mental model : "is the
  thing I tested giving me what I expect").
- For floats : `pytest.approx(expected, rel=1e-6)`.
- For exceptions : `with pytest.raises(FooError, match="snippet"):`.
  Always set `match=` so a different `FooError` doesn't accidentally
  pass.
- For warnings : `with pytest.warns(DeprecationWarning):`.

## Mocking

- **`unittest.mock` for stdlib, `pytest-mock`** (the `mocker` fixture)
  for cleaner syntax + auto-cleanup.
- Mock at the boundary — never mock your own module's internals.
  Mock the HTTP client, the DB driver, the clock — not the function
  under test.
- **Patch where used, not where defined** : `mocker.patch("{{root_package}}.auth.jwt.datetime")`,
  not `mocker.patch("datetime.datetime")`.

## Coverage

- Target : **80 % line + branch coverage** on `src/{{root_package}}/`.
  Higher for security-critical modules (auth, crypto) — aim for 95 %.
- Excluded from coverage by `# pragma: no cover` :
  - `if TYPE_CHECKING:` blocks.
  - `raise NotImplementedError` placeholders in abstract methods.
  - Defensive `else` branches that are truly unreachable.
- Use `pytest-cov` :
  ```toml
  [tool.coverage.run]
  branch = true
  source = ["src/{{root_package}}"]
  ```
- Run with `pytest --cov --cov-report=term-missing --cov-fail-under=80`.

## Markers

- `@pytest.mark.slow` for tests > 1s — gated by `-m "not slow"` by
  default in CI's fast lane.
- `@pytest.mark.integration` for tests that hit real infrastructure
  (a test container, the filesystem with real I/O patterns).
- Declare every marker in `pyproject.toml` to avoid pytest warning
  about unknown markers :
  ```toml
  [tool.pytest.ini_options]
  markers = [
    "slow: tests > 1s",
    "integration: hits real infra",
  ]
  ```

## Anti-patterns

- **Don't test private helpers.** Test the public function that uses
  them. If a private helper is so complex it needs its own test,
  promote it.
- **Don't share mutable state between tests.** Every test starts from
  a fresh fixture stack.
- **Don't `print()` for debugging in checked-in tests.** Use the
  `caplog` fixture for log assertions, `capsys` for captured stdout.
