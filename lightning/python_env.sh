#!/usr/bin/env bash
# Source this file. Lightning Studios expose one persistent Conda environment
# and prohibit nested venv creation, so use that active interpreter directly.
# A pre-existing .venv remains supported for non-Studio hosted environments.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${EXECUTION_TARGET:-}" != lightning && -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$ROOT/.venv/bin/python"
elif [[ -n "${PYTHON_BIN:-}" ]] && command -v "$PYTHON_BIN" >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v "$PYTHON_BIN")"
else
  PYTHON_BIN=""
  # `python` is first because it is the interpreter from Lightning's active
  # Conda environment; a system python3 may be older.
  for candidate in python python3 python3.13 python3.12 python3.11; do
    if command -v "$candidate" >/dev/null 2>&1 \
        && "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
      PYTHON_BIN="$(command -v "$candidate")"
      break
    fi
  done
fi

if [[ -z "$PYTHON_BIN" ]] \
    || ! "$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo 'Python 3.11 or newer is required in the active Studio Conda environment.' >&2
  return 1
fi

export PYTHON_BIN
