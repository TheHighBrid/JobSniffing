#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
PARTS=(overlays/workday-v1/workday-v1.patch.part-*)
if [[ ${#PARTS[@]} -ne 7 || ! -f "${PARTS[0]}" ]]; then
  echo "Missing one or more transparent Workday patch parts" >&2
  exit 1
fi
PATCH_FILE="$(mktemp)"
trap 'rm -f "$PATCH_FILE"' EXIT
cat "${PARTS[@]}" > "$PATCH_FILE"
printf '%s  %s\n' "d1fd83017240e073b303e2ce61371df1cc5b66d49d8ff15ff56a5f475c8590bb" "$PATCH_FILE" | sha256sum -c -
patch --batch --forward -p2 < "$PATCH_FILE"
