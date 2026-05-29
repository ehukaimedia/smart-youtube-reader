#!/usr/bin/env bash
# Fetch Inter (the product UI font) as woff2 into a fonts/ dir for HTML rendering.
# Inter is not installed system-wide; the infographic kit @font-face's these files.
# Usage: ./setup_fonts.sh [target_dir]   (default: ./fonts next to where you run it)
set -euo pipefail
DIR="${1:-fonts}"
mkdir -p "$DIR"
BASE="https://cdn.jsdelivr.net/npm/@fontsource/inter/files"
for w in 400 500 600 700 800 900; do
  out="$DIR/inter-$w.woff2"
  if [ -f "$out" ]; then echo "have inter-$w.woff2"; continue; fi
  curl -fsS -o "$out" "$BASE/inter-latin-$w-normal.woff2" \
    && echo "got inter-$w.woff2 ($(wc -c < "$out") bytes)" \
    || echo "FAILED inter-$w (offline? Chrome will fall back to the system sans)"
done
