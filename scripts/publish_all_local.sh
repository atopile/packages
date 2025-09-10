#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/Users/nicholaskrstevski/github/packages/packages}"

for dir in "$ROOT"/*; do
  [ -d "$dir" ] || continue
  [ -f "$dir/ato.yaml" ] || { echo "Skipping $(basename "$dir"): no ato.yaml"; continue; }

  echo "Publishing $(basename "$dir")..."
  if (cd "$dir" && ato package publish --skip-auth); then
    echo "OK: $(basename "$dir")"
  else
    echo "FAILED: $(basename "$dir")" >&2
  fi
done