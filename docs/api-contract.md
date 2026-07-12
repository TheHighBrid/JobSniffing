# API Contract

- `GET /health` returns local backend status.
- `POST /api/jobs` upserts a normalized job posting and scores it locally.
- `GET /api/jobs` lists tracked jobs in score order.
- `POST /api/jobs/{job_id}/status` changes status only when the state machine allows it.

The web UI must call these contracts rather than embedding ATS-specific logic.
