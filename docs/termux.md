# Android, Termux, and Ubuntu via PRoot-Distro

This is the verified installation and operating guide for JobSniffing 0.2.0.

## Choose one runtime

- **Native Termux** is the recommended route. It starts faster, uses less storage, and has fewer moving pieces.
- **Ubuntu via PRoot-Distro** is useful when you want a more conventional Debian/Ubuntu userspace.

Both routes bind the web server to `127.0.0.1`, so the dashboard is reachable from the same Android device but is not exposed to the local network.

## Prerequisites

Use a current Termux installation from F-Droid or the official Termux GitHub releases. Keep Termux and all Termux plugin apps from the same installation source because their signatures must match.

The repository requires:

- Android 7 or newer for current Termux packages
- Python 3.11 or newer
- internet access during installation and public board scans
- additional storage for the Ubuntu image when using PRoot-Distro

## Route A: native Termux

### 1. Prepare Termux and clone

```sh
pkg update -y
pkg install -y git
git clone https://github.com/TheHighBrid/JobSniffing.git
cd JobSniffing
```

### 2. Install the application

```sh
./scripts/termux-bootstrap.sh
```

This installs Python and curl if needed, creates `.venv-termux`, and installs JobSniffing with its test dependencies.

### 3. Verify the complete stack

```sh
./scripts/verify.sh
```

Expected final line:

```text
Verification passed: compile, tests, startup, health endpoint.
```

### 4. Start JobSniffing

```sh
./scripts/termux-run.sh
```

Open:

```text
http://127.0.0.1:8010
```

Keep the Termux session open while using the dashboard. Press `Ctrl+C` to stop the server.

## Route B: Ubuntu 24.04 through PRoot-Distro

### 1. Install PRoot-Distro and clone once

Run in Termux:

```sh
pkg update -y
pkg install -y git proot-distro
git clone https://github.com/TheHighBrid/JobSniffing.git
proot-distro install ubuntu:24.04
```

### 2. Enter Ubuntu with the Termux home shared

```sh
proot-distro login ubuntu --shared-home
```

With `--shared-home`, the Termux home is mounted as `/root` in the root Ubuntu session, so the repository is available as `/root/JobSniffing`.

### 3. Install inside Ubuntu

```sh
cd /root/JobSniffing
./scripts/ubuntu-bootstrap.sh
```

This creates `.venv-ubuntu`. It does not reuse `.venv-termux`, because Python executables built for the Termux userspace are not interchangeable with Ubuntu executables.

### 4. Verify and run

```sh
./scripts/verify.sh
./scripts/ubuntu-run.sh
```

Open `http://127.0.0.1:8010` in the Android browser.

### 5. Return later

From Termux:

```sh
proot-distro login ubuntu --shared-home
cd /root/JobSniffing
./scripts/ubuntu-run.sh
```

## Configuration

The run scripts support these environment variables:

| Variable | Default | Purpose |
|---|---:|---|
| `HOST` | `127.0.0.1` | Listen address |
| `PORT` | `8010` | HTTP port |
| `JOBSNIFFING_DB` | `data/jobsniffing.sqlite3` | SQLite database path |
| `DISCOVERY_TIMEOUT_SECONDS` | `20` | Public ATS request timeout |

Examples:

```sh
PORT=8011 ./scripts/termux-run.sh
```

```sh
JOBSNIFFING_DB="$HOME/private/jobs.sqlite3" ./scripts/ubuntu-run.sh
```

Keep `HOST=127.0.0.1` unless you deliberately add authentication and network protections. JobSniffing 0.2.0 is designed as a same-device service.

## Health checks

While the server is running:

```sh
./scripts/healthcheck.sh
```

Expected response:

```json
{"status":"ok","mode":"local-first","automation":"manual-review-only","version":"0.2.0"}
```

## Board scanning

Use the dashboard scan form or the API. The board value must be the ATS token, not a full URL.

Greenhouse example shape:

```sh
curl -fsS -X POST http://127.0.0.1:8010/api/discovery/scan \
  -H 'content-type: application/json' \
  -d '{"source":"greenhouse","board":"company-token","company":"Company Name"}'
```

For Lever, change `source` to `lever`. For Ashby, change it to `ashby`.

## Safe background operation

The simplest supported mode is a foreground Termux session. Android can stop background processes, and PRoot-Distro is not a virtual machine or a system service manager.

For a longer session:

1. Disable Android battery optimization for Termux.
2. Keep the Termux notification active.
3. Do not run both native and Ubuntu JobSniffing servers against the same database.
4. Copy the SQLite database periodically while the server is stopped.

## Updating without losing data

Native Termux:

```sh
cd ~/JobSniffing
git pull --ff-only
./scripts/termux-bootstrap.sh
./scripts/verify.sh
```

Ubuntu with shared home:

```sh
proot-distro login ubuntu --shared-home
cd /root/JobSniffing
git pull --ff-only
./scripts/ubuntu-bootstrap.sh
./scripts/verify.sh
```

The bootstrap scripts recreate or refresh the environment but do not delete `data/jobsniffing.sqlite3`.

## Recovery commands

Check installed PRoot-Distro containers:

```sh
proot-distro list
```

Resetting Ubuntu deletes everything stored only inside that Ubuntu container. The repository remains in the shared Termux home when installed using this guide:

```sh
proot-distro reset ubuntu
```

Repair a broken native Python environment:

```sh
cd ~/JobSniffing
rm -rf .venv-termux
./scripts/termux-bootstrap.sh
```

Repair a broken Ubuntu Python environment:

```sh
cd /root/JobSniffing
rm -rf .venv-ubuntu
./scripts/ubuntu-bootstrap.sh
```
