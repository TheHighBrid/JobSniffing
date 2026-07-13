# API contract

Base URL for the local Android setup:

```text
http://127.0.0.1:8010
```

Interactive OpenAPI documentation is served at `/docs`.

## Health

### `GET /health`

Returns process status, operating mode, automation policy, and version.

## Jobs

### `POST /api/jobs`

Creates or updates a normalized job. Duplicate identity is `(source, external_id)`. Updating a job refreshes its content and score but does not reset a review status already chosen by the user.

Required JSON fields:

- `source`
- `external_id`
- `title`
- `company`
- `apply_url`, which must be an HTTP or HTTPS URL

Optional fields:

- `location`
- `description`

Returns `201 Created` with the stored job.

### `GET /api/jobs`

Query parameters:

- `status`: optional application status
- `min_score`: integer from 0 to 100, default 0
- `limit`: integer from 1 to 1000, default 200

Jobs are ordered by descending score and then newest creation time.

### `GET /api/jobs/{job_id}`

Returns one job or `404 Not Found`.

### `POST /api/jobs/{job_id}/status`

Body:

```json
{"status":"shortlisted","notes":"Strong fit"}
```

Returns the updated job. Error behavior:

- `404 Not Found` for an unknown ID
- `409 Conflict` for a disallowed state transition
- `422 Unprocessable Entity` for malformed input

## Discovery

### `POST /api/discovery/scan`

Body:

```json
{
  "source": "greenhouse",
  "board": "company-token",
  "company": "Company Name"
}
```

Supported sources:

- `greenhouse`
- `lever`
- `ashby`

`company` is optional and controls the display label. `board` is restricted to a safe ATS slug and cannot contain slashes, query strings, or URL schemes.

The service requests only a fixed public endpoint for the selected provider. A provider error returns `502 Bad Gateway`. Valid jobs are normalized, scored, and upserted into SQLite.

Response:

```json
{
  "source": "greenhouse",
  "board": "company-token",
  "fetched": 25,
  "upserted": 25
}
```

## Validation and limits

- Job source, ID, title, and company: 1 to 500 characters
- Board token: 1 to 200 safe slug characters
- Description: up to 200,000 characters
- Notes: up to 10,000 characters
- Apply URL: HTTP or HTTPS URL validated by Pydantic
