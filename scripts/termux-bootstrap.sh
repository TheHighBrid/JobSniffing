#!/usr/bin/env sh
set -eu
pkg update
pkg install -y python git
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
echo "Run ./scripts/termux-run.sh and open http://127.0.0.1:8010"
