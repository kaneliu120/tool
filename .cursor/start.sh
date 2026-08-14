#!/usr/bin/env bash
# Per-boot gateway for Cloud Agents / local VMs.
# Idempotent: if :8080 already serves /healthz, exit 0.
# Must return after readiness (do not keep this script in the foreground
# unless --attach is passed for a named terminal).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Cloud VM: Engine on :2375, no docker.sock. Harmless if docker is unused.
if [[ ! -S /var/run/docker.sock ]] \
  && curl -sf --max-time 1 http://127.0.0.1:2375/version >/dev/null 2>&1; then
  export DOCKER_HOST="${DOCKER_HOST:-tcp://127.0.0.1:2375}"
fi

PORT="${REA_GATEWAY_PORT:-8080}"
HOST="${REA_GATEWAY_HOST:-0.0.0.0}"
SESSION="${REA_GATEWAY_TMUX_SESSION:-rea-gateway}"
LOG="${REA_GATEWAY_LOG:-/tmp/rea-gateway.log}"
ATTACH=0
if [[ "${1:-}" == "--attach" ]]; then
  ATTACH=1
fi

health() {
  curl -sf "http://127.0.0.1:${PORT}/healthz" >/dev/null
}

tmux_bin() {
  if [[ -f /exec-daemon/tmux.portal.conf ]]; then
    tmux -f /exec-daemon/tmux.portal.conf "$@"
  else
    tmux "$@"
  fi
}

start_server() {
  if [[ ! -x .venv/bin/uvicorn ]]; then
    echo "start.sh: missing .venv/bin/uvicorn — run ./.cursor/install.sh first" >&2
    exit 1
  fi
  mkdir -p "$(dirname "$LOG")"
  touch "$LOG"
  if tmux_bin has-session -t "=$SESSION" 2>/dev/null; then
    tmux_bin kill-session -t "=$SESSION" 2>/dev/null || true
  fi
  tmux_bin new-session -d -s "$SESSION" -c "$ROOT" -- \
    env REA_INCLUDE_MOCK=1 REA_GATEWAY_HOST="$HOST" REA_GATEWAY_PORT="$PORT" \
    bash -lc "exec .venv/bin/uvicorn rea_unblocker.gateway.app:app --host ${HOST} --port ${PORT} >>${LOG} 2>&1"
}

wait_healthy() {
  local i
  for i in $(seq 1 40); do
    if health; then
      echo "gateway ready on :${PORT} (tmux session ${SESSION})"
      return 0
    fi
    sleep 0.25
  done
  echo "start.sh: gateway did not become healthy on :${PORT}" >&2
  tail -n 80 "$LOG" >&2 || true
  return 1
}

if health; then
  echo "gateway already healthy on :${PORT}"
else
  start_server
  wait_healthy
fi

if [[ "$ATTACH" -eq 1 ]]; then
  touch "$LOG"
  exec tail -n 50 -f "$LOG"
fi
