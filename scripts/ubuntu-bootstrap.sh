#!/usr/bin/env sh
set -eu
if ! command -v apt-get >/dev/null 2>&1; then echo "This script requires Ubuntu/Debian." >&2; exit 1; fi
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
if ! command -v python3 >/dev/null 2>&1 || ! python3 -m venv --help >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip ca-certificates
fi
cd "$ROOT"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[test]'
./scripts/verify.sh
echo "Ready. Run ./scripts/termux-run.sh"
