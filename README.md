# JobSniffing

JobSniffing is an Android-first, local-first job discovery and review queue. It follows a simple rule: **API first, browser last, human approval before real submission**.

## What is set up

- FastAPI app serving both JSON and a small server-rendered review UI.
- SQLite as the only required database.
- Deterministic local scoring with no paid API dependency.
- Strict application status machine.
- Fixture-backed discovery adapter contracts for Greenhouse, Lever, and Ashby shapes.
- Termux scripts for bootstrap, run, and health checks.
- Optional automation bridge placeholder, disabled by default.
- Android shell placeholder for a future thin localhost wrapper.

## Quick start

```sh
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
./scripts/termux-run.sh
```

Open `http://127.0.0.1:8010`.

## API

```sh
curl -X POST http://127.0.0.1:8010/api/jobs \
  -H 'content-type: application/json' \
  -d '{"source":"manual","external_id":"1","title":"Android FastAPI Engineer","company":"Example","location":"Remote","apply_url":"https://example.com/apply","description":"Python SQLite backend"}'
```

Then open the review queue or call `GET /api/jobs`.

## Safety defaults

The app does not auto-submit applications in version one. Unsupported automation should produce `needs_review`, not `submitted`. A job can only become `submitted` after a supported adapter observes a confirmation signal.

See:

- [Architecture](docs/architecture.md)
- [API contract](docs/api-contract.md)
- [Status machine](docs/status-machine.md)
- [Termux guide](docs/termux.md)
- [APK shell plan](docs/apk-build.md)
