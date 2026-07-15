#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
OVERLAY="$ROOT/overlays/taleo-v1/files"
for path in \
  app/adapters/submit/taleo_playwright.py \
  app/services/submission_service.py \
  app/domain/schemas.py \
  app/main.py \
  scripts/init-credentials.sh \
  tests/unit/test_taleo_adapter.py \
  docs/credentials.md \
  docs/SPRINT_HANDOFF.md \
  README.md
do
  test -f "$OVERLAY/$path" || { echo "Missing taleo-v1 overlay file: $path" >&2; exit 1; }
done
cp -a "$OVERLAY/." "$ROOT/"
