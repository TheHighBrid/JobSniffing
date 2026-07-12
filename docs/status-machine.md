# Status Machine

Applications move through a strict review-gated state machine:

`discovered -> scored -> shortlisted -> approved -> queued -> filling -> needs_review | submitted | blocked | failed`

Rules:

- `submitted` is terminal and must only be set after an observed confirmation signal.
- Unsupported or uncertain automation returns `needs_review`, never fake success.
- `blocked` is terminal for policy, blacklist, daily cap, or site restriction failures.
- `failed` can move back to `needs_review` so the user can decide whether to retry manually.
