#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/hosted_guard.sh"
cd "$ROOT"
export ENABLE_SLAM=true
source "$ROOT/lightning/node_env.sh"
source "$ROOT/lightning/python_env.sh"
"$PYTHON_BIN" -m pytest backend/tests -q
npm --prefix frontend run build:hosted
"${SLAM_RUNNER:-$ROOT/.local/slam/bin/slam_runner}" --version
echo 'Unit checks and frontend build completed. Real video and public deployment acceptance are separate.'
