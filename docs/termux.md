# Android, Termux, and Ubuntu/proot

## Recommended one-time installation

In Termux:

```sh
pkg update -y
pkg install -y proot-distro
proot-distro install ubuntu
proot-distro login ubuntu
```

Inside Ubuntu:

```sh
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y git python3 python3-venv python3-pip ca-certificates
cd /root
git clone https://github.com/TheHighBrid/JobSniffing.git
cd JobSniffing
./scripts/ubuntu-bootstrap.sh
```

The bootstrap creates `.venv`, installs the project, runs all tests, launches a temporary server, and verifies a real HTTP request against a temporary SQLite database.

## Daily start

```sh
proot-distro login ubuntu
cd /root/JobSniffing
./scripts/termux-run.sh
```

Open `http://127.0.0.1:8010` in the Android browser and keep the Termux session open.

## Update

```sh
proot-distro login ubuntu
cd /root/JobSniffing
git pull --ff-only
. .venv/bin/activate
python -m pip install -e '.[test]'
./scripts/verify.sh
```

## Backup

Stop the server, then:

```sh
cp data/jobsniffing.sqlite3 "$HOME/jobsniffing-backup.sqlite3"
```

CSV export is available from the dashboard or `/api/jobs/export.csv`.

## Native Termux alternative

```sh
./scripts/termux-bootstrap.sh
./scripts/termux-run.sh
```

Ubuntu/proot is preferred because normal Linux ARM64 Python wheels are more predictable than native Android builds.
