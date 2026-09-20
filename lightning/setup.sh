#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Optional combined setup; each service also has its own folder-local entry point.
bash "$ROOT/backend/setup-lightning.sh"
bash "$ROOT/frontend/setup-lightning.sh"
echo 'Setup finished. Start both services with: ENABLE_SLAM=true bash lightning/run.sh'
