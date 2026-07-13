#!/usr/bin/env sh
set -eu
curl -fsS "http://${HOST:-127.0.0.1}:${PORT:-8010}/health"
printf '\n'
