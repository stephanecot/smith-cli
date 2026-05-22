#!/usr/bin/env bash
# smoke_check.sh — fail fast if the freshly scaffolded FastAPI project
# can't sync deps or pass its starter tests.
set -euo pipefail

ROOT="${1:-$(pwd)}"
cd "$ROOT"

echo "==> uv sync --all-extras"
uv sync --all-extras

echo "==> uv run pytest -q"
uv run pytest -q

echo "OK — FastAPI scaffold smoke test passed."
