# JobSniffing Autonomy Progress Map

**Checkpoint:** 2026-07-15  
**Working branch:** `autonomy/workday-v1`  
**Draft PR:** #12 into `autonomy/taleo-v1`  
**Verified baseline:** **134 tests passing**, plus FastAPI, HTTP, SQLite, and default `discovery_only` smoke checks.

## Mission

Build a truthful, fail-closed, Android-first job application agent. Supported and certified application flows may run automatically only when verified answers and every gate pass. CAPTCHA, anti-bot, MFA, account creation, assessments, legal declarations, demographic self-identification, government portals, and unknown required questions remain human handoffs. `submitted` always requires concrete confirmation evidence.

## Canonical architecture

JobSniffing remains one FastAPI process, one SQLite database, and optional Playwright. No mandatory Redis, Celery, Docker, PostgreSQL, paid AI, or distributed worker fleet. JobTomatik is a reference source for proven browser and certification patterns, not a runtime architecture to copy wholesale.

## Branch stack

| Layer | Branch | PR | Verified milestone |
|---|---|---:|---:|
| Consolidation | `consolidation-v1` archive/bundle | historical | 69 |
| Shared ATS primitives and unattended foundation | `autonomy/shared-primitives-v1` | historical | 89 |
| External credentials | `autonomy/credentials-v1` | #9 | 100 |
| Shared multi-page wizard | `autonomy/wizard-v1` | #10 | 110 |
| Taleo adapter | `autonomy/taleo-v1` | #11 | 120 |
| Workday adapter | `autonomy/workday-v1` | #12 | 134 |

## Materialize and verify

```sh
cd JobSniffing
git fetch origin
git switch autonomy/workday-v1
bash scripts/materialize-autonomy.sh
sh scripts/verify.sh
```

Expected baseline: **134 tests passed**.

## Completed capability map

- Greenhouse, Lever, and Ashby public discovery
- local scoring, exclusions, duplicate prevention, and SQLite tracking
- verified candidate profile and approved answer bank
- factual resume and grounded cover-letter pipeline
- nine submission gates and confirmation-kind evidence
- shared text, select, radio, checkbox, label, and field-type controls
- two-pass real-form inspection and verified filling
- bounded multi-page Next and Review traversal
- final Submit separation
- accessible iframe discovery
- post-fill structural fingerprints and URL/structure loop detection
- one bounded validation recovery cycle
- redacted wizard journals and blurred candidate-text screenshots
- CAPTCHA, MFA, assessment, legal, demographic, and account-wall handoffs
- scheduled discovery/preparation and batch release
- Greenhouse, Lever, Ashby, Taleo, and Workday submission adapters

## ATS status

| ATS | Status |
|---|---|
| Greenhouse | Implemented, watched live certification still required in JobSniffing |
| Lever | Implemented, watched live certification still required in JobSniffing |
| Ashby | Implemented, watched live certification required |
| Taleo | 120-test deterministic-fixture certified, employer-specific watched run required |
| Workday | 134-test deterministic-fixture certified, employer-specific watched run required |
| iCIMS | **Next task** |
| SmartRecruiters | Not started |
| Government portals | Preparation and manual-submit only |

## Locked invariants

- Never solve or bypass CAPTCHA or anti-bot controls.
- Never automate MFA or verification codes.
- Never answer employer assessments.
- Never automate candidate-account creation.
- Never attest legal or demographic answers without explicit human confirmation.
- Never fabricate candidate facts.
- Never store credential values or protected challenge responses in Git, SQLite, logs, screenshots, evidence, or exports.
- Never record `submitted` without confirmation evidence.
- Live submission requires `JOBSNIFFING_ALLOW_LIVE_SUBMISSION=1` and all non-bypassable gates.

## Remaining sequence

1. **iCIMS iframe and SPA adapter**
2. SmartRecruiters submission and discovery
3. redacted real-form fixtures
4. live certification and recurring drift checks
5. unattended-release hardening and dashboard polish

The command **`next`** means start the first unfinished item. At this checkpoint it means **iCIMS iframe and SPA adapter**.

## Workday v1 completed boundary

Workday v1 is implemented as a thin preflight on the shared wizard:

- strict `myworkdayjobs.com` Candidate Experience job recognition
- query-free tenant, cluster, site, and requisition evidence
- generic corporate and tenant-home rejection
- one bounded Apply transition
- existing-account login through external `workday` credentials
- account-creation and MFA handoffs
- React/ARIA combobox exact matching with rendered-selection verification
- dynamic-question rescanning through the shared wizard
- bounded validation recovery
- dry-run zero-submit behavior
- confirmation-kind evidence for submitted state

Before unattended Workday use, run a watched Chromium dry run for each employer tenant and inspect screenshots plus `wizard_journal`.

## iCIMS continuation contract

Create `autonomy/icims-v1` from `autonomy/workday-v1` and stack its PR into Workday.

Expected files:

```text
app/adapters/submit/icims_playwright.py
tests/unit/test_icims_adapter.py
app/services/submission_service.py
app/domain/schemas.py
app/main.py
docs/SPRINT_HANDOFF.md
docs/AUTONOMY_PROGRESS.md
README.md
.github/workflows/verify-icims-v1.yml
```

Required behavior:

- recognize iCIMS hosted career and application URLs without classifying unrelated employer pages
- resolve active application surfaces across same-origin iframes and SPA shells
- follow only bounded Apply transitions
- use the shared wizard rather than creating an iCIMS traversal loop
- preserve exact approved-answer mapping for custom selects, radios, checkboxes, and ARIA controls
- route login, CAPTCHA, MFA, assessments, legal, demographic, and unknown-required boundaries to named handoffs
- add hosted, embedded-frame, SPA, dynamic-question, validation, dry-run, confirmation, uncertainty, and redaction fixtures
- add a manual materialization workflow

Before coding, inspect current JobTomatik branches and PRs for any iCIMS implementation or reusable fixture patterns.

## Do not redo

Do not rebuild the state machine, profile model, question engine, document pipeline, gates, evidence service, credentials loader, DOM primitives, multi-page wizard, scheduler, batch release, or existing ATS adapters. Extend through narrow interfaces and fix only proven defects.

## Resume checklist

1. Read this file and `docs/SPRINT_HANDOFF.md`.
2. Inspect stacked PRs #9, #10, and #11.
3. Materialize and confirm 134 tests.
4. Inspect JobTomatik iCIMS work.
5. Branch `autonomy/icims-v1` from `autonomy/workday-v1`.
6. Implement only the iCIMS layer, tests, docs, and workflow.
7. Update both checkpoint documents.
8. Open a stacked draft PR into `autonomy/workday-v1`.
