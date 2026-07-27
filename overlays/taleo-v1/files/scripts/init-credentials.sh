#!/usr/bin/env bash
set -euo pipefail

TARGET="${JOBSNIFFING_CREDENTIALS_FILE:-$HOME/.config/jobsniffing/credentials.json}"
mkdir -p "$(dirname "$TARGET")"
umask 077

if [[ -e "$TARGET" ]]; then
  echo "Credential file already exists: $TARGET"
  echo "No changes made."
  exit 0
fi

cat > "$TARGET" <<'JSON'
{
  "version": 1,
  "providers": {
    "smtp": {
      "default": {
        "host": "",
        "port": 587,
        "username": "",
        "password": "",
        "from_address": "",
        "use_tls": true
      }
    },
    "taleo": {
      "default": {
        "username": "",
        "password": ""
      }
    },
    "workday": {
      "default": {
        "username": "",
        "password": ""
      }
    }
  }
}
JSON
chmod 600 "$TARGET"
printf 'Created owner-only credential file: %s\n' "$TARGET"
printf 'Edit it locally. Never copy it into the JobSniffing repository.\n'
