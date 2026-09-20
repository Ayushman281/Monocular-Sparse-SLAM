#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export EXECUTION_TARGET=lightning
source "$ROOT/scripts/hosted_guard.sh"
export INSTALL_NODE_IF_MISSING=true
source "$ROOT/lightning/node_env.sh"
cd "$ROOT/frontend"
node --version
npm --version
npm ci
npm run build:hosted
echo 'Frontend setup finished. From frontend/: bash run-lightning.sh'
