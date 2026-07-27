#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
OVERLAY="$ROOT/overlays/wizard-v1/files"
for path in \
  app/adapters/submit/wizard.py \
  app/adapters/submit/browser_form.py \
  app/adapters/submit/handoff.py \
  tests/unit/test_wizard_engine.py \
  docs/SPRINT_HANDOFF.md \
  README.md
do
  test -f "$OVERLAY/$path" || { echo "Missing wizard-v1 overlay file: $path" >&2; exit 1; }
done
cp -a "$OVERLAY/." "$ROOT/"
