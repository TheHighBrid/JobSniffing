#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3 python3-venv python3-pip curl
python3 -m venv .venv-ubuntu
. .venv-ubuntu/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'

echo "Installed. Run: ./scripts/ubuntu-run.sh"
