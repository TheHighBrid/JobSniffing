# JobSniffing

JobSniffing is an Android-first, local-first job discovery and human review queue. It runs as one FastAPI process with one SQLite file and a mobile-friendly dashboard.

> **Public ATS APIs first, browser automation last, human approval before every real application.**

## What is ready

- Live discovery from Greenhouse, Lever, and Ashby public boards.
- Manual entry and JSON bulk import.
- Offline scoring with editable weighted terms.
- Defaults tuned for bilingual banking, fraud, AML/KYC, compliance, risk, government, Ottawa/Gatineau, and remote-Canada searches.
- Negative-term penalties and company blocking.
- Strict status transitions with preparation, confirmation, verification-failure, manual-intervention, withdrawal, and proper 404, 409, and 422 responses.
- Mobile dashboard for filters, review, status changes, deletion, opening applications, and the visible manual/assisted/auto mode switch.
- SQLite deduplication, rescoring, CSV export, diagnostics, and OpenAPI docs.
- Ubuntu/proot and native Termux bootstrap scripts.
- No Redis, Celery, Docker, paid AI key, cloud database, or browser driver.
- Real submission remains manual and is never falsely reported.

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

JobSniffing discovers, scores, prepares, and tracks. The default mode is `manual`, `assisted` requires human confirmation, and `auto` is reserved for capped, adapter-gated submission paths. It does not attempt universal auto-submission. A future submission adapter must be site-specific, dry-run-first, obey local safety guardrails, and should move through `awaiting_confirmation` before the state becomes `submitted`.

- [Detailed Android, Termux, and Ubuntu guide](docs/termux.md)
- [Audit and readiness report](docs/audit.md)
- [Architecture](docs/architecture.md)
- [API contract](docs/api-contract.md)
- [Status machine](docs/status-machine.md)
