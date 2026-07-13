# Architecture

## Design goals

JobSniffing is local-first, API-first, and browser-friendly. It favors a small dependable process over a distributed stack that is awkward on Android.

The required runtime is:

```text
Android browser
      |
127.0.0.1:8010
      |
FastAPI + Jinja2
      |
Services and state machine
      |
SQLite
```

Public discovery is outbound HTTPS only:

```text
Greenhouse / Lever / Ashby public job API
                    |
             normalization
                    |
          validation and scoring
                    |
                 SQLite
```

## Boundaries

### Domain

`app/domain/` contains Pydantic request models, response models, status values, and transition rules. It has no network or UI responsibility.

### Database

`app/db/sqlite.py` resolves the database path at connection time, not import time. This makes environment overrides reliable and keeps tests isolated. Transactions commit only after a successful request and roll back on exceptions.

SQLite settings include:

- WAL journal mode
- foreign keys enabled
- 30-second busy timeout
- unique `(source, external_id)` identity
- index on status and score

### Discovery adapters

Each adapter converts one upstream provider payload into `JobPostingIn`. Invalid entries are skipped, while an invalid top-level payload fails the scan instead of manufacturing placeholder jobs.

### Services

- `discovery_service.py`: fixed-host public HTTPS requests and provider dispatch
- `scoring_service.py`: deterministic keyword score with token boundaries
- `tracking_service.py`: upsert, list, lookup, notes, and status changes

### Web layer

`app/main.py` translates domain errors into stable HTTP responses. Static and template paths are resolved from the module location, so the app works even when launched from another working directory.

The dashboard uses the same JSON API as command-line clients. It does not duplicate database logic.

## Security posture

Version 0.2.0 binds to localhost by default and has no multi-user authentication. It should not be exposed on `0.0.0.0` or the public internet.

Discovery board slugs are restricted to letters, numbers, periods, underscores, and hyphens. Upstream hosts are selected from a fixed map, reducing URL manipulation and server-side request-forgery risk.

No credentials are requested or stored. There is no browser login automation, CAPTCHA handling, stealth behavior, or real application submitter.

## Why no Redis, Celery, Docker, or mandatory browser engine

The reference repositories contain useful distributed and browser-driven ideas, but those dependencies add memory, storage, process-management, and compatibility costs on Android. JobSniffing keeps the required path to one Python process and one SQLite file.

Optional automation can be added later behind the current API and state machine. Any future submit adapter must fail closed into `needs_review` or `failed`, and may mark `submitted` only after observing a confirmation signal.
