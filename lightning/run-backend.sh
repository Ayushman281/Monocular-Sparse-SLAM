#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export EXECUTION_TARGET=lightning
export SLAM_PREFIX="${SLAM_PREFIX:-$ROOT/.local/slam}"
export SLAM_RUNNER="${SLAM_RUNNER:-$SLAM_PREFIX/bin/slam_runner}"
export SLAM_VOCAB="${SLAM_VOCAB:-$SLAM_PREFIX/share/orb_vocab.fbow}"
export LD_LIBRARY_PATH="$SLAM_PREFIX/lib:${LD_LIBRARY_PATH:-}"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
export API_HOST="${API_HOST:-0.0.0.0}"
if [[ "${API_PORT:-8000}" != 8000 ]]; then
  echo 'Lightning frontend proxying requires API_PORT=8000.' >&2
  exit 1
fi
export API_PORT=8000
export JOB_ROOT="${JOB_ROOT:-$ROOT/data/jobs}"
# The Lightning frontend is a separate process on 5173. Keep this API process
# API-only so the two public ports have unambiguous roles.
export FRONTEND_DIR="${FRONTEND_DIR:-$ROOT/.local/no-static-frontend}"

source "$ROOT/scripts/hosted_guard.sh"
source "$ROOT/lightning/python_env.sh"

if [[ "${ENABLE_SLAM:-false}" != true ]]; then
  echo 'Set ENABLE_SLAM=true on the selected Lightning Studio before starting the backend.' >&2
  exit 1
fi
if [[ ! -x "$SLAM_RUNNER" ]]; then
  echo "SLAM runner is missing: $SLAM_RUNNER. From backend/, run bash setup-lightning.sh first." >&2
  exit 1
fi
if [[ ! -s "$SLAM_VOCAB" ]]; then
  echo "ORB vocabulary is missing: $SLAM_VOCAB. From backend/, run bash setup-lightning.sh first." >&2
  exit 1
fi
echo "Starting the SLAM API on http://0.0.0.0:$API_PORT"
exec "$PYTHON_BIN" "$ROOT/scripts/cloud_backend.py"
