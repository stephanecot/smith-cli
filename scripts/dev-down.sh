#!/usr/bin/env bash
# Smith — local dev shutdown.
#
# Stops the processes started by scripts/dev-up.sh and (optionally) the
# infrastructure containers.
#
# Usage:
#   scripts/dev-down.sh                # stop backend + frontend, keep infra
#   scripts/dev-down.sh --all          # also stop docker compose
#   scripts/dev-down.sh --infra-only   # only stop docker compose
#   scripts/dev-down.sh --backend      # stop backend only
#   scripts/dev-down.sh --frontend     # stop frontend only

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${REPO_ROOT}/.logs"

STOP_BACKEND=1
STOP_FRONTEND=1
STOP_INFRA=0

for arg in "$@"; do
  case "${arg}" in
    --all)           STOP_INFRA=1 ;;
    --infra-only)    STOP_INFRA=1; STOP_BACKEND=0; STOP_FRONTEND=0 ;;
    --backend)       STOP_BACKEND=1; STOP_FRONTEND=0 ;;
    --frontend)      STOP_BACKEND=0; STOP_FRONTEND=1 ;;
    -h|--help)       sed -n '2,12p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "Unknown flag: ${arg}"; exit 2 ;;
  esac
done

say()  { printf '\033[1;36m[smith]\033[0m %s\n' "$*"; }

stop_pid_tree() {
  # $1 = label, $2 = pid file
  local label="$1" pid_file="$2"
  if [[ ! -f "${pid_file}" ]]; then
    say "${label} not running (no pid file)"
    return 0
  fi
  local pid; pid="$(cat "${pid_file}")"
  if [[ -z "${pid}" ]] || ! kill -0 "${pid}" 2>/dev/null; then
    say "${label} already stopped"
    rm -f "${pid_file}"
    return 0
  fi

  # Why: mvn / ng spawn child processes ; killing the group avoids orphans.
  say "Stopping ${label} (PID ${pid}) …"
  if pkill -TERM -P "${pid}" 2>/dev/null; then :; fi
  kill -TERM "${pid}" 2>/dev/null || true
  for _ in {1..15}; do
    kill -0 "${pid}" 2>/dev/null || break
    sleep 1
  done
  if kill -0 "${pid}" 2>/dev/null; then
    say "${label} did not stop cleanly — sending SIGKILL"
    pkill -KILL -P "${pid}" 2>/dev/null || true
    kill -KILL "${pid}" 2>/dev/null || true
  fi
  rm -f "${pid_file}"
}

(( STOP_BACKEND ))  && stop_pid_tree "backend"  "${LOG_DIR}/backend.pid"
(( STOP_FRONTEND )) && stop_pid_tree "frontend" "${LOG_DIR}/frontend.pid"

if (( STOP_INFRA )); then
  say "Stopping docker compose (Postgres + Redis) …"
  ( cd "${REPO_ROOT}/deploy/local" && docker compose down )
fi

say "Done."
