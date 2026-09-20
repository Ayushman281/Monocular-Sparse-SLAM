#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export EXECUTION_TARGET=lightning
source "$ROOT/scripts/hosted_guard.sh"
source "$ROOT/lightning/python_env.sh"
cd "$ROOT/backend"

# Native dependencies are shared project assets, installed under .local/slam.
# This setup deliberately installs no frontend packages and runs no npm build.
bash "$ROOT/scripts/install_system.sh"
bash "$ROOT/scripts/build_native.sh"
bash "$ROOT/scripts/download_vocab.sh"
"$PYTHON_BIN" -m pip install -r requirements-test.txt
echo 'Backend setup finished. From backend/: ENABLE_SLAM=true bash run-lightning.sh'
