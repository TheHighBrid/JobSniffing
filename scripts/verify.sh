#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
if [ -x .venv/bin/python ]; then PYTHON="$ROOT/.venv/bin/python"; else PYTHON=$(command -v python3 || command -v python); fi
"$PYTHON" -m pytest -q
TMP_DIR=$(mktemp -d)
PORT=$($PYTHON - <<'PYPORT'
import socket
with socket.socket() as s:
    s.bind(('127.0.0.1',0)); print(s.getsockname()[1])
PYPORT
)
export JOBSNIFFING_DB="$TMP_DIR/verify.sqlite3"
"$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" --log-level warning >"$TMP_DIR/server.log" 2>&1 &
PID=$!
cleanup(){ kill "$PID" 2>/dev/null || true; wait "$PID" 2>/dev/null || true; rm -rf "$TMP_DIR"; }
trap cleanup EXIT INT TERM
"$PYTHON" - "$PORT" <<'PYSMOKE'
import json,sys,time
from urllib.error import URLError
from urllib.request import Request,urlopen
base=f'http://127.0.0.1:{sys.argv[1]}'
for _ in range(50):
    try:
        with urlopen(base+'/health',timeout=1) as r: health=json.load(r)
        break
    except URLError: time.sleep(.1)
else: raise SystemExit('Server did not become healthy')
payload={'source':'verify','external_id':'smoke-1','title':'Bilingual Fraud Investigator','company':'Example','location':'Ottawa','apply_url':'https://example.com/apply','description':'AML KYC banking investigation'}
req=Request(base+'/api/jobs',data=json.dumps(payload).encode(),headers={'content-type':'application/json'},method='POST')
with urlopen(req,timeout=2) as r: created=json.load(r)
if not created.get('id'): raise SystemExit(created)
print(f"Verified tests, server startup, HTTP API, and temporary SQLite database on port {sys.argv[1]}")
PYSMOKE
