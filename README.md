# JobSniffing

JobSniffing is an Android-first, local-first job discovery and review queue. It collects published jobs from supported public applicant-tracking-system APIs, scores them locally, stores them in SQLite, and keeps every application behind an explicit human-review workflow.

**Version 0.2.0 is ready for local job discovery and tracking. It does not submit applications.**

## What works

- FastAPI backend and mobile-friendly browser dashboard
- SQLite storage with safe transactions, WAL mode, and duplicate protection
- Live public job discovery for Greenhouse, Lever, and Ashby boards
- Manual job entry
- Deterministic local scoring with no paid API or model
- Strict, review-gated status transitions
- Android/Termux and Ubuntu via PRoot-Distro launch scripts
- Automated unit, contract, API integration, startup, and health verification
- GitHub Actions tests on Python 3.11, 3.12, and 3.13

## Safety boundary

JobSniffing never performs browser stealth, CAPTCHA bypass, credential harvesting, or automatic application submission. The final `submitted` status can only be reached through the explicit state machine after a filling step. Version 0.2.0 offers tracking and manual handoff only.

## Fastest setup: native Termux

Install a current Termux build from F-Droid or the official Termux GitHub releases. Do not mix Termux and plugin APKs from different sources.

```sh
pkg update -y
pkg install -y git
git clone https://github.com/TheHighBrid/JobSniffing.git
cd JobSniffing
./scripts/termux-bootstrap.sh
./scripts/verify.sh
./scripts/termux-run.sh
```

Open this address in the Android browser:

```text
http://127.0.0.1:8010
```

Stop the server with `Ctrl+C`.

## Ubuntu via PRoot-Distro

This route keeps a separate Ubuntu Python environment while sharing the same repository with Termux. The scripts use `.venv-termux` and `.venv-ubuntu`, so both environments can coexist without corrupting each other.

Run in Termux:

```sh
pkg update -y
pkg install -y git proot-distro
git clone https://github.com/TheHighBrid/JobSniffing.git
proot-distro install ubuntu:24.04
proot-distro login ubuntu --shared-home
```

Then run inside Ubuntu:

```sh
cd /root/JobSniffing
./scripts/ubuntu-bootstrap.sh
./scripts/verify.sh
./scripts/ubuntu-run.sh
```

Open `http://127.0.0.1:8010` in the Android browser. Do not run the Termux server and Ubuntu server at the same time against the same database.

## Daily use

Start the native Termux build:

```sh
cd ~/JobSniffing
./scripts/termux-run.sh
```

Or start the Ubuntu build:

```sh
proot-distro login ubuntu --shared-home
cd /root/JobSniffing
./scripts/ubuntu-run.sh
```

The dashboard lets you:

1. Scan a Greenhouse, Lever, or Ashby public board.
2. Add a job manually.
3. Open the original application page.
4. Move a job through allowed review states.
5. Add notes during a status change.

Interactive API documentation is available at `http://127.0.0.1:8010/docs`.

## Finding a board token

The board token is the company-specific slug used by its ATS:

- Greenhouse: the token in a board URL such as `boards.greenhouse.io/<token>`.
- Lever: the token in a jobs URL such as `jobs.lever.co/<token>`.
- Ashby: the token in a jobs URL such as `jobs.ashbyhq.com/<token>`.

Only letters, numbers, periods, underscores, and hyphens are accepted. This prevents a board value from changing the fixed upstream API host or path structure.

## API examples

Health check:

```sh
curl -fsS http://127.0.0.1:8010/health
```

Add one job:

```sh
curl -fsS -X POST http://127.0.0.1:8010/api/jobs \
  -H 'content-type: application/json' \
  -d '{
    "source":"manual",
    "external_id":"example-1",
    "title":"Android FastAPI Engineer",
    "company":"Example Company",
    "location":"Remote",
    "apply_url":"https://example.com/apply",
    "description":"Python, FastAPI, SQLite, Android"
  }'
```

Scan a public board after replacing the token and label:

```sh
curl -fsS -X POST http://127.0.0.1:8010/api/discovery/scan \
  -H 'content-type: application/json' \
  -d '{"source":"greenhouse","board":"company-token","company":"Company Name"}'
```

List shortlisted jobs:

```sh
curl -fsS 'http://127.0.0.1:8010/api/jobs?status=shortlisted&min_score=1'
```

Change a job status, replacing `1` with its ID:

```sh
curl -fsS -X POST http://127.0.0.1:8010/api/jobs/1/status \
  -H 'content-type: application/json' \
  -d '{"status":"shortlisted","notes":"Strong Android and Python match"}'
```

## Status workflow

```text
discovered -> scored -> shortlisted -> approved -> queued -> filling
                                                     |          |
                                                     |          +-> submitted
                                                     |          +-> needs_review
                                                     |          +-> failed
                                                     +-> blocked
```

The API returns `409 Conflict` when a requested transition is not permitted. `submitted` and `blocked` are terminal.

## Verification

Run the complete local verification command from the repository root:

```sh
./scripts/verify.sh
```

It performs:

- Python bytecode compilation
- all unit, contract, and integration tests
- a real Uvicorn startup on an isolated port
- a real `/health` request
- cleanup of the temporary server and database

Run only the tests:

```sh
. .venv-termux/bin/activate   # native Termux
# or: . .venv-ubuntu/bin/activate
python -m pytest -q
```

## Data and backup

The default database is:

```text
data/jobsniffing.sqlite3
```

Stop the server before copying the database:

```sh
cp data/jobsniffing.sqlite3 "$HOME/jobsniffing-backup.sqlite3"
```

Use another location for one run:

```sh
JOBSNIFFING_DB="$HOME/my-jobs.sqlite3" ./scripts/termux-run.sh
```

## Updating

Stop the server, then run:

```sh
cd ~/JobSniffing
git pull --ff-only
./scripts/termux-bootstrap.sh
./scripts/verify.sh
```

Inside Ubuntu, use the same flow with `./scripts/ubuntu-bootstrap.sh`.

## Troubleshooting

**`pkg` repository errors**

```sh
termux-change-repo
pkg upgrade -y
```

Choose a working main mirror, then retry the bootstrap script.

**Port 8010 is already in use**

```sh
PORT=8011 ./scripts/termux-run.sh
```

Then open `http://127.0.0.1:8011`.

**The server exits while Android is in the background**

Disable battery optimization for Termux. Android may stop long-running or CPU-heavy processes, especially on Android 12 and newer.

**Reset only the Python environment**

Native Termux:

```sh
rm -rf .venv-termux
./scripts/termux-bootstrap.sh
```

Ubuntu:

```sh
rm -rf .venv-ubuntu
./scripts/ubuntu-bootstrap.sh
```

Do not delete `data/` unless you also intend to delete the tracked jobs.

## Project layout

```text
app/
  adapters/discovery/   ATS payload normalization
  db/                   SQLite connection and schema
  domain/               validation and state machine
  services/             discovery, scoring, and tracking
  web/                  mobile-friendly dashboard
scripts/                 Termux, Ubuntu, health, and verification commands
tests/                   unit, contract, and API integration tests
docs/                    architecture, API, audit, and environment guides
```

## More documentation

- [Android, Termux, and Ubuntu guide](docs/termux.md)
- [API contract](docs/api-contract.md)
- [Architecture](docs/architecture.md)
- [Status machine](docs/status-machine.md)
- [Audit and reference-repository findings](docs/audit.md)
