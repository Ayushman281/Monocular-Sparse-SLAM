#!/usr/bin/env bash
set -euo pipefail
case "${EXECUTION_TARGET:-disabled}" in
  aws|lightning) ;;
  *) echo 'Select an authorized hosted EXECUTION_TARGET (aws or lightning).' >&2; exit 1 ;;
esac
if [[ "$(uname -s)" != Linux ]] || grep -qi microsoft /proc/sys/kernel/osrelease; then
  echo 'Backend work is prohibited on Windows/WSL. Use the selected hosted runtime.' >&2
  exit 1
fi
