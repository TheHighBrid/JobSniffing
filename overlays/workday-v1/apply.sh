#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

PAYLOAD_PARTS=(
  overlays/workday-v1/payload-gz.part-00
  overlays/workday-v1/payload-gz.part-01
  overlays/workday-v1/payload-gz.part-02
  overlays/workday-v1/payload-gz-tail.part-00
  overlays/workday-v1/payload-gz-tail.part-01
  overlays/workday-v1/payload-gz-tail.part-02
)

for part in "${PAYLOAD_PARTS[@]}"; do
  test -f "$part" || { echo "Missing Workday payload part: $part" >&2; exit 1; }
done

ENCODED_FILE="$(mktemp)"
GZIP_FILE="$(mktemp)"
PATCH_FILE="$(mktemp)"
trap 'rm -f "$ENCODED_FILE" "$GZIP_FILE" "$PATCH_FILE"' EXIT

cat "${PAYLOAD_PARTS[@]}" > "$ENCODED_FILE"
printf 'Workday encoded payload bytes: '
wc -c < "$ENCODED_FILE"
base64 --decode "$ENCODED_FILE" > "$GZIP_FILE"
printf '%s  %s\n' \
  "68f4c18d9bd7cd43684c578cb26f497b5b84a07e542f2cb9916a034756f7417e" \
  "$GZIP_FILE" | sha256sum -c -
gzip --decompress --stdout "$GZIP_FILE" > "$PATCH_FILE"
printf '%s  %s\n' \
  "82c23cfdf1e971912525918f48d1f7e316afc6c3c1957dc907b76c7f400d9b57" \
  "$PATCH_FILE" | sha256sum -c -
patch --batch --forward -p2 < "$PATCH_FILE"
