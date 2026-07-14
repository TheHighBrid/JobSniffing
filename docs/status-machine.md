# Status Machine

`discovered -> scored -> shortlisted -> documents_prepared -> approved -> queued -> filling -> awaiting_confirmation -> submitted`

The direct legacy path `filling -> submitted` remains valid for existing manual workflows, but new automation adapters should use `awaiting_confirmation` and only mark `submitted` after a verifiable confirmation signal is stored.

Review and failure branches are fail-closed:

- `documents_prepared` can become `verification_failed` or `needs_review`.
- `queued` and `filling` can become `manual_intervention_required` when a CAPTCHA, account wall, unsupported question, or adapter limitation appears.
- `awaiting_confirmation` can become `submitted`, `verification_failed`, `needs_review`, `manual_intervention_required`, or `failed`.
- `needs_review`, `manual_intervention_required`, `verification_failed`, and `failed` can route back to human review or a safe retry state.
- `submitted`, `blocked`, and `withdrawn` are terminal except that `submitted -> withdrawn` is allowed to record a later human withdrawal.

Repeating the current status is a safe no-op. Invalid status changes return stable HTTP errors.
