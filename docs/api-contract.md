# API Contract

Interactive documentation is available at `/docs`.

- `GET /health`
- `POST /api/jobs`
- `POST /api/jobs/import`
- `GET /api/jobs?status=&q=&min_score=&limit=`
- `GET /api/jobs/{id}`
- `DELETE /api/jobs/{id}`
- `POST /api/jobs/{id}/status`
- `POST /api/discovery`
- `GET|PUT /api/settings/scoring`
- `POST /api/jobs/rescore`
- `GET /api/jobs/export.csv`
- `GET /api/stats`

Discovery accepts an ATS board identifier, not an arbitrary URL.
