# Status Machine

`discovered -> scored -> shortlisted -> approved -> queued -> filling`

From `filling`, a job can become `needs_review`, `submitted`, `blocked`, or `failed`. `needs_review` can return to `approved` or `queued`. `failed` can return to `needs_review`. `submitted` and `blocked` are terminal. Repeating the current status is a safe no-op.

Invalid transitions return HTTP 409. Unknown jobs return HTTP 404.
