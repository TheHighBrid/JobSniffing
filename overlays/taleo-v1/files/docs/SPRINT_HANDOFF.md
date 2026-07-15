# Autonomy Sprint Handoff

**Checkpoint:** 2026-07-15  
**Working branch:** `autonomy/taleo-v1`  
**Canonical base:** `autonomy/wizard-v1`  
**Current draft PR:** `#11`  
**Verified baseline:** **120 tests passing**, plus FastAPI, HTTP, SQLite, and default-mode smoke checks.

Read `docs/AUTONOMY_PROGRESS.md` first. It is the complete capability map, branch stack, remaining sequence, and resume protocol. This handoff is the tactical continuation brief.

## Mission

Continue JobSniffing toward reliable in-scope autonomy without replacing its lightweight local-first architecture and without weakening its evidence, truthfulness, privacy, or human-handoff boundaries.

## Locked safety lines

- CAPTCHA, reCAPTCHA, hCaptcha, Turnstile, and generic anti-bot challenges always route to `manual_intervention_required`. Never solve or bypass them.
- 2FA/MFA and verification codes always route to the user.
- HireVue, HackerRank, Codility, personality, cognitive, and similar assessments always route to the user.
- Legal declarations and demographic self-identification require explicit human attestation.
- Candidate account creation is never automated.
- Government portals remain discovery, preparation, and manual-submit only.
- `submitted` requires stored confirmation-kind evidence.
- Unknown answers remain unknown. Never fabricate qualifications, dates, education, certifications, security clearance, work authorization, or experience.
- Live submission remains blocked unless `JOBSNIFFING_ALLOW_LIVE_SUBMISSION=1` and every non-bypassable gate passes.
- Secrets never enter Git, SQLite, logs, screenshots, evidence, exports, or exception representations.

## Branch stack

```text
consolidation-v1
  └─ autonomy/shared-primitives-v1        89 tests
      └─ autonomy/credentials-v1          PR #9, 100 tests
          └─ autonomy/wizard-v1           PR #10, 110 tests
              └─ autonomy/taleo-v1        PR #11, 120 tests
```

The next branch must be created from `autonomy/taleo-v1` and should be named:

```text
autonomy/workday-v1
```

The next PR must be stacked into `autonomy/taleo-v1`, not directly into `main`.

## Completed foundation

Do not rebuild these components:

- strict application state machine
- verified candidate profile with provenance and permissions
- factual resume and cover-letter pipeline
- approved QA answer bank
- nine submission gates
- evidence service and confirmation requirements
- shared DOM controls
- two-pass inspect/fill flow
- external credential loader
- adapter-neutral multi-page wizard
- bounded navigation, loop protection, validation recovery
- iframe discovery
- redacted journals and candidate-text-blurred screenshots
- scheduled discovery and batch-release foundation
- Greenhouse, Lever, Ashby, and Taleo adapters

JobTomatik is a reference source. Borrow compatible patterns and fixtures, but do not import its Redis, Celery, PostgreSQL, distributed-worker, or remote-browser stack into JobSniffing by default.

## Step 3 complete: Taleo adapter v1

Taleo now has a thin platform preflight over the shared wizard:

- strict Taleo Enterprise and Business Edition URL recognition
- generic Oracle and Oracle Cloud Candidate Experience rejection
- custom-domain support only with explicit Taleo form, frame, post target, or link evidence
- bounded Apply Online transition
- accessible nested-frame form discovery
- classic and newer control layouts
- existing-account login through `credential_service.resolve_job_credentials("taleo", job)` only
- no candidate-account creation
- missing-credential, account-creation, CAPTCHA, MFA, assessment, legal, demographic, and unknown-required handoffs
- Taleo inspection and submission registration
- dry-run zero-submit behavior
- confirmation evidence before `submitted`

Taleo verification coverage includes:

- strict host and URL detection
- custom-domain markers
- classic nested-frame multi-page traversal
- newer control layout
- Apply Online transition
- credential login without secret evidence leakage
- missing credentials
- account creation
- post-login MFA
- dry-run final boundary
- confirmation success and uncertainty

Current truthful boundary: deterministic fixtures and the full suite are certified. Employer-specific watched Chromium certification is still required before unattended Taleo submission.

## Exact next task: Workday adapter v1

The user’s next `next` command means begin Workday adapter v1.

### First actions

1. Materialize `autonomy/taleo-v1` and run the full verifier.
2. Confirm exactly **120 tests** before edits.
3. Inspect current JobTomatik branches and open PRs for Workday code, fixtures, URL parsing, React control handling, login boundaries, and certification workflows.
4. Borrow only compatible, proven pieces.
5. Create `autonomy/workday-v1` from `autonomy/taleo-v1`.

### Expected implementation files

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

### Architecture rules

Workday owns only the platform doorway:

- Candidate Experience recognition
- tenant, site, and job identifier parsing
- bounded transition from job detail to application
- optional existing-account login
- active application-surface resolution

Once the form is reachable, delegate to the existing shared wizard for:

- question extraction
- verified-answer filling
- React/native control interaction
- dynamic rescanning
- frame discovery
- Next and Review navigation
- validation recovery
- loop detection
- screenshots and journal
- final Submit separation
- confirmation evidence

Do not create a Workday-specific traversal loop.

### Required Workday behavior

- Recognize Workday Candidate Experience application URLs on Workday-controlled hosts without classifying unrelated tenant pages as job applications.
- Parse tenant, site, and job identifiers conservatively.
- Strip URL query strings and fragments from all evidence and diagnostics.
- Follow only bounded Apply transitions.
- Resolve existing-account credentials only through `credential_service.py` under provider `workday`.
- Record only credential provider/profile metadata, never values.
- Never create a Workday candidate account.
- Handle React-style comboboxes, radios, checkboxes, and dynamically revealed controls through shared primitives.
- Verify selected rendered values and never choose the first option as a fallback.
- Route CAPTCHA, MFA, assessments, legal declarations, demographic self-ID, and unknown required questions to named human handoffs.
- Require confirmation evidence after live submission.

### Required fixture coverage

- strict Workday host and path recognition
- unrelated Workday tenant-page rejection
- direct-apply flow
- job-detail to Apply transition
- login-first flow with external credentials
- missing-credential handoff
- account-creation handoff
- post-login MFA handoff
- React combobox and dynamic-question flow
- validation recovery
- dry-run final Submit boundary
- successful confirmation evidence
- uncertain-submission handoff
- secret-redaction regression

### Workflow and documentation

- Add `Verify workday-v1 materialization` as a manual workflow.
- Update `scripts/materialize-autonomy.sh` to apply the Workday overlay after Taleo.
- Update both this file and `docs/AUTONOMY_PROGRESS.md` after the suite is green.
- Open a stacked draft PR into `autonomy/taleo-v1`.

## Resume commands

```sh
cd JobSniffing
git fetch origin
git switch autonomy/taleo-v1
bash scripts/materialize-autonomy.sh
sh scripts/verify.sh
```

Expected baseline:

```text
120 tests passed
```

For watched browser validation:

```sh
pip install '.[automation]'
playwright install chromium
JOBSNIFFING_PLAYWRIGHT_HEADLESS=0 sh scripts/termux-run.sh
```

Always begin ATS certification with `live=false`, inspect every screenshot and `wizard_journal` entry, and use `live=true` only after all visible values and actions are correct.

## After Workday

The remaining fixed sequence is:

1. iCIMS iframe and SPA adapter
2. SmartRecruiters submission and discovery
3. redacted real-form fixtures
4. live adapter certification and recurring drift checks
5. unattended-release hardening and dashboard polish
