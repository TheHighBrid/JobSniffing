# Architecture

JobSniffing is one local FastAPI process with four separate layers:

1. Discovery adapters normalize public Greenhouse, Lever, and Ashby payloads.
2. Scoring and settings provide deterministic local ranking with editable terms, exclusions, and company blocks.
3. Tracking owns SQLite, deduplication, state transitions, statistics, and export.
4. Web/API serves the mobile review queue and typed JSON contract from the same process.

SQLite is the only service. Redis, Celery, Docker, paid AI, a cloud database, and browser drivers are not required. Submission remains outside the trusted core and manual by default.
