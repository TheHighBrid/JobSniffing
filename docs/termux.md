# Android, Termux, and Ubuntu 24.04 via PRoot-Distro

This is the supported Android installation guide for JobSniffing 0.2.0. The Python tests, editable installation, Uvicorn startup, `/health` response, and dashboard rendering were verified in a Linux runtime. The Termux and PRoot-Distro commands were checked against official documentation. A physical Android handset was not available in the audit environment, so battery-management behavior remains device-specific.

## Choose a runtime

**Ubuntu 24.04 through PRoot-Distro is recommended.** It provides a conventional Linux userspace and normally has the most predictable Python package installation on Android.

**Native Termux is supported** and uses less storage. Use one runtime for a repository checkout, and do not start both servers against the same SQLite database at the same time.

## Requirements

- A current Termux build from F-Droid or the official Termux GitHub releases
- Android 7 or newer for current Termux packages
- Internet access during installation and ATS scans
- Enough free storage for Ubuntu when using PRoot-Distro

Keep Termux and any Termux plugin APKs from the same distribution source because their signatures must match.

## Recommended installation: Ubuntu 24.04 via PRoot-Distro

### 1. Install Ubuntu from Termux

```sh
pkg update -y
pkg install -y proot-distro
proot-distro install ubuntu:24.04
proot-distro login ubuntu
```

### 2. Clone and bootstrap inside Ubuntu

```sh
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git ca-certificates
cd /root
git clone https://github.com/TheHighBrid/JobSniffing.git
cd JobSniffing
./scripts/ubuntu-bootstrap.sh
```

The bootstrap installs Python only when needed, creates `.venv`, installs JobSniffing and its test dependencies, runs the full test suite, starts a temporary Uvicorn server, and verifies a real health request.

### 3. Start JobSniffing

```sh
./scripts/termux-run.sh
```

Open `http://127.0.0.1:8010` in the Android browser. Keep the Termux session open. Stop the server with `Ctrl+C`.

## Native Termux installation

```sh
pkg update -y
pkg install -y git
git clone https://github.com/TheHighBrid/JobSniffing.git
cd JobSniffing
./scripts/termux-bootstrap.sh
./scripts/termux-run.sh
```

Open `http://127.0.0.1:8010` in the Android browser.

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

## Verify after an update

The bootstrap scripts already run verification. For a later check without rebuilding the environment:

```sh
cd /root/JobSniffing
./scripts/verify.sh
```

For native Termux, use `cd ~/JobSniffing` first. The verifier runs the Python tests, starts Uvicorn on an isolated port with a temporary SQLite database, requests `/health`, and shuts the temporary server down.

## Update without losing data

Stop the server first.

Ubuntu route:

```sh
proot-distro login ubuntu
cd /root/JobSniffing
git pull --ff-only
./scripts/ubuntu-bootstrap.sh
```

Native Termux route:

```sh
cd ~/JobSniffing
git pull --ff-only
./scripts/termux-bootstrap.sh
```

Neither bootstrap script deletes `data/jobsniffing.sqlite3`.

## Configuration

The run script reads an optional `.env` file from the repository root:

```sh
cp .env.example .env
```

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Listen address |
| `PORT` | `8010` | HTTP port |
| `JOBSNIFFING_DB` | `data/jobsniffing.sqlite3` | SQLite database path |

Keep `HOST=127.0.0.1`. Version 0.2.0 is a same-device application and does not include network authentication.

Use another port for one launch:

```sh
PORT=8011 ./scripts/termux-run.sh
```

Then open `http://127.0.0.1:8011`.

## Health and useful addresses

```sh
curl -fsS http://127.0.0.1:8010/health
```

- Dashboard: `http://127.0.0.1:8010`
- Health: `http://127.0.0.1:8010/health`
- OpenAPI documentation: `http://127.0.0.1:8010/docs`
- Jobs JSON: `http://127.0.0.1:8010/api/jobs`
- CSV export: `http://127.0.0.1:8010/api/jobs/export.csv`

## Backup and recovery

Stop the server before copying the database:

```sh
cp data/jobsniffing.sqlite3 "$HOME/jobsniffing-backup.sqlite3"
```

Restore it while the server is stopped:

```sh
cp "$HOME/jobsniffing-backup.sqlite3" data/jobsniffing.sqlite3
```

Rebuild only the Python environment:

```sh
rm -rf .venv
./scripts/ubuntu-bootstrap.sh
```

On native Termux, replace the final command with `./scripts/termux-bootstrap.sh`.

## Android troubleshooting

### Termux is stopped in the background

Disable battery optimization for Termux and keep its notification active. Android 12 and newer may terminate long-running or CPU-heavy processes.

### A package mirror fails

```sh
termux-change-repo
pkg update -y
```

Choose a working main repository mirror, then repeat the bootstrap command.

### Port 8010 is already in use

```sh
PORT=8011 ./scripts/termux-run.sh
```

### Ubuntu is damaged

```sh
proot-distro list
```

A full reset deletes the Ubuntu filesystem:

```sh
proot-distro reset ubuntu
```

Back up the JobSniffing database before resetting when the repository is stored inside `/root`.

## Operational boundary

JobSniffing discovers public ATS listings, scores and filters them locally, imports jobs, exports CSV, and tracks human review decisions. It does not log into job sites, bypass CAPTCHAs, or submit applications unattended.

## Official references

- Termux installation and Android requirements: https://github.com/termux/termux-app
- PRoot-Distro commands and aliases: https://github.com/termux/proot-distro
- Termux package-management help: https://github.com/termux/termux-packages/wiki/Package-Management
