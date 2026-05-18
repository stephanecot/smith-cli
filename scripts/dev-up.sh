#!/usr/bin/env bash
# Smith — local dev orchestrator.
#
# Brings the full local stack up:
#   1. Infra:    Postgres 17 + Redis 7 via deploy/local/docker-compose.yml
#   2. Backend:  Spring Boot (smith-api) via Maven Spring Boot plugin on :8080
#   3. Frontend: Angular dev server (ng serve) on :4200
#
# Usage:
#   scripts/dev-up.sh                 # everything (infra + backend + frontend)
#   scripts/dev-up.sh --no-infra      # skip docker compose (assumes Postgres/Redis already up)
#   scripts/dev-up.sh --backend-only  # infra + backend only
#   scripts/dev-up.sh --frontend-only # frontend only (assumes backend already up)
#   scripts/dev-up.sh --skip-build    # skip the initial mvn install of dependent modules
#
# Stop everything: scripts/dev-down.sh
#
# Logs land in <repo>/.logs/{backend,frontend}.log ; PIDs in <repo>/.logs/{backend,frontend}.pid

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${REPO_ROOT}/.logs"
mkdir -p "${LOG_DIR}"

# Defaults
START_INFRA=1
START_BACKEND=1
START_FRONTEND=1
SKIP_BUILD=0

for arg in "$@"; do
  case "${arg}" in
    --no-infra)       START_INFRA=0 ;;
    --backend-only)   START_INFRA=1; START_BACKEND=1; START_FRONTEND=0 ;;
    --frontend-only)  START_INFRA=0; START_BACKEND=0; START_FRONTEND=1 ;;
    --skip-build)     SKIP_BUILD=1 ;;
    -h|--help)        sed -n '2,18p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "Unknown flag: ${arg}"; exit 2 ;;
  esac
done

# ─── helpers ───────────────────────────────────────────────────────────────────
say()  { printf '\033[1;36m[smith]\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m[smith]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[smith]\033[0m %s\n' "$*" >&2; exit 1; }

require() {
  command -v "$1" >/dev/null 2>&1 || die "Missing dependency: $1 (install it and retry)"
}

is_pid_alive() {
  local pid_file="$1"
  [[ -f "${pid_file}" ]] || return 1
  local pid; pid="$(cat "${pid_file}")"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

free_port() {
  # $1 = port, $2 = label — kills whoever is bound to the port (TERM, then KILL).
  local port="$1" label="$2"
  local pids
  pids="$(lsof -ti ":${port}" 2>/dev/null || true)"
  [[ -z "${pids}" ]] && return 0

  warn "Port ${port} (${label}) busy — killing PIDs ${pids//$'\n'/ }"
  # shellcheck disable=SC2086
  kill -TERM ${pids} 2>/dev/null || true
  for _ in {1..10}; do
    pids="$(lsof -ti ":${port}" 2>/dev/null || true)"
    [[ -z "${pids}" ]] && break
    sleep 1
  done
  if [[ -n "${pids}" ]]; then
    warn "Port ${port} still held — sending SIGKILL"
    # shellcheck disable=SC2086
    kill -KILL ${pids} 2>/dev/null || true
    sleep 1
  fi
}

wait_http_200() {
  # $1 = url, $2 = label, $3 = max_seconds (default 90)
  local url="$1" label="$2" max="${3:-90}"
  local start; start="$(date +%s)"
  while :; do
    if curl -fsS -m 2 "${url}" >/dev/null 2>&1; then
      say "${label} ready (${url})"
      return 0
    fi
    local now; now="$(date +%s)"
    if (( now - start > max )); then
      warn "${label} did not respond within ${max}s — check ${LOG_DIR}/${label}.log"
      return 1
    fi
    sleep 1
  done
}

# ─── 1. Infra (Postgres + Redis) ──────────────────────────────────────────────
if (( START_INFRA )); then
  require docker
  say "Starting Postgres + Redis (docker compose) …"
  pushd "${REPO_ROOT}/deploy/local" >/dev/null
  docker compose up -d
  popd >/dev/null
  say "Waiting for Postgres health …"
  for _ in {1..30}; do
    if docker inspect --format='{{.State.Health.Status}}' smith-postgres 2>/dev/null | grep -q healthy; then
      break
    fi
    sleep 1
  done
fi

# ─── 2. Backend (smith-api) ───────────────────────────────────────────────────
if (( START_BACKEND )); then
  require mvn

  # Why: a stale spring-boot:run from a previous session would re-bind 8080.
  if is_pid_alive "${LOG_DIR}/backend.pid"; then
    say "Stopping previous backend (PID $(cat "${LOG_DIR}/backend.pid")) …"
    pkill -TERM -P "$(cat "${LOG_DIR}/backend.pid")" 2>/dev/null || true
    kill -TERM "$(cat "${LOG_DIR}/backend.pid")" 2>/dev/null || true
    sleep 2
    rm -f "${LOG_DIR}/backend.pid"
  fi
  free_port 8080 backend

  if (( ! SKIP_BUILD )); then
    say "Building backend modules (mvn -DskipTests install) …"
    ( cd "${REPO_ROOT}/backend" && mvn -B -DskipTests -pl smith-api -am install -q )
  fi

  say "Starting smith-api on :8080 (logs: ${LOG_DIR}/backend.log)"
  (
    cd "${REPO_ROOT}/backend/smith-api"
    nohup mvn -B spring-boot:run >"${LOG_DIR}/backend.log" 2>&1 &
    echo $! >"${LOG_DIR}/backend.pid"
  )

  wait_http_200 "http://localhost:8080/actuator/health" "backend" 120 || true
fi

# ─── 3. Frontend (Angular) ────────────────────────────────────────────────────
if (( START_FRONTEND )); then
  require npm

  # Why: a stale ng serve from a previous session would re-bind 4200 and the
  # script would silently report "ready" while serving the old bundle.
  if is_pid_alive "${LOG_DIR}/frontend.pid"; then
    say "Stopping previous frontend (PID $(cat "${LOG_DIR}/frontend.pid")) …"
    pkill -TERM -P "$(cat "${LOG_DIR}/frontend.pid")" 2>/dev/null || true
    kill -TERM "$(cat "${LOG_DIR}/frontend.pid")" 2>/dev/null || true
    sleep 2
    rm -f "${LOG_DIR}/frontend.pid"
  fi
  free_port 4200 frontend

  if [[ ! -d "${REPO_ROOT}/frontend/node_modules" ]]; then
    say "Installing frontend dependencies (npm ci) …"
    ( cd "${REPO_ROOT}/frontend" && npm ci )
  fi

  say "Starting Angular dev server on :4200 (logs: ${LOG_DIR}/frontend.log)"
  (
    cd "${REPO_ROOT}/frontend"
    nohup npm start -- --host 0.0.0.0 --port 4200 >"${LOG_DIR}/frontend.log" 2>&1 &
    echo $! >"${LOG_DIR}/frontend.pid"
  )

  wait_http_200 "http://localhost:4200" "frontend" 120 || true
fi

cat <<EOF

Smith local stack:
  Postgres : localhost:5433  (smith / smith / smith)
  Redis    : localhost:6379
  Backend  : http://localhost:8080  (Swagger UI: /swagger-ui.html)
  Frontend : http://localhost:4200

Tail logs:
  tail -f ${LOG_DIR}/backend.log
  tail -f ${LOG_DIR}/frontend.log

Stop everything:
  scripts/dev-down.sh
EOF
