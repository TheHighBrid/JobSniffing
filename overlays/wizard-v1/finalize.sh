#!/usr/bin/env bash
set -euo pipefail
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"
python -m compileall -q app tests
python - <<'PY'
from app.adapters.submit.wizard import WizardConfig, WizardLimits, run_wizard
assert WizardLimits().max_steps == 8
assert callable(run_wizard)
assert WizardConfig(adapter_name="check").adapter_name == "check"
PY
