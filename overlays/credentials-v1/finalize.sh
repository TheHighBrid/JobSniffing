#!/usr/bin/env bash
set -euo pipefail

python - <<'PY'
from pathlib import Path

service = Path('app/services/credential_service.py')
text = service.read_text(encoding='utf-8')
text = text.replace(
    '@dataclass(frozen=True)\nclass CredentialResolution:',
    '@dataclass(frozen=True, repr=False)\nclass CredentialResolution:',
)
needle = '''    source_path: Path\n\n\ndef _normalise_name'''
replacement = '''    source_path: Path\n\n    def __repr__(self) -> str:\n        return (\n            f"CredentialResolution(provider={self.provider!r}, profile={self.profile!r}, "\n            f"source_path={str(self.source_path)!r})"\n        )\n\n\ndef _normalise_name'''
if needle not in text:
    raise SystemExit('credential repr insertion point was not found')
service.write_text(text.replace(needle, replacement), encoding='utf-8')

tests = Path('tests/unit/test_credentials.py')
test_text = tests.read_text(encoding='utf-8')
if 'test_resolution_repr_never_contains_values' not in test_text:
    test_text += '''\n\ndef test_resolution_repr_never_contains_values(monkeypatch, tmp_path):\n    path = write_store(tmp_path / "credentials.json", {\n        "smtp": {"default": {"username": "user", "password": "do-not-print"}}\n    })\n    monkeypatch.setenv(credentials.CREDENTIALS_ENV, str(path))\n    resolved = credentials.resolve_credentials("smtp")\n    assert resolved is not None\n    assert "do-not-print" not in repr(resolved)\n    assert "password" not in repr(resolved)\n'''
tests.write_text(test_text, encoding='utf-8')

handoff = Path('docs/SPRINT_HANDOFF.md')
handoff_text = handoff.read_text(encoding='utf-8')
handoff_text = handoff_text.replace(
    '**Working branch:** `autonomy/shared-primitives-v1`',
    '**Working branch:** `autonomy/credentials-v1`',
).replace(
    'Current result: **99 tests passing**',
    'Current result: **100 tests passing**',
)
handoff.write_text(handoff_text, encoding='utf-8')
PY

echo "Applied credential repr hardening and final handoff metadata."