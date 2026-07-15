#!/usr/bin/env bash
set -euo pipefail

# Transparent source overlay for autonomy step 1: external credentials.
mkdir -p "$(dirname '.env.example')"
cat > '.env.example' <<'JOB_SNIFFING_CREDENTIALS_V1_0'
HOST=127.0.0.1
PORT=8010
JOBSNIFFING_DB=data/jobsniffing.sqlite3

# Owner-only JSON outside the repository. Create it with scripts/init-credentials.sh.
# JOBSNIFFING_CREDENTIALS_FILE=~/.config/jobsniffing/credentials.json

# --- Submission (consolidation-v1) ---------------------------------------
# Hard gate: live submissions stay disabled until this is exactly 1.
JOBSNIFFING_ALLOW_LIVE_SUBMISSION=0
# Tier-0 email compatibility fallback. Prefer smtp/default in the external credential file.
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_ADDRESS=
SMTP_USE_TLS=1
JOB_SNIFFING_CREDENTIALS_V1_0

mkdir -p "$(dirname '.gitignore')"
cat > '.gitignore' <<'JOB_SNIFFING_CREDENTIALS_V1_1'
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
.venv/
data/
exports/
*.sqlite3
*.sqlite3-shm
*.sqlite3-wal
node_modules/
dist/
build/
.env
# Local secrets must stay outside the repository. These patterns are a final guard.
credentials.local.json
*.credentials.local.json
secrets.local.json
.credentials/
JOB_SNIFFING_CREDENTIALS_V1_1

mkdir -p "$(dirname 'README.md')"
cat > 'README.md' <<'JOB_SNIFFING_CREDENTIALS_V1_2'
# JobSniffing

JobSniffing is an Android-first, local-first job discovery and human review queue. It runs as one FastAPI process with one SQLite file and a mobile-friendly dashboard.

> **Public ATS APIs first, browser automation last, human approval before every real application.**

## What is ready

- Live discovery from Greenhouse, Lever, and Ashby public boards.
- Manual entry and JSON bulk import.
- Offline scoring with editable weighted terms.
- Defaults tuned for bilingual banking, fraud, AML/KYC, compliance, risk, government, Ottawa/Gatineau, and remote-Canada searches.
- Negative-term penalties and company blocking.
- Strict status transitions with proper 404, 409, and 422 responses.
- Mobile dashboard for filters, review, status changes, deletion, and opening applications.
- SQLite deduplication, rescoring, CSV export, diagnostics, and OpenAPI docs.
- Ubuntu/proot and native Termux bootstrap scripts.
- No Redis, Celery, Docker, paid AI key, cloud database, or browser driver.
- Real submission remains evidence-gated and is never falsely reported.

## Consolidation-v1 additions

- Full application pipeline: `discovered → scored → shortlisted → documents_prepared → answers_prepared → ready_for_review → approved → queued → filling → awaiting_confirmation → submitted`, with `verification_failed`, `manual_intervention_required`, `rejected`, `withdrawn`, and `closed` branches.
- Three automation modes (`discovery_only` default, `prepare_only`, `autonomous`) with a color-coded dashboard switch and per-company/ATS/job autonomy opt-in.
- Verified candidate profile (per-field source, verification, contexts, permissions; sensitive keys locked to manual approval).
- Question engine: safe_auto / adapter_rule / requires_review classification; answers only from the verified profile or the approved QA bank; unknown is never guessed.
- Document pipeline: id-tracked master resume facts, reorder-only tailoring, factuality report (source facts, excluded keywords, exaggeration flags), grounded cover letter, ATS-safe ReportLab PDFs.
- Submission: Tier-0 email adapter (stdlib SMTP), Greenhouse Playwright adapter as opt-in `[automation]` extra; both fail closed, CAPTCHA hands off to you, and `submitted` requires recorded confirmation evidence.
- 9-check gate report per job (`GET /api/jobs/{id}/gates`), full audit (`/audit`), JSON export (`/api/export.json`).
- See `docs/CONSOLIDATION.md` for the decision record. Fill in `.env` from `.env.example` before enabling live sends.

## External credentials

Credentials for SMTP and future login-based ATS adapters live in an owner-only JSON file outside the repository. Create the file with:

```sh
sh scripts/init-credentials.sh
```

The default path is `~/.config/jobsniffing/credentials.json`. The loader rejects repository-local files and insecure POSIX permissions. See `docs/credentials.md`.

## Recommended Android setup

Run in Termux:

```sh
pkg update -y
pkg install -y proot-distro
proot-distro install ubuntu:24.04
proot-distro login ubuntu
```

Run inside Ubuntu:

```sh
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git ca-certificates
cd /root
git clone https://github.com/TheHighBrid/JobSniffing.git
cd JobSniffing
./scripts/ubuntu-bootstrap.sh
./scripts/termux-run.sh
```

Open `http://127.0.0.1:8010` in the Android browser. Keep the Termux session open.

The bootstrap installs missing Python packages, creates `.venv`, installs JobSniffing, runs all tests, starts a temporary server, and verifies a real health request.

## Native Termux alternative

```sh
pkg update -y
pkg install -y git
git clone https://github.com/TheHighBrid/JobSniffing.git
cd JobSniffing
./scripts/termux-bootstrap.sh
./scripts/termux-run.sh
```

## Daily start

Ubuntu route:

```sh
proot-distro login ubuntu
cd /root/JobSniffing
./scripts/termux-run.sh
```

Native Termux route:

```sh
cd ~/JobSniffing
./scripts/termux-run.sh
```

## Add a job

```sh
curl -X POST http://127.0.0.1:8010/api/jobs \
  -H 'content-type: application/json' \
  -d '{"source":"manual","external_id":"example-1","title":"Bilingual Fraud Investigator","company":"Example Bank","location":"Ottawa","apply_url":"https://example.com/apply","description":"AML KYC banking investigation and client service"}'
```

## Discover an ATS board

```sh
curl -X POST http://127.0.0.1:8010/api/discovery \
  -H 'content-type: application/json' \
  -d '{"provider":"greenhouse","identifier":"company-board-token","company":"Company Name","query":"fraud","location":"Canada","limit":100}'
```

Use `lever` or `ashby` for the other supported providers. The identifier accepts only letters, numbers, underscores, and hyphens, which prevents arbitrary URL fetching.

## Tune scoring

Read settings:

```sh
curl http://127.0.0.1:8010/api/settings/scoring
```

Replace settings and automatically rescore all jobs:

```sh
curl -X PUT http://127.0.0.1:8010/api/settings/scoring \
  -H 'content-type: application/json' \
  -d '{"preferred_terms":{"fraud":20,"aml":18,"kyc":16,"bilingual":14,"compliance":14,"investigation":12,"ottawa":8,"remote":6},"excluded_terms":["commission only","door to door"],"blacklisted_companies":[],"minimum_score":15}'
```

Title matches receive double weight. Each excluded term subtracts 35 points. Scores are clamped from 0 to 100. Blacklisted companies are moved to `blocked` unless a job is already terminal.

## Verify after updates

```sh
cd /root/JobSniffing
./scripts/verify.sh
```

For native Termux, use `cd ~/JobSniffing` first.

## Backup and export

Stop the server before copying the database:

```sh
cp data/jobsniffing.sqlite3 "$HOME/jobsniffing-backup.sqlite3"
```

Export CSV while running:

```sh
curl -o jobsniffing-export.csv http://127.0.0.1:8010/api/jobs/export.csv
```

## Useful addresses

- Dashboard: `http://127.0.0.1:8010`
- Health: `http://127.0.0.1:8010/health`
- API docs: `http://127.0.0.1:8010/docs`
- Jobs JSON: `http://127.0.0.1:8010/api/jobs`
- CSV export: `http://127.0.0.1:8010/api/jobs/export.csv`

## Safety boundary

JobSniffing discovers, scores, prepares, and tracks. It does not attempt universal auto-submission. A future submission adapter must be site-specific, dry-run-first, and must observe a confirmation signal before the state can become `submitted`.

- [Detailed Android, Termux, and Ubuntu guide](docs/termux.md)
- [Audit and readiness report](docs/audit.md)
- [Architecture](docs/architecture.md)
- [API contract](docs/api-contract.md)
- [Status machine](docs/status-machine.md)
JOB_SNIFFING_CREDENTIALS_V1_2

mkdir -p "$(dirname 'app/adapters/submit/email_smtp.py')"
cat > 'app/adapters/submit/email_smtp.py' <<'JOB_SNIFFING_CREDENTIALS_V1_3'
"""Tier-0 submission channel: direct email with attachments over SMTP.

Termux-native (stdlib only). Live sending requires BOTH the per-call
live=True flag and the JOBSNIFFING_ALLOW_LIVE_SUBMISSION=1 environment gate;
the environment gate cannot be toggled from the API or dashboard.
For email, credible confirmation = the SMTP server accepted the message;
the Message-ID plus a full RFC-822 copy are stored as evidence.
"""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from pathlib import Path

from app.adapters.submit.base import LIVE_ENV_FLAG, AdapterInput, AdapterOutcome
from app.services.credential_service import CredentialError, resolve_credentials


class EmailSmtpAdapter:
    name = "email"

    def run(self, ctx: AdapterInput) -> AdapterOutcome:
        if not ctx.to_email or "@" not in ctx.to_email:
            return AdapterOutcome("manual_intervention", "no destination email address was provided")
        resume = Path(ctx.resume_pdf) if ctx.resume_pdf else None
        if resume is None or not resume.exists():
            return AdapterOutcome("manual_intervention", "resume PDF is missing; prepare documents first")

        try:
            resolved = resolve_credentials("smtp")
        except CredentialError as exc:
            return AdapterOutcome("failed", f"credential configuration error: {exc}")
        external = dict(resolved.values) if resolved else {}

        def setting(name: str, env_name: str, default=""):
            value = external.get(name)
            return value if value not in (None, "") else os.getenv(env_name, default)

        message = EmailMessage()
        title, company = ctx.job.get("title", "the role"), ctx.job.get("company", "")
        message["Subject"] = f"Application for {title}" + (f" at {company}" if company else "")
        message["To"] = ctx.to_email
        message["From"] = str(setting("from_address", "SMTP_FROM_ADDRESS") or setting("username", "SMTP_USERNAME") or ctx.contact.get("email", ""))
        message["Message-ID"] = make_msgid()
        message.set_content(ctx.cover_letter or "Please find my application attached.")
        message.add_attachment(resume.read_bytes(), maintype="application", subtype="pdf", filename="resume.pdf")

        if not ctx.live or os.getenv(LIVE_ENV_FLAG, "0") != "1":
            return AdapterOutcome(
                "manual_intervention",
                f"dry run: application email to {ctx.to_email} prepared but NOT sent "
                f"(set {LIVE_ENV_FLAG}=1 and pass live=true to send)",
                evidence=[("email_draft", str(message)[:20_000])],
            )

        host = str(setting("host", "SMTP_HOST"))
        username = str(setting("username", "SMTP_USERNAME"))
        password = str(setting("password", "SMTP_PASSWORD"))
        try:
            port = int(setting("port", "SMTP_PORT", "587"))
        except (TypeError, ValueError):
            return AdapterOutcome("failed", "SMTP port must be an integer")
        if not 1 <= port <= 65535:
            return AdapterOutcome("failed", "SMTP port must be between 1 and 65535")
        if not host or not username or not password:
            return AdapterOutcome(
                "failed",
                "SMTP is not configured; add smtp/default to the external credential file or set the SMTP_* compatibility variables",
            )
        try:
            raw_tls = setting("use_tls", "SMTP_USE_TLS", "1")
            use_tls = raw_tls if isinstance(raw_tls, bool) else str(raw_tls).strip().lower() in {"1", "true", "yes", "on"}
            if use_tls:
                with smtplib.SMTP(host, port, timeout=30) as server:
                    server.starttls()
                    server.login(username, password)
                    server.send_message(message)
            else:
                with smtplib.SMTP_SSL(host, port, timeout=30) as server:
                    server.login(username, password)
                    server.send_message(message)
        except Exception as exc:  # noqa: BLE001 — any transport failure is a clean "failed"
            return AdapterOutcome("failed", f"SMTP send failed: {exc}")
        return AdapterOutcome(
            "submitted",
            f"application emailed to {ctx.to_email}",
            evidence=[
                ("smtp_message_id", str(message["Message-ID"])),
                ("email_copy", str(message)[:20_000]),
            ],
        )
JOB_SNIFFING_CREDENTIALS_V1_3

mkdir -p "$(dirname 'app/services/credential_service.py')"
cat > 'app/services/credential_service.py' <<'JOB_SNIFFING_CREDENTIALS_V1_4'
"""External, file-backed credentials for submission adapters.

Credentials are intentionally kept outside the repository and SQLite. The
loader accepts a small JSON document owned by the current user, requires
owner-only permissions on POSIX, and returns secrets only to the adapter that
requested them. Diagnostic summaries contain provider/profile names only.
"""
from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

from app.config import PROJECT_ROOT

CREDENTIALS_ENV = "JOBSNIFFING_CREDENTIALS_FILE"
DEFAULT_CREDENTIALS_PATH = Path("~/.config/jobsniffing/credentials.json").expanduser()
MAX_CREDENTIAL_FILE_BYTES = 64 * 1024
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,119}$")
_ALLOWED_VALUE_TYPES = (str, int, bool, type(None))


class CredentialError(RuntimeError):
    """Safe configuration error that never includes credential values."""


@dataclass(frozen=True)
class CredentialResolution:
    provider: str
    profile: str
    values: Mapping[str, str | int | bool | None]
    source_path: Path


def _normalise_name(value: str, *, label: str) -> str:
    cleaned = value.strip().lower()
    if not _NAME_RE.fullmatch(cleaned):
        raise CredentialError(f"invalid {label} name; use lowercase letters, numbers, dots, dashes, or underscores")
    return cleaned


def _configured_path() -> tuple[Path, bool]:
    raw = os.getenv(CREDENTIALS_ENV, "").strip()
    path = Path(raw).expanduser() if raw else DEFAULT_CREDENTIALS_PATH
    return path.resolve(), bool(raw)


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _validate_path(path: Path, *, explicitly_configured: bool) -> bool:
    if _is_within(path, PROJECT_ROOT):
        raise CredentialError(
            f"credential file must live outside the repository; move it to {DEFAULT_CREDENTIALS_PATH}"
        )
    if not path.exists():
        if explicitly_configured:
            raise CredentialError(f"credential file does not exist: {path}")
        return False
    if not path.is_file():
        raise CredentialError("credential path must point to a regular file")
    info = path.stat()
    if info.st_size > MAX_CREDENTIAL_FILE_BYTES:
        raise CredentialError(f"credential file exceeds {MAX_CREDENTIAL_FILE_BYTES} bytes")
    if os.name == "posix":
        mode = stat.S_IMODE(info.st_mode)
        if mode & 0o077:
            raise CredentialError(f"credential file permissions are too broad; run: chmod 600 {path}")
        getuid = getattr(os, "getuid", None)
        if getuid is not None and info.st_uid != getuid():
            raise CredentialError("credential file must be owned by the current user")
    return True


def _validate_document(payload: Any) -> dict[str, dict[str, dict[str, str | int | bool | None]]]:
    if not isinstance(payload, dict):
        raise CredentialError("credential file root must be a JSON object")
    if payload.get("version") != 1:
        raise CredentialError("credential file version must be 1")
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise CredentialError("credential file must contain a providers object")

    validated: dict[str, dict[str, dict[str, str | int | bool | None]]] = {}
    for raw_provider, raw_profiles in providers.items():
        if not isinstance(raw_provider, str):
            raise CredentialError("credential provider names must be strings")
        provider = _normalise_name(raw_provider, label="provider")
        if not isinstance(raw_profiles, dict):
            raise CredentialError(f"credential provider '{provider}' must contain profile objects")
        profiles: dict[str, dict[str, str | int | bool | None]] = {}
        for raw_profile, raw_values in raw_profiles.items():
            if not isinstance(raw_profile, str):
                raise CredentialError(f"credential profiles for '{provider}' must use string names")
            profile = _normalise_name(raw_profile, label="profile")
            if not isinstance(raw_values, dict):
                raise CredentialError(f"credential profile '{provider}/{profile}' must be an object")
            values: dict[str, str | int | bool | None] = {}
            for raw_key, value in raw_values.items():
                if not isinstance(raw_key, str):
                    raise CredentialError(f"credential keys for '{provider}/{profile}' must be strings")
                key = _normalise_name(raw_key, label="credential key")
                if not isinstance(value, _ALLOWED_VALUE_TYPES):
                    raise CredentialError(
                        f"credential value '{provider}/{profile}/{key}' must be a string, number, boolean, or null"
                    )
                values[key] = value
            profiles[profile] = values
        validated[provider] = profiles
    return validated


def load_credential_store() -> tuple[Path | None, dict[str, dict[str, dict[str, str | int | bool | None]]]]:
    """Load and validate the external store.

    The default path is optional so fresh installations can run discovery and
    preparation without credentials. An explicitly configured missing or
    invalid path fails closed.
    """
    path, explicit = _configured_path()
    if not _validate_path(path, explicitly_configured=explicit):
        return None, {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CredentialError(f"credential file is invalid JSON at line {exc.lineno}, column {exc.colno}") from exc
    except OSError as exc:
        raise CredentialError(f"credential file could not be read: {exc.strerror or type(exc).__name__}") from exc
    return path, _validate_document(payload)


def resolve_credentials(
    provider: str,
    *,
    profile_candidates: tuple[str, ...] | list[str] = (),
    required: bool = False,
) -> CredentialResolution | None:
    """Resolve the first matching profile, then fall back to ``default``."""
    provider_name = _normalise_name(provider, label="provider")
    path, store = load_credential_store()
    profiles = store.get(provider_name, {})
    candidates: list[str] = []
    for raw in [*profile_candidates, "default"]:
        if not raw:
            continue
        try:
            name = _normalise_name(str(raw), label="profile")
        except CredentialError:
            continue
        if name not in candidates:
            candidates.append(name)
    for profile in candidates:
        if profile in profiles and path is not None:
            return CredentialResolution(provider_name, profile, dict(profiles[profile]), path)
    if required:
        wanted = ", ".join(candidates) or "default"
        raise CredentialError(f"no credential profile found for provider '{provider_name}' (tried: {wanted})")
    return None


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9._-]+", "-", value.strip().lower()).strip("-._")[:120]


def job_profile_candidates(job: Mapping[str, Any]) -> tuple[str, ...]:
    """Return non-secret profile hints for a job, strongest match first."""
    candidates: list[str] = []
    explicit = _slug(str(job.get("credential_profile", "")))
    if explicit:
        candidates.append(explicit)
    host = (urlparse(str(job.get("apply_url", ""))).hostname or "").lower()
    if host and _NAME_RE.fullmatch(host):
        candidates.append(host)
    company = _slug(str(job.get("company", "")))
    if company:
        candidates.append(company)
    return tuple(dict.fromkeys(candidates))


def resolve_job_credentials(
    provider: str,
    job: Mapping[str, Any],
    *,
    required: bool = False,
) -> CredentialResolution | None:
    return resolve_credentials(provider, profile_candidates=job_profile_candidates(job), required=required)


def credential_status() -> dict[str, Any]:
    """Return a safe summary containing no keys or values from any profile."""
    path, store = load_credential_store()
    return {
        "configured": path is not None,
        "path": _display_path(path) if path else None,
        "providers": {provider: sorted(profiles) for provider, profiles in sorted(store.items())},
    }


def _display_path(path: Path | None) -> str | None:
    if path is None:
        return None
    home = Path.home().resolve()
    try:
        return str(Path("~") / path.resolve().relative_to(home))
    except ValueError:
        return str(path)
JOB_SNIFFING_CREDENTIALS_V1_4

mkdir -p "$(dirname 'docs/SPRINT_HANDOFF.md')"
cat > 'docs/SPRINT_HANDOFF.md' <<'JOB_SNIFFING_CREDENTIALS_V1_5'
# Autonomy Sprint Handoff

**Working branch:** `autonomy/shared-primitives-v1`  
**Canonical base:** Sonnet/Fable `consolidation-v1`, not the older source previously visible on `main`.

## Mission

Continue JobSniffing toward reliable in-scope autonomy without rebuilding the consolidation layer or weakening its safety invariants.

## Locked safety lines

- CAPTCHA, reCAPTCHA, hCaptcha, Turnstile, and generic anti-bot challenges always route to `manual_intervention_required`. Never solve or bypass them.
- 2FA/MFA and verification codes always route to the user.
- HireVue, HackerRank, Codility, personality, cognitive, and similar assessments always route to the user. Never answer an employer assessment autonomously.
- Legal declarations and demographic self-identification require explicit human attestation.
- Government portals remain discovery, preparation, and manual-submit only.
- `submitted` requires stored confirmation-kind evidence.
- Unknown answers remain unknown. Never fabricate qualifications, dates, education, certifications, or experience.
- Live submission remains blocked unless `JOBSNIFFING_ALLOW_LIVE_SUBMISSION=1` and all non-bypassable gates pass.

## Completed

### Shared browser primitives

- `dom_kit.py`: accessible label matching, conservative fuzzy matching, text/select/radio/checkbox support, question extraction, options, and required-state detection.
- `handoff.py`: common anti-bot, 2FA/MFA, and assessment detection with explicit reasons.
- `confirmation.py`: confirmation text, confirmation URL, application/reference ID, and weak-signal handling. Form disappearance alone is not proof.
- `browser_form.py`: reusable single-page ATS engine with screenshots, dry-run previews, verified-answer filling, question extraction, fail-closed submission, and evidence.

### Two-pass preparation

- `POST /api/jobs/{id}/inspect` runs an adapter with no submit click.
- First pass extracts real form questions and stores them through the question engine.
- Second pass fills only verified or explicitly approved answers.
- Empty custom-question forms become answer-ready only when browser evidence records `[]`.

### Submission adapters

- Greenhouse refactored onto the shared engine.
- Lever implemented on the same engine.
- Ashby implemented on the same engine.
- All three support dry-run inspection and evidence-gated live submission.
- Live Chromium verification is still required on the user's Android Ubuntu proot.

### External credentials

- `credential_service.py` loads versioned provider/profile JSON from a user-owned file outside the repository.
- Default path: `~/.config/jobsniffing/credentials.json`; override with `JOBSNIFFING_CREDENTIALS_FILE`.
- Repository-local files, insecure POSIX permissions, wrong ownership, oversized files, invalid schemas, and nested values fail closed.
- No credential keys or values are exposed by diagnostics. No secrets enter SQLite, evidence, screenshots, logs, or Git.
- SMTP prefers `smtp/default`; legacy `SMTP_*` variables remain compatibility-only.
- `scripts/init-credentials.sh` creates an owner-only starter file.

### Local unattended operation

- SQLite migration v3 adds persistent `discovery_targets`.
- Scheduler runs due Greenhouse, Lever, and Ashby board scans.
- Score-qualified jobs advance through factual document preparation.
- Browser inspection can run during scheduler cycles.
- Default release policy is `batch_confirm`: jobs stop at `ready_for_review` for one-tap daily release.
- Optional `immediate` policy exists, but still requires autonomous mode, explicit scope, the live environment gate, daily caps, delays, factual documents, approved answers, and confirmation evidence.
- `python -m app.autonomy_loop` and `scripts/autonomy-loop.sh` run locally without Redis, Celery, Docker, or a cloud daemon.

## Verification

```sh
sh scripts/verify.sh
```

Current result: **99 tests passing**, plus live server, HTTP smoke, default-mode, and temporary SQLite verification.

## Exact next task

Build the shared multi-page wizard engine. Preserve the external credential service and use it rather than adding adapter-specific secret handling.

1. Add bounded step traversal with explicit maximum-step and repeated-page protection.
2. Detect next, continue, save-and-continue, back, review, and final-submit controls without confusing final submission with navigation.
3. Extract and prepare questions on every step, including fields inside iframes.
4. Capture screenshots and redacted step metadata before and after every navigation.
5. Detect autosave signals and recoverable validation errors.
6. Stop for CAPTCHA, MFA, assessments, legal declarations, demographic self-ID, unknown required questions, and unexpected account walls.
7. Add Page-shaped fake tests before implementing Taleo.

Do not build Taleo until this shared wizard layer is green and adapter-neutral.

## Device verification commands

```sh
pip install '.[automation]'
playwright install chromium
JOBSNIFFING_PLAYWRIGHT_HEADLESS=0 sh scripts/termux-run.sh
```

For each ATS, run one job with `live=false`, inspect every screenshot and `field_fill_report`, then use `live=true` only after all visible values are correct.
JOB_SNIFFING_CREDENTIALS_V1_5

mkdir -p "$(dirname 'docs/credentials.md')"
cat > 'docs/credentials.md' <<'JOB_SNIFFING_CREDENTIALS_V1_6'
# External credentials

JobSniffing reads credentials from a user-owned JSON file outside the repository. Credentials are never written to SQLite, logs, evidence records, screenshots, exports, or Git.

## Create the file

```sh
sh scripts/init-credentials.sh
```

Default location:

```text
~/.config/jobsniffing/credentials.json
```

Override the location only when needed:

```sh
export JOBSNIFFING_CREDENTIALS_FILE="$HOME/private/jobsniffing-credentials.json"
```

The loader rejects files inside the JobSniffing repository. On Android, Termux, Linux, and Ubuntu proot, the file must belong to the current user and must not be readable by the group or other users:

```sh
chmod 600 ~/.config/jobsniffing/credentials.json
```

## Schema

```json
{
  "version": 1,
  "providers": {
    "smtp": {
      "default": {
        "host": "smtp.example.com",
        "port": 587,
        "username": "you@example.com",
        "password": "APP-SPECIFIC-PASSWORD",
        "from_address": "you@example.com",
        "use_tls": true
      }
    },
    "workday": {
      "bank-name": {
        "username": "you@example.com",
        "password": "ACCOUNT-PASSWORD"
      },
      "default": {
        "username": "fallback@example.com",
        "password": "FALLBACK-PASSWORD"
      }
    }
  }
}
```

Providers contain named profiles. Future login-based adapters resolve profiles in this order:

1. An explicit credential profile attached to the job
2. The application hostname
3. A normalized company name
4. `default`

For example, a Workday application for `Example Bank` may use a profile named `example-bank`, the exact Workday hostname, or `default`.

## Safety behaviour

The loader fails closed when:

- An explicitly configured file is missing
- The file is inside the repository
- POSIX permissions permit group or other access
- The file belongs to another user
- The file exceeds 64 KiB
- The JSON structure or version is invalid
- A credential value is a nested object or array

Diagnostic status contains only provider and profile names. Credential keys and values are never returned.

## SMTP compatibility

The email adapter now prefers the external `smtp/default` profile. Existing `SMTP_*` environment variables remain as a compatibility fallback, but the external owner-only file is the recommended configuration.
JOB_SNIFFING_CREDENTIALS_V1_6

mkdir -p "$(dirname 'scripts/init-credentials.sh')"
cat > 'scripts/init-credentials.sh' <<'JOB_SNIFFING_CREDENTIALS_V1_7'
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
JOB_SNIFFING_CREDENTIALS_V1_7

mkdir -p "$(dirname 'tests/unit/test_credentials.py')"
cat > 'tests/unit/test_credentials.py' <<'JOB_SNIFFING_CREDENTIALS_V1_8'
import json
import os
from pathlib import Path

import pytest

from app.services import credential_service as credentials


def write_store(path: Path, providers: dict, mode: int = 0o600) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"version": 1, "providers": providers}), encoding="utf-8")
    path.chmod(mode)
    return path


def test_missing_default_store_is_optional(monkeypatch, tmp_path):
    monkeypatch.delenv(credentials.CREDENTIALS_ENV, raising=False)
    monkeypatch.setattr(credentials, "DEFAULT_CREDENTIALS_PATH", tmp_path / "missing.json")
    assert credentials.load_credential_store() == (None, {})
    assert credentials.resolve_credentials("smtp") is None


def test_explicit_missing_store_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv(credentials.CREDENTIALS_ENV, str(tmp_path / "missing.json"))
    with pytest.raises(credentials.CredentialError, match="does not exist"):
        credentials.load_credential_store()


def test_repository_local_store_is_rejected(monkeypatch, tmp_path):
    repo = tmp_path / "repo"
    path = write_store(repo / "credentials.json", {})
    monkeypatch.setattr(credentials, "PROJECT_ROOT", repo)
    monkeypatch.setenv(credentials.CREDENTIALS_ENV, str(path))
    with pytest.raises(credentials.CredentialError, match="outside the repository"):
        credentials.load_credential_store()


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission check")
def test_group_readable_store_is_rejected(monkeypatch, tmp_path):
    path = write_store(tmp_path / "credentials.json", {}, mode=0o640)
    monkeypatch.setenv(credentials.CREDENTIALS_ENV, str(path))
    with pytest.raises(credentials.CredentialError, match="chmod 600"):
        credentials.load_credential_store()


def test_profile_resolution_prefers_candidate_then_default(monkeypatch, tmp_path):
    path = write_store(tmp_path / "credentials.json", {
        "workday": {
            "default": {"username": "fallback", "password": "fallback-secret"},
            "example-bank": {"username": "specific", "password": "specific-secret"},
        }
    })
    monkeypatch.setenv(credentials.CREDENTIALS_ENV, str(path))
    resolved = credentials.resolve_credentials("workday", profile_candidates=["example-bank"])
    assert resolved and resolved.profile == "example-bank"
    assert resolved.values["username"] == "specific"
    status = credentials.credential_status()
    assert status["providers"] == {"workday": ["default", "example-bank"]}
    assert "specific-secret" not in json.dumps(status)
    assert "password" not in json.dumps(status)


def test_job_profile_candidates_use_host_then_company(monkeypatch, tmp_path):
    path = write_store(tmp_path / "credentials.json", {
        "workday": {
            "example.myworkdayjobs.com": {"username": "host-user"},
            "example-bank": {"username": "company-user"},
        }
    })
    monkeypatch.setenv(credentials.CREDENTIALS_ENV, str(path))
    job = {"company": "Example Bank", "apply_url": "https://example.myworkdayjobs.com/en-US/jobs/1"}
    resolved = credentials.resolve_job_credentials("workday", job)
    assert resolved and resolved.profile == "example.myworkdayjobs.com"
    assert resolved.values["username"] == "host-user"


def test_nested_credential_values_are_rejected(monkeypatch, tmp_path):
    path = write_store(tmp_path / "credentials.json", {
        "smtp": {"default": {"password": {"nested": "not allowed"}}}
    })
    monkeypatch.setenv(credentials.CREDENTIALS_ENV, str(path))
    with pytest.raises(credentials.CredentialError, match="string, number, boolean, or null"):
        credentials.load_credential_store()


def test_required_profile_reports_names_not_values(monkeypatch, tmp_path):
    path = write_store(tmp_path / "credentials.json", {"smtp": {"other": {"password": "top-secret"}}})
    monkeypatch.setenv(credentials.CREDENTIALS_ENV, str(path))
    with pytest.raises(credentials.CredentialError) as caught:
        credentials.resolve_credentials("workday", profile_candidates=["bank"], required=True)
    assert "top-secret" not in str(caught.value)
JOB_SNIFFING_CREDENTIALS_V1_8

mkdir -p "$(dirname 'tests/unit/test_email_adapter.py')"
cat > 'tests/unit/test_email_adapter.py' <<'JOB_SNIFFING_CREDENTIALS_V1_9'
import smtplib
from app.adapters.submit.base import AdapterInput
from app.adapters.submit.email_smtp import EmailSmtpAdapter


def ctx(tmp_path, **overrides):
    pdf = tmp_path / "resume.pdf"; pdf.write_bytes(b"%PDF-1.4 fake")
    defaults = dict(job={"title": "Fraud Analyst", "company": "Bank"}, contact={"name": "M. Alem"},
                    resume_pdf=str(pdf), cover_letter="Dear team", to_email="hr@example.com", live=False)
    defaults.update(overrides)
    return AdapterInput(**defaults)


def test_dry_run_prepares_but_never_sends(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(smtplib, "SMTP", lambda *a, **k: called.append(a))
    outcome = EmailSmtpAdapter().run(ctx(tmp_path))
    assert outcome.result == "manual_intervention" and "not sent" in outcome.message.lower()
    assert outcome.evidence[0][0] == "email_draft" and not called


def test_env_gate_blocks_even_with_live_flag(tmp_path, monkeypatch):
    monkeypatch.delenv("JOBSNIFFING_ALLOW_LIVE_SUBMISSION", raising=False)
    outcome = EmailSmtpAdapter().run(ctx(tmp_path, live=True))
    assert outcome.result == "manual_intervention"


def test_missing_destination_or_resume_goes_manual(tmp_path):
    assert EmailSmtpAdapter().run(ctx(tmp_path, to_email=None)).result == "manual_intervention"
    assert EmailSmtpAdapter().run(ctx(tmp_path, resume_pdf="/nope.pdf")).result == "manual_intervention"


def test_live_send_records_message_id_evidence(tmp_path, monkeypatch):
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=30): sent["host"] = host
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def starttls(self): sent["tls"] = True
        def login(self, user, password): sent["user"] = user
        def send_message(self, message): sent["message_id"] = message["Message-ID"]

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    for key, value in {"JOBSNIFFING_ALLOW_LIVE_SUBMISSION": "1", "SMTP_HOST": "smtp.example.com",
                       "SMTP_USERNAME": "u", "SMTP_PASSWORD": "p"}.items():
        monkeypatch.setenv(key, value)
    outcome = EmailSmtpAdapter().run(ctx(tmp_path, live=True))
    assert outcome.result == "submitted"
    kinds = dict(outcome.evidence)
    assert kinds["smtp_message_id"] == sent["message_id"] and "email_copy" in kinds


def test_smtp_failure_is_failed_not_submitted(tmp_path, monkeypatch):
    class Boom:
        def __init__(self, *a, **k): raise OSError("connection refused")
    monkeypatch.setattr(smtplib, "SMTP", Boom)
    for key, value in {"JOBSNIFFING_ALLOW_LIVE_SUBMISSION": "1", "SMTP_HOST": "smtp.example.com",
                       "SMTP_USERNAME": "u", "SMTP_PASSWORD": "p"}.items():
        monkeypatch.setenv(key, value)
    outcome = EmailSmtpAdapter().run(ctx(tmp_path, live=True))
    assert outcome.result == "failed" and "connection refused" in outcome.message


def test_external_credential_file_is_preferred(tmp_path, monkeypatch):
    import json
    credential_file = tmp_path / "credentials.json"
    credential_file.write_text(json.dumps({
        "version": 1,
        "providers": {"smtp": {"default": {
            "host": "external.example.com", "port": 2525,
            "username": "external-user", "password": "external-secret",
            "from_address": "from@example.com", "use_tls": True,
        }}},
    }))
    credential_file.chmod(0o600)
    monkeypatch.setenv("JOBSNIFFING_CREDENTIALS_FILE", str(credential_file))
    monkeypatch.setenv("JOBSNIFFING_ALLOW_LIVE_SUBMISSION", "1")
    monkeypatch.setenv("SMTP_HOST", "wrong.example.com")
    sent = {}

    class FakeSMTP:
        def __init__(self, host, port, timeout=30): sent.update(host=host, port=port)
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def starttls(self): sent["tls"] = True
        def login(self, user, password): sent.update(user=user, password=password)
        def send_message(self, message): sent["from"] = message["From"]

    monkeypatch.setattr(smtplib, "SMTP", FakeSMTP)
    outcome = EmailSmtpAdapter().run(ctx(tmp_path, live=True))
    assert outcome.result == "submitted"
    assert sent == {
        "host": "external.example.com", "port": 2525, "tls": True,
        "user": "external-user", "password": "external-secret", "from": "from@example.com",
    }


def test_invalid_external_credentials_fail_without_leaking_secret(tmp_path, monkeypatch):
    import json
    credential_file = tmp_path / "credentials.json"
    credential_file.write_text(json.dumps({
        "version": 1,
        "providers": {"smtp": {"default": {"password": {"secret": "do-not-leak"}}}},
    }))
    credential_file.chmod(0o600)
    monkeypatch.setenv("JOBSNIFFING_CREDENTIALS_FILE", str(credential_file))
    outcome = EmailSmtpAdapter().run(ctx(tmp_path))
    assert outcome.result == "failed"
    assert "do-not-leak" not in outcome.message
JOB_SNIFFING_CREDENTIALS_V1_9

chmod +x scripts/init-credentials.sh
echo "Applied external credential loader overlay."
