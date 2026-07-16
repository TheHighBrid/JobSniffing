#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

required_files=(
  app/adapters/submit/dom_kit.py
  app/adapters/submit/wizard.py
  app/adapters/submit/taleo_playwright.py
  app/adapters/submit/workday_playwright.py
  app/services/credential_service.py
  tests/unit/test_wizard_engine.py
  tests/unit/test_taleo_adapter.py
  tests/unit/test_workday_adapter.py
)

for path in "${required_files[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Materialized source is incomplete: missing $path" >&2
    exit 1
  fi
done

find . -type d -name __pycache__ -prune -exec rm -rf {} +
rm -rf .pytest_cache jobsniffing.egg-info data
chmod +x scripts/*.sh

python -m pip install --upgrade pip
python -m pip install -e '.[test]'
sh scripts/verify.sh

echo
echo "Checked-in autonomy source through Workday v1 verified successfully."
