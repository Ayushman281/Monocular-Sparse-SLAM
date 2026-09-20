#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/hosted_guard.sh"
sudo apt-get update
sudo apt-get install -y --no-install-recommends build-essential cmake ninja-build git curl ca-certificates \
  pkg-config libeigen3-dev libopencv-dev libyaml-cpp-dev libsqlite3-dev libsuitesparse-dev \
  libspdlog-dev libgl1-mesa-dev ffmpeg python3-venv python3-dev xz-utils
