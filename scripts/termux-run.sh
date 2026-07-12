#!/usr/bin/env sh
set -eu
export JOBSNIFFING_DB="${JOBSNIFFING_DB:-data/jobsniffing.sqlite3}"
exec python -m uvicorn app.main:app --host 127.0.0.1 --port "${PORT:-8010}"
