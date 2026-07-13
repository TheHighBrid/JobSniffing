#!/data/data/com.termux/files/usr/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

[ -x .venv-termux/bin/python ] || { echo "Missing .venv-termux. Run ./scripts/termux-bootstrap.sh" >&2; exit 1; }
export JOBSNIFFING_DB="${JOBSNIFFING_DB:-$ROOT/data/jobsniffing.sqlite3}"
exec .venv-termux/bin/python -m uvicorn app.main:app \
  --host "${HOST:-127.0.0.1}" \
  --port "${PORT:-8010}"
