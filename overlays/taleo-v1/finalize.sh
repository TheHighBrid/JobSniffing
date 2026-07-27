#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
python -m compileall -q app tests
python - <<'PY'
from app.adapters.submit.taleo_playwright import CONFIG, is_taleo_url
from app.services.submission_service import INSPECTABLE_ADAPTERS
assert is_taleo_url("https://example.taleo.net/careersection/2/jobdetail.ftl?job=1")
assert not is_taleo_url("https://example.oraclecloud.com/candidate/job/1")
assert "taleo" in INSPECTABLE_ADAPTERS
assert "input[type='submit'][value='Submit']" in CONFIG.submit_selectors
PY
