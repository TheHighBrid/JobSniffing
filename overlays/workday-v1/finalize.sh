#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
python -m compileall -q app tests
python - <<'PY2'
from app.adapters.submit.workday_playwright import WorkdayPlaywrightAdapter, parse_workday_target
from app.adapters.submit.dom_kit import try_combobox
assert WorkdayPlaywrightAdapter.name == "workday"
assert callable(try_combobox)
target = parse_workday_target("https://acme.wd5.myworkdayjobs.com/en-US/Careers/job/Ottawa/Analyst_R-123?source=private")
assert target is not None
assert target.job_id == "R-123"
assert "?" not in target.safe_url
PY2
