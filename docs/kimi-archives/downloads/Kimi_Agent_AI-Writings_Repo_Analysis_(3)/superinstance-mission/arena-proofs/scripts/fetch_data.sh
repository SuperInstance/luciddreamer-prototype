#!/usr/bin/env bash
# Vendor the experiment JSONs needed by arena-proofs from the zeroclaw-arena
# repo (read-only) into data/. Committed copies make the test suite offline.
set -euo pipefail
ZARENA_DIR="${ZARENA_DIR:-/mnt/agents/repos/zeroclaw-arena}"
DEST="$(cd "$(dirname "$0")/.." && pwd)/data"
mkdir -p "$DEST"
files=(
  "scaling-emergence-results.json"
  "decay-results.json"
  "min-exposure-results.json"
  "tile-capacity-results.json"
  "temperature-sweep-results.json"
  "results/temporal-dynamics-results.json"
  "results/reflex-evolution-v2-results.json"
  "results/tile-conservation-results.json"
  "results/holographic-bound-results.json"
  "results/entropy-production-results.json"
)
for f in "${files[@]}"; do
  cp "$ZARENA_DIR/$f" "$DEST/$(basename "$f")"
  echo "vendored $f"
done
