#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
OVERLAY="$ROOT/overlays/workday-v1/files"
for path in \
  app/adapters/submit/workday_playwright.py \
  app/adapters/submit/dom_kit.py \
  app/services/submission_service.py \
  app/domain/schemas.py \
  app/main.py \
  tests/unit/test_workday_adapter.py \
  docs/credentials.md \
  docs/AUTONOMY_PROGRESS.md \
  docs/SPRINT_HANDOFF.md \
  README.md \
  CHECKPOINT.md
do
  test -f "$OVERLAY/$path" || { echo "Missing workday-v1 overlay file: $path" >&2; exit 1; }
done
cp -a "$OVERLAY/." "$ROOT/"
