#!/usr/bin/env bash
# smoke_check.sh — fail fast if the freshly scaffolded library can't
# sync deps or pass its trivial import test.
set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

echo "==> uv sync --all-extras"
uv sync --all-extras

echo "==> uv run pytest -q"
uv run pytest -q

echo "OK — Python library scaffold smoke test passed."
