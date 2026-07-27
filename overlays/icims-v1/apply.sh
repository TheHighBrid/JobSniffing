#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

PARTS=(
  overlays/icims-v1/icims-v1.patch.xz.b64.part-00
  overlays/icims-v1/icims-v1.patch.xz.b64.part-01
)
for part in "${PARTS[@]}"; do
  [[ -f "$part" ]] || { echo "Missing iCIMS overlay part: $part" >&2; exit 1; }
done

ENCODED="$(mktemp)"
COMPRESSED="$(mktemp)"
PATCH_FILE="$(mktemp)"
trap 'rm -f "$ENCODED" "$COMPRESSED" "$PATCH_FILE"' EXIT

cat "${PARTS[@]}" > "$ENCODED"
base64 --decode "$ENCODED" > "$COMPRESSED"
printf '%s  %s\n' \
  'a8c4b2301182c10b856355eb3f3aac432c50974f2cdf048e1154c98a25218ae3' \
  "$COMPRESSED" | sha256sum -c -
xz --decompress --stdout "$COMPRESSED" > "$PATCH_FILE"
printf '%s  %s\n' \
  '3339cfb5c89c32ebfea42cf0ec74874f2be772a0f04d7dda13ed6ad9f92f3826' \
  "$PATCH_FILE" | sha256sum -c -
patch --batch --forward -p5 < "$PATCH_FILE"
