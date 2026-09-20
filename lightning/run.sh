#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export EXECUTION_TARGET=lightning
if [[ "${API_PORT:-8000}" != 8000 ]]; then
  echo 'Lightning frontend proxying requires API_PORT=8000.' >&2
  exit 1
fi
export API_PORT=8000
source "$ROOT/lightning/python_env.sh"

PIDS=()
stop_services() {
  trap - EXIT
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null || true
  done
}
stop_on_signal() {
  stop_services
  exit 130
}
trap stop_services EXIT
trap stop_on_signal INT TERM

bash "$ROOT/lightning/run-backend.sh" &
BACKEND_PID=$!
PIDS+=("$BACKEND_PID")

BACKEND_READY=false
for _ in $(seq 1 60); do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    wait "$BACKEND_PID"
    exit $?
  fi
  if "$PYTHON_BIN" -c '
import json, urllib.request
import os
url = "http://127.0.0.1:" + os.environ["API_PORT"] + "/api/health"
data = json.load(urllib.request.urlopen(url, timeout=2))
raise SystemExit(0 if data.get("status") == "healthy" else 1)
' 2>/dev/null; then
    BACKEND_READY=true
    break
  fi
  sleep 1
done
if [[ "$BACKEND_READY" != true ]]; then
  echo 'Backend did not become healthy within 60 seconds.' >&2
  exit 1
fi

bash "$ROOT/lightning/run-frontend.sh" &
FRONTEND_PID=$!
PIDS+=("$FRONTEND_PID")

echo "Assignment 2 is running: backend $API_PORT, frontend 5173."
echo 'Expose port 5173 with the Lightning Ports tool and use its public URL.'

set +e
wait -n "$BACKEND_PID" "$FRONTEND_PID"
STATUS=$?
set -e
exit "$STATUS"
