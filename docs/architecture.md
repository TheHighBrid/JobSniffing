# Architecture

JobSniffing is local-first, API-first, and browser-last. One FastAPI process serves JSON endpoints and a small server-rendered UI backed by SQLite.

Core boundaries:

- Discovery adapters normalize jobs from public job-board surfaces.
- Scoring is deterministic and has no paid API dependency.
- Tracking owns the SQLite source of truth.
- Submission adapters are optional and must fail safely into `needs_review`.
- The Android shell is packaging only and should load the localhost UI.

Version-one non-goals: Redis, Celery, Docker as the primary path, paid LLM requirements, stealth LinkedIn automation, a separate native client, and committed APK binaries.
