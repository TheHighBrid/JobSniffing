# JobSniffing Autonomy Progress Map

**Checkpoint:** 2026-07-15  
**Current working branch:** `autonomy/taleo-v1`  
**Current draft PR:** `#11` into `autonomy/wizard-v1`  
**Latest verified result:** **120 tests passing**, plus FastAPI, HTTP, SQLite, and default-mode smoke checks.

This file is the durable map for continuing the autonomy project. The repository, tests, and these documents are the source of truth. Chat history is supplementary only.

## 1. Mission

Build an Android-first, local-first job application agent that can discover, score, prepare, fill, submit, verify, and track applications with high reliability while remaining truthful and fail-closed.

The intended practical autonomy boundary is:

- Fully automatic for supported, certified ATS flows when all verified answers and submission gates pass.
- Human handoff for CAPTCHA, anti-bot challenges, MFA, account creation, assessments, legal declarations, demographic self-identification, government portals, and unknown required questions.
- Never fabricate candidate facts.
- Never record `submitted` without concrete confirmation evidence.

## 2. Canonical architecture

JobSniffing remains the canonical lightweight repository:

- one FastAPI process
- one SQLite database
- optional Playwright browser automation
- no mandatory Redis, Celery, Docker, PostgreSQL, paid AI, or distributed worker fleet
- public ATS APIs first, browser automation only where required

JobTomatik is an active reference implementation. Borrow proven browser and certification patterns from it when useful, but do not copy its heavier runtime stack unless a later requirement genuinely needs it.

## 3. Branch and PR stack

The current work is intentionally stacked:

| Layer | Branch | PR | Verified milestone |
|---|---|---:|---:|
| Sonnet/Fable consolidation | `consolidation-v1` archive/bundle | historical | 69 tests |
| Shared ATS primitives and unattended foundation | `autonomy/shared-primitives-v1` | historical branch | 89 tests |
| External credentials | `autonomy/credentials-v1` | #9 | 100 tests |
| Shared multi-page wizard | `autonomy/wizard-v1` | #10 | 110 tests |
| Taleo adapter | `autonomy/taleo-v1` | #11 | 120 tests |

Do not squash or merge a higher layer before its base layer unless the complete materialized source tree has been reconstructed and verified.

## 4. Materialization model

The branch stores transparent overlays on top of the original consolidation package.

Reconstruct the complete source tree with:

```sh
cd JobSniffing
git fetch origin
git switch autonomy/taleo-v1
bash scripts/materialize-autonomy.sh
```

Expected result:

```text
120 tests passed
FastAPI startup smoke passed
HTTP API smoke passed
Temporary SQLite verification passed
Default discovery_only mode confirmed
```

The materializer applies, in order:

1. Sonnet/Fable consolidation
2. shared autonomy primitives
3. external credential layer
4. shared wizard layer
5. Taleo layer

After materialization, review the resulting source tree before committing it permanently.

## 5. Completed capability map

### Core workflow

| Capability | State | Notes |
|---|---|---|
| Public ATS discovery | Ready | Greenhouse, Lever, Ashby |
| Job scoring and filtering | Ready | Local weighted scoring and exclusions |
| Duplicate prevention | Ready | SQLite-backed |
| Verified candidate profile | Ready | Field provenance and permissions |
| Factual resume tailoring | Ready | Source-fact tracking and reorder-only safety |
| Grounded cover letters | Ready | No invented qualifications |
| Prepared application answers | Ready | Verified profile and approved QA bank only |
| Submission gates | Ready | Nine checks before submission |
| Evidence trail | Ready | Confirmation evidence required for `submitted` |
| Scheduled discovery/preparation | Ready | Lightweight local loop |
| Daily batch release | Ready | Default unattended release model |
| Immediate release mode | Implemented, disabled by default | Requires explicit scope and every gate |

### Shared browser engine

| Capability | State |
|---|---|
| Text inputs and textareas | Implemented |
| Native dropdowns | Implemented |
| Radio buttons and checkboxes | Implemented |
| Accessible labels and conservative matching | Implemented |
| Per-step question extraction | Implemented |
| Two-pass inspect then fill | Implemented |
| Multi-page Next and Review traversal | Implemented |
| Final Submit separation | Implemented |
| Accessible iframe discovery | Implemented |
| Post-fill structural fingerprints | Implemented |
| URL and structure loop detection | Implemented |
| Bounded validation recovery | Implemented |
| Redacted wizard journal | Implemented |
| Candidate-text-blurred screenshots | Implemented |
| CAPTCHA/MFA/assessment/account-wall detection | Implemented as human handoff |
| Submission confirmation detection | Implemented |

### ATS coverage

| ATS | Discovery | Preparation/fill | Submission | Certification state |
|---|---|---|---|---|
| Greenhouse | Ready | Implemented | Implemented | Fake-page/full-suite; watched live certification still required in JobSniffing |
| Lever | Ready | Implemented | Implemented | Fake-page/full-suite; JobTomatik has stronger live certification patterns to borrow |
| Ashby | Ready | Implemented | Implemented | Fake-page/full-suite; watched live certification required |
| Taleo | Manual/import source | Implemented | Implemented | 120-test deterministic-fixture certification; watched employer-specific run required |
| Workday | Not yet | Not yet | Not yet | **Next task** |
| iCIMS | Not yet | Not yet | Not yet | Later task |
| SmartRecruiters | Not yet | Not yet | Not yet | Later task; evaluate discovery API too |
| Government portals | Discovery/prep only | Manual checklist | Manual only | Locked policy boundary |

## 6. Locked safety invariants

These are product requirements, not temporary missing features:

- Never solve or bypass CAPTCHA, reCAPTCHA, hCaptcha, Turnstile, or generic anti-bot challenges.
- Never automate MFA or verification-code entry.
- Never answer HireVue, HackerRank, Codility, personality, cognitive, or similar employer assessments.
- Never attest legal declarations or demographic self-identification without explicit human confirmation.
- Never automate candidate-account creation.
- Never fabricate qualifications, employment dates, education, certifications, security clearance, work authorization, or experience.
- Never store passwords, tokens, CAPTCHA responses, MFA values, or credential values in Git, SQLite, logs, screenshots, evidence, or exports.
- Never mark an application submitted without confirmation-kind evidence.
- Live submission stays blocked unless `JOBSNIFFING_ALLOW_LIVE_SUBMISSION=1` and every non-bypassable gate passes.
- Government portals remain preparation and manual-submit only.

## 7. External credentials

Credentials live outside the repository:

```text
~/.config/jobsniffing/credentials.json
```

Create the secure template with:

```sh
sh scripts/init-credentials.sh
```

The loader rejects repository-local files, insecure permissions, wrong ownership, excessive size, malformed schemas, and nested secret structures. Runtime diagnostics may expose provider/profile names only, never values.

Current providers include SMTP and Taleo. Workday must use the same service and add a `workday` provider profile rather than introducing environment-variable passwords.

## 8. Current Taleo boundary

Taleo v1 is complete at the deterministic-fixture level:

- strict Taleo host and URL recognition
- generic Oracle-page rejection
- custom-domain Taleo-marker detection
- bounded Apply Online transition
- classic nested-frame multi-page flow
- newer Taleo controls
- existing-account credential login
- missing-credential handoff
- account-creation handoff
- post-login MFA handoff
- dry-run zero-submit enforcement
- confirmation evidence requirement

Before unattended Taleo use, perform a watched Chromium dry run for each employer career section and inspect every screenshot and wizard-journal entry.

## 9. Exact remaining sequence

1. **Workday adapter v1**
2. iCIMS iframe and SPA adapter
3. SmartRecruiters submission and discovery
4. Redacted real-form fixtures
5. Live adapter certification and recurring drift checks
6. Broader unattended-release hardening and operational dashboard polish

The keyword **“next”** means start the first unfinished item in this sequence. At this checkpoint, **“next” means Workday adapter v1**.

## 10. Workday continuation contract

The next implementation should create a thin Workday preflight on top of the existing wizard. Do not create a second traversal engine.

Expected files:

```text
app/adapters/submit/workday_playwright.py
tests/unit/test_workday_adapter.py
app/services/submission_service.py
app/domain/schemas.py
app/main.py
scripts/init-credentials.sh
docs/credentials.md
docs/SPRINT_HANDOFF.md
docs/AUTONOMY_PROGRESS.md
README.md
.github/workflows/verify-workday-v1.yml
```

Required behavior:

- Recognize Candidate Experience application URLs on Workday-controlled hosts without treating unrelated tenant pages as job applications.
- Parse tenant, site, and job identifiers while stripping URL query strings from evidence.
- Follow only bounded Apply transitions.
- Use external `workday` credentials for existing-account login.
- Never automate account creation.
- Route CAPTCHA, MFA, assessment, legal, demographic, and unknown-required boundaries to named human handoffs.
- Reuse shared DOM controls, iframe discovery, question extraction, validation recovery, fingerprints, screenshots, journal, final-submit separation, and confirmation evidence.
- Handle React-style comboboxes conservatively and verify the rendered selection. Never select an arbitrary first option.
- Add fixtures for direct apply, login-first, dynamic controls, validation recovery, dry-run final boundary, and confirmed live submission simulation.
- Add a manual materialization workflow.

Before coding, inspect current JobTomatik branches and PRs for any Workday implementation or reusable certification fixtures. Port concepts and targeted logic only when compatible with JobSniffing’s lightweight architecture.

## 11. Do not redo

Do not rebuild or replace:

- the state machine
- candidate profile model
- question engine
- factual document pipeline
- nine submission gates
- evidence requirements
- external credential loader
- shared DOM primitives
- shared multi-page wizard
- scheduler and batch-release foundation
- existing Greenhouse, Lever, Ashby, or Taleo adapters

Extend these components through narrow interfaces. Fix proven defects when discovered, but avoid architectural churn.

## 12. Resume checklist for any model

1. Read `docs/AUTONOMY_PROGRESS.md`.
2. Read `docs/SPRINT_HANDOFF.md`.
3. Inspect open stacked PRs #9, #10, and #11.
4. Confirm the current branch is `autonomy/taleo-v1` before creating the next branch.
5. Materialize and run `sh scripts/verify.sh`.
6. Confirm **120 tests** before modifying code.
7. Inspect JobTomatik for relevant completed Workday work.
8. Create `autonomy/workday-v1` from `autonomy/taleo-v1`.
9. Implement only the Workday layer and supporting tests/docs.
10. Update both progress and handoff documents after verification.
11. Open a stacked draft PR into `autonomy/taleo-v1`.

## 13. Device certification commands

```sh
pip install '.[automation]'
playwright install chromium
JOBSNIFFING_PLAYWRIGHT_HEADLESS=0 sh scripts/termux-run.sh
```

For any ATS, begin with `live=false`. Inspect the full redacted evidence bundle. Use `live=true` only after every visible value and navigation action is correct and the application is intentionally approved for submission.
