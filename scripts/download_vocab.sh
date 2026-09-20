#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/scripts/hosted_guard.sh"
source "$ROOT/slam/dependencies.env"
PREFIX="${SLAM_PREFIX:-$ROOT/.local/slam}"
mkdir -p "$PREFIX/share"
curl --fail --location --retry 3 \
  "https://raw.githubusercontent.com/stella-cv/FBoW_orb_vocab/$VOCAB_COMMIT/orb_vocab.fbow" \
  -o "$PREFIX/share/orb_vocab.fbow.part"
[[ "$(wc -c < "$PREFIX/share/orb_vocab.fbow.part")" -gt 1000000 ]]
mv "$PREFIX/share/orb_vocab.fbow.part" "$PREFIX/share/orb_vocab.fbow"
sha256sum "$PREFIX/share/orb_vocab.fbow" > "$PREFIX/share/orb_vocab.sha256"
echo 'Vocabulary fetched at a pinned Git revision; checksum recorded for benchmark provenance.'
