#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/hosted_guard.sh"
source "$ROOT/slam/dependencies.env"
PREFIX="${SLAM_PREFIX:-$ROOT/.local/slam}"
WORK="$ROOT/build/dependencies"
JOBS="${BUILD_JOBS:-2}"
mkdir -p "$WORK" "$PREFIX/share/licenses"
fetch() {
  local url="$1" sha="$2" dest="$3"
  if [[ ! -d "$dest/.git" ]]; then
    git init "$dest"
    git -C "$dest" remote add origin "$url"
  fi
  if [[ -n "$(git -C "$dest" status --porcelain)" ]]; then
    echo "Source tree is modified: $dest. Inspect it before retrying; no automatic reset." >&2
    exit 1
  fi
  git -C "$dest" fetch --depth 1 origin "$sha"
  git -C "$dest" checkout --detach FETCH_HEAD
  [[ "$(git -C "$dest" rev-parse HEAD)" == "$sha" ]]
}
fetch https://github.com/RainerKuemmerle/g2o.git "$G2O_COMMIT" "$WORK/g2o"
cmake -S "$WORK/g2o" -B "$WORK/g2o-build" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" \
  -DBUILD_SHARED_LIBS=ON -DBUILD_UNITTESTS=OFF -DBUILD_WITH_MARCH_NATIVE=OFF \
  -DG2O_USE_CHOLMOD=OFF -DG2O_USE_CSPARSE=ON -DG2O_USE_OPENGL=OFF -DG2O_USE_OPENMP=OFF \
  -DG2O_BUILD_APPS=OFF -DG2O_BUILD_EXAMPLES=OFF -DG2O_BUILD_LINKED_APPS=OFF
cmake --build "$WORK/g2o-build" --parallel "$JOBS"
cmake --install "$WORK/g2o-build"
fetch https://github.com/stella-cv/FBoW.git "$FBOW_COMMIT" "$WORK/fbow"
cmake -S "$WORK/fbow" -B "$WORK/fbow-build" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" -DUSE_AVX=OFF -DUSE_SSE=OFF
cmake --build "$WORK/fbow-build" --parallel "$JOBS"
cmake --install "$WORK/fbow-build"
# Reuse a previously patched source only if it is exactly this revision and patch.
STELLA="$WORK/stella"
if [[ -d "$STELLA/.git" ]] && git -C "$STELLA" apply --reverse --check "$ROOT/slam/patches/offline-drain.patch" 2>/dev/null; then
  [[ "$(git -C "$STELLA" rev-parse HEAD)" == "$STELLA_COMMIT" ]]
  git -C "$STELLA" diff --no-ext-diff HEAD > "$WORK/stella-existing.patch"
  if ! cmp -s "$WORK/stella-existing.patch" "$ROOT/slam/patches/offline-drain.patch"; then
    echo 'The stella checkout differs from the recorded patch. Inspect before rebuilding.' >&2
    exit 1
  fi
else
  fetch https://github.com/stella-cv/stella_vslam.git "$STELLA_COMMIT" "$STELLA"
  git -C "$STELLA" submodule update --init --recursive
  git -C "$STELLA" apply --check "$ROOT/slam/patches/offline-drain.patch"
  git -C "$STELLA" apply "$ROOT/slam/patches/offline-drain.patch"
fi
cmake -S "$STELLA" -B "$WORK/stella-build" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" -DCMAKE_PREFIX_PATH="$PREFIX" \
  -DBUILD_TESTS=OFF -DBUILD_WITH_MARCH_NATIVE=OFF -DUSE_OPENMP=ON \
  -DUSE_ARUCO=OFF -DUSE_GTSAM=OFF -DUSE_CUDA_EFFICIENT_DESCRIPTORS=OFF -DBOW_FRAMEWORK=FBoW
cmake --build "$WORK/stella-build" --parallel "$JOBS"
cmake --install "$WORK/stella-build"
cmake -S "$ROOT/slam" -B "$ROOT/build/runner" -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX="$PREFIX" -DCMAKE_PREFIX_PATH="$PREFIX"
cmake --build "$ROOT/build/runner" --parallel "$JOBS"
cmake --install "$ROOT/build/runner"
cp "$STELLA"/LICENSE* "$PREFIX/share/licenses/"
cp "$WORK/fbow/LICENSE" "$PREFIX/share/licenses/FBoW-LICENSE"
cp "$WORK/g2o"/doc/license-*.txt "$PREFIX/share/licenses/"
cp "$STELLA/3rd/json/LICENSE" "$PREFIX/share/licenses/nlohmann-json-LICENSE"
cp "$STELLA/3rd/spdlog/LICENSE" "$PREFIX/share/licenses/spdlog-LICENSE"
cp -R "$ROOT/third_party/licenses/." "$PREFIX/share/licenses/"
cp "$ROOT/slam/dependencies.env" "$PREFIX/share/"
cp "$ROOT/slam/patches/offline-drain.patch" "$PREFIX/share/"
git -C "$STELLA" submodule status > "$PREFIX/share/submodules.txt"
dpkg-query -W > "$PREFIX/share/system-packages.txt"
echo "Native installation prepared at $PREFIX. Run hosted validation next."
