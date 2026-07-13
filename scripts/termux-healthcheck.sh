#!/usr/bin/env sh
set -eu
python3 - "http://127.0.0.1:${PORT:-8010}/health" <<'PYCODE'
import json,sys
from urllib.request import urlopen
with urlopen(sys.argv[1],timeout=5) as r: payload=json.load(r)
if payload.get('status')!='ok': raise SystemExit(payload)
print(json.dumps(payload,indent=2))
PYCODE
