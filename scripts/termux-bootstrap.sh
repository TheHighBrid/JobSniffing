#!/data/data/com.termux/files/usr/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

pkg install -y python curl
python -m venv .venv-termux
. .venv-termux/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'

echo "Installed. Run: ./scripts/termux-run.sh"
