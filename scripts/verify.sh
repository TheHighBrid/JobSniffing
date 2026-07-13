#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

if [ -n "${PYTHON:-}" ]; then
  PYTHON_BIN=$PYTHON
elif [ -n "${TERMUX_VERSION:-}" ] && [ -x .venv-termux/bin/python ]; then
  PYTHON_BIN=.venv-termux/bin/python
elif [ -x .venv-ubuntu/bin/python ]; then
  PYTHON_BIN=.venv-ubuntu/bin/python
elif [ -x .venv-termux/bin/python ]; then
  PYTHON_BIN=.venv-termux/bin/python
else
  PYTHON_BIN=python
fi

TMPDIR_ROOT=$(mktemp -d)
SERVER_PID=""
cleanup() {
  [ -z "$SERVER_PID" ] || kill "$SERVER_PID" 2>/dev/null || true
  rm -rf "$TMPDIR_ROOT"
}
trap cleanup EXIT INT TERM

export JOBSNIFFING_DB="$TMPDIR_ROOT/verify.sqlite3"
export PORT=18110

"$PYTHON_BIN" -m compileall -q app tests
"$PYTHON_BIN" -m pytest
"$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT" >"$TMPDIR_ROOT/server.log" 2>&1 &
SERVER_PID=$!

attempt=0
until curl -fsS "http://127.0.0.1:$PORT/health" >"$TMPDIR_ROOT/health.json" 2>/dev/null; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    cat "$TMPDIR_ROOT/server.log" >&2
    exit 1
  fi
  sleep 0.2
done

grep -q '"status":"ok"' "$TMPDIR_ROOT/health.json"
printf 'Verification passed: compile, tests, startup, health endpoint.\n'
