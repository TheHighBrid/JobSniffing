#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

[ -x .venv-ubuntu/bin/python ] || { echo "Missing .venv-ubuntu. Run ./scripts/ubuntu-bootstrap.sh" >&2; exit 1; }
export JOBSNIFFING_DB="${JOBSNIFFING_DB:-$ROOT/data/jobsniffing.sqlite3}"
exec .venv-ubuntu/bin/python -m uvicorn app.main:app \
  --host "${HOST:-127.0.0.1}" \
  --port "${PORT:-8010}"
