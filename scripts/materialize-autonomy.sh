#!/usr/bin/env bash
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

if [[ ! -f jobsniffing-consolidation-v1.zip ]]; then
  echo "Missing jobsniffing-consolidation-v1.zip" >&2
  exit 1
fi

if [[ ! -f .autonomy-current.part-00 || ! -f .autonomy-current.part-02h ]]; then
  echo "Missing one or more autonomy overlay parts" >&2
  exit 1
fi

if [[ ! -f overlays/credentials-v1/apply.sh ]]; then
  echo "Missing transparent credentials-v1 overlay" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

unzip -q jobsniffing-consolidation-v1.zip -d "$TMP_DIR"
cp -a "$TMP_DIR/JobSniffing/." ./

cat .autonomy-current.part-* | base64 --decode | tar -xzf -
bash overlays/credentials-v1/apply.sh

find . -type d -name __pycache__ -prune -exec rm -rf {} +
rm -rf .pytest_cache jobsniffing.egg-info data
chmod +x scripts/*.sh

python -m pip install --upgrade pip
python -m pip install -e '.[test]'
sh scripts/verify.sh

rm -f .autonomy-current.part-*
rm -f .autonomy-phase1.tar.gz.b64
rm -f jobsniffing-consolidation-v1.zip jobsniffing-consolidation-v1.bundle
rm -f .github/workflows/autonomy-bootstrap.yml
rm -rf overlays/credentials-v1

echo
echo "Autonomy source tree with external credentials materialized and verified."
echo "Review with: git status && git diff --stat"
echo "Then commit and push only after review."