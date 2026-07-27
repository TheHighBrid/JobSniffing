#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

python -m compileall -q app tests
python - <<'PY'
from app.adapters.submit.icims_playwright import IcimsPlaywrightAdapter, parse_icims_target
from app.domain.schemas import InspectRequest, SubmitRequest
from app.services import submission_service

target = parse_icims_target('https://careers-acme.icims.com/jobs/12345/fraud-analyst?source=private')
assert target is not None
assert target.job_id == '12345'
assert '?' not in target.safe_url
assert IcimsPlaywrightAdapter.name == 'icims'
assert 'icims' in submission_service.INSPECTABLE_ADAPTERS
assert submission_service.ADAPTERS['icims'].name == 'icims'
assert InspectRequest(adapter='icims').adapter == 'icims'
assert SubmitRequest(adapter='icims').adapter == 'icims'
PY
