#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
if [ -f .env ]; then set -a; . "$ROOT/.env"; set +a; fi
if [ -x .venv/bin/python ]; then PYTHON="$ROOT/.venv/bin/python"; else PYTHON=$(command -v python3 || command -v python); fi
export JOBSNIFFING_DB="${JOBSNIFFING_DB:-data/jobsniffing.sqlite3}"
exec "$PYTHON" -m uvicorn app.main:app --host "${HOST:-127.0.0.1}" --port "${PORT:-8010}"
