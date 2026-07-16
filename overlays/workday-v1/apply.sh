#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

PREFIX_PARTS=(
  overlays/workday-v1/workday-v1.patch.b64.part-00
  overlays/workday-v1/workday-v1.patch.b64.part-01
)
TAIL_PARTS=(overlays/workday-v1/workday-v1.tail.part-*)

printf 'Workday payload parts: prefix=%s tail=%s\n' "${#PREFIX_PARTS[@]}" "${#TAIL_PARTS[@]}"
if [[ ! -f "${PREFIX_PARTS[0]}" || ! -f "${PREFIX_PARTS[1]}" || ${#TAIL_PARTS[@]} -ne 12 || ! -f "${TAIL_PARTS[0]}" ]]; then
  echo "Missing one or more Workday payload parts" >&2
  printf '%s\n' "${PREFIX_PARTS[@]}" "${TAIL_PARTS[@]}" >&2
  exit 1
fi

ENCODED_FILE="$(mktemp)"
PATCH_FILE="$(mktemp)"
trap 'rm -f "$ENCODED_FILE" "$PATCH_FILE"' EXIT

cat "${PREFIX_PARTS[@]}" "${TAIL_PARTS[@]}" > "$ENCODED_FILE"
printf 'Encoded payload bytes: '
wc -c < "$ENCODED_FILE"
base64 --decode "$ENCODED_FILE" > "$PATCH_FILE"
printf 'Decoded patch SHA-256: '
sha256sum "$PATCH_FILE"
printf '%s  %s\n' \
  "82c23cfdf1e971912525918f48d1f7e316afc6c3c1957dc907b76c7f400d9b57" \
  "$PATCH_FILE" | sha256sum -c -
patch --batch --forward -p2 < "$PATCH_FILE"
