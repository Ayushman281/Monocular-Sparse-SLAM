#!/usr/bin/env bash
# Source this file. It selects a compatible system Node.js or installs a pinned
# official binary under this project without changing the Studio-wide runtime.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NODE_VERSION="${NODE_VERSION:-22.15.0}"

case "$(uname -m)" in
  x86_64|amd64) NODE_ARCH=x64 ;;
  aarch64|arm64) NODE_ARCH=arm64 ;;
  *) echo "Unsupported Node.js architecture: $(uname -m)" >&2; return 1 ;;
esac

NODE_HOME="$ROOT/.local/node-v$NODE_VERSION-linux-$NODE_ARCH"
if [[ -x "$NODE_HOME/bin/node" ]]; then
  export PATH="$NODE_HOME/bin:$PATH"
elif command -v node >/dev/null 2>&1 && node -e '
  const [major, minor] = process.versions.node.split(".").map(Number);
  process.exit(major > 22 || (major === 22 && minor >= 12) ? 0 : 1);
'; then
  :
elif [[ "${INSTALL_NODE_IF_MISSING:-false}" == true ]]; then
  ARCHIVE="node-v$NODE_VERSION-linux-$NODE_ARCH.tar.xz"
  CACHE="$ROOT/.cache/node-v$NODE_VERSION"
  mkdir -p "$CACHE" "$NODE_HOME"
  curl --fail --location --retry 3 "https://nodejs.org/dist/v$NODE_VERSION/$ARCHIVE" -o "$CACHE/$ARCHIVE"
  curl --fail --location --retry 3 "https://nodejs.org/dist/v$NODE_VERSION/SHASUMS256.txt" -o "$CACHE/SHASUMS256.txt"
  (
    cd "$CACHE"
    grep "  $ARCHIVE\$" SHASUMS256.txt | sha256sum --check -
  )
  tar -xJf "$CACHE/$ARCHIVE" --strip-components=1 -C "$NODE_HOME"
  export PATH="$NODE_HOME/bin:$PATH"
else
  echo 'Node.js >=22.12 is required. From frontend/, run bash setup-lightning.sh first.' >&2
  return 1
fi

node -e '
  const [major, minor] = process.versions.node.split(".").map(Number);
  if (!(major > 22 || (major === 22 && minor >= 12))) {
    throw new Error("Node.js >=22.12 is required");
  }
'
