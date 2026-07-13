# Status machine

JobSniffing separates discovery, review, preparation, and outcome states.

## States

| State | Meaning |
|---|---|
| `discovered` | Raw job recorded before scoring |
| `scored` | Local deterministic score calculated |
| `shortlisted` | User selected the job for deeper review |
| `approved` | User approved application preparation |
| `queued` | Ready for a future filling step |
| `filling` | Application details are being prepared or entered |
| `needs_review` | A human decision or missing answer is required |
| `submitted` | Submission confirmation was observed |
| `blocked` | Policy, blacklist, site restriction, or user decision stopped the job |
| `failed` | A recoverable technical operation failed |

## Allowed transitions

```text
discovered  -> scored, blocked
scored      -> shortlisted, blocked
shortlisted -> approved, needs_review, blocked
approved    -> queued, blocked
queued      -> filling, needs_review, blocked
filling     -> needs_review, submitted, blocked, failed
needs_review-> approved, queued, blocked, failed
failed      -> needs_review, queued
submitted   -> none
blocked     -> none
```

## Rules

- Newly created and discovered jobs are stored as `scored` because scoring happens during upsert.
- A duplicate discovery refreshes the title, company, location, URL, description, and score without resetting the user-selected status.
- `submitted` and `blocked` are terminal.
- An unsupported transition returns HTTP `409 Conflict`.
- A future submission adapter must not report `submitted` based only on a button click or lack of an exception. It must observe a provider-specific confirmation page, URL, response, or message.
