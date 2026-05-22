# Skill — Linting + formatting with ruff

`ruff` is the unified tool for this project — formatter + linter +
import sorter + pyupgrade, all in one. Replaces `black` + `isort` +
`flake8` + `pyupgrade`.

## Why ruff

- **One tool, one config block** in `pyproject.toml`. No more
  juggling four sets of plugins.
- **Fast.** Rust-based ; orders of magnitude faster than the pure-
  Python alternatives. Whole repo lint in seconds, not minutes.
- **Drop-in compatible** with black's output (same formatter
  semantics) + isort (same import sorting).

## Configuration

`pyproject.toml` :

```toml
[tool.ruff]
line-length = 100
target-version = "py312"
src = ["src", "tests"]
extend-exclude = ["docs/_build", "build", "dist"]

[tool.ruff.lint]
# Rule families to enable :
# E + W       : pycodestyle (PEP 8)
# F           : pyflakes (unused imports, undefined names)
# I           : isort (import order)
# B           : bugbear (likely bug patterns)
# UP          : pyupgrade (modernise to py3.12+ syntax)
# SIM         : simplify (e.g. `if x: return True else: return False`)
# C4          : comprehensions
# RUF         : ruff-specific rules
# N           : pep8-naming
# D           : pydocstyle (docstrings) — opt-in per project
# ANN         : flake8-annotations — opt-in when full annotations required
select = ["E", "W", "F", "I", "B", "UP", "SIM", "C4", "RUF", "N"]
ignore = [
  "E501",  # line too long — black/ruff format handles wrapping
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["B", "N"]      # tests may use bare names + skip a few bugbear rules
"__init__.py"   = ["F401"]        # unused imports OK (re-exports)

[tool.ruff.lint.isort]
known-first-party = ["{{root_package}}"]
section-order = ["future", "standard-library", "third-party", "first-party", "local-folder"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true       # also format code blocks INSIDE docstrings
```

## Commands

```bash
# Lint (read-only) — fails non-zero on findings.
uv run ruff check src tests

# Lint + autofix the safe ones :
uv run ruff check --fix src tests

# Format every file in place :
uv run ruff format src tests

# Combined "format then lint with fixes" — typical pre-commit chain :
uv run ruff format src tests && uv run ruff check --fix src tests
```

## Pre-commit

`.pre-commit-config.yaml` :

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.5.0    # bump when ruff releases
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

Install once : `uv run pre-commit install`. Every commit then runs
`ruff format` + `ruff check --fix` and re-stages.

## CI gate

CI runs the same chain but without `--fix` — it must be a no-op on a
correct PR :

```bash
uv run ruff format --check src tests   # exits non-zero if any file would be reformatted
uv run ruff check src tests             # exits non-zero on any unfixed finding
```

`ruff format --check` is the formatter's "would-have-changed" mode.
If it fails, the dev forgot to run pre-commit ; fix and re-push.

## Disabling rules locally

- Per-line : `do_thing()  # noqa: SIM102` (always include the code,
  never a bare `# noqa`).
- Per-block : wrap in `# fmt: off` / `# fmt: on` (formatter only —
  doesn't disable linter).
- Per-file : add to `[tool.ruff.lint.per-file-ignores]`.

Use sparingly. A `noqa` is technical debt — leave a comment
explaining why the rule shouldn't apply.

## What ruff does NOT do

- **Type checking.** That's `mypy` or `pyright` — see the `typing`
  skill.
- **Security audit.** Use `bandit` or `pip-audit` separately.
- **Coverage.** That's `pytest-cov` — see the `tests-coverage`
  skill.

## When to add a new rule family

When the team agrees a class of bugs needs catching :
1. Open `ruff`'s docs (`ruff linter`), find the rule family code.
2. Add it to `select = [...]` in `pyproject.toml`.
3. Run `uv run ruff check src tests` to see how many findings the
   new family produces.
4. Either fix them all in the same PR (preferred) or add temporary
   `# noqa`s + a follow-up issue.
