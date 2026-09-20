#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/lightning/node_env.sh"

if [[ ! -f "$ROOT/frontend/dist/app-config.json" ]]; then
  echo 'Hosted frontend build is missing. From frontend/, run bash setup-lightning.sh first.' >&2
  exit 1
fi
if ! grep -Eq '"preview"[[:space:]]*:[[:space:]]*false' "$ROOT/frontend/dist/app-config.json"; then
  echo 'The frontend is a local-preview build. From frontend/, run bash setup-lightning.sh.' >&2
  exit 1
fi
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  echo 'Frontend dependencies are missing. From frontend/, run bash setup-lightning.sh first.' >&2
  exit 1
fi

echo 'Starting the React frontend on http://0.0.0.0:5173'
echo 'Requests under /api are proxied to the backend on 127.0.0.1:8000.'
exec npm --prefix "$ROOT/frontend" run preview:hosted
