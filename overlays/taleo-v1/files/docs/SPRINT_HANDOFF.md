# Autonomy Sprint Handoff

**Working branch:** `autonomy/taleo-v1`  
**Canonical base:** `autonomy/wizard-v1`, continuing the external-credentials and shared-wizard stack.

## Mission

Continue JobSniffing toward reliable in-scope autonomy without replacing the lightweight local-first architecture or weakening its evidence and human-handoff invariants.

## Locked safety lines

- CAPTCHA, reCAPTCHA, hCaptcha, Turnstile, and generic anti-bot challenges always route to `manual_intervention_required`. Never solve or bypass them.
- 2FA/MFA and verification codes always route to the user.
- HireVue, HackerRank, Codility, personality, cognitive, and similar assessments always route to the user.
- Legal declarations and demographic self-identification require explicit human attestation.
- Government portals remain discovery, preparation, and manual-submit only.
- `submitted` requires stored confirmation-kind evidence.
- Unknown answers remain unknown. Never fabricate qualifications, dates, education, certifications, or experience.
- Live submission remains blocked unless `JOBSNIFFING_ALLOW_LIVE_SUBMISSION=1` and every non-bypassable gate passes.
- Candidate account creation is never automated.

## Completed foundation

- JobSniffing remains one FastAPI process plus SQLite, with no Redis, Celery, Docker, paid AI, or distributed worker requirement.
- Verified candidate profile, factual document generation, prepared-answer engine, submission gates, evidence trail, and strict state machine remain intact.
- Greenhouse, Lever, and Ashby remain on the adapter-neutral multi-page wizard.
- External credentials remain outside the repository under `~/.config/jobsniffing/credentials.json`, with owner-only permissions and secret-safe diagnostics.
- The wizard retains bounded traversal, frame discovery, post-fill fingerprints, validation recovery, redacted journals, blurred screenshots, and strict final-Submit separation.

## Step 3 complete: Taleo adapter v1

- Added `taleo_playwright.py` as a thin Taleo preflight over the shared wizard.
- Recognizes Taleo Enterprise career-section URLs and Taleo Business Edition career URLs only on `taleo.net` hosts.
- Rejects generic Oracle Jobs and Oracle Cloud Candidate Experience URLs as Taleo.
- Supports custom employer domains only when the page explicitly embeds, posts to, or links to a Taleo-hosted surface.
- Follows a bounded `Apply Online` or `Apply for this job` transition before locating the application form.
- Resolves application and login surfaces across accessible nested frames.
- Supports classic Taleo submit-input controls for Save and Continue, Next, Review, Review and Submit, and final Submit through shared wizard selectors.
- Supports newer button and `data-testid` style controls through the same wizard.
- Uses `credential_service.resolve_job_credentials("taleo", job)` exclusively for existing-account login.
- Accepts `username`, `email`, or `login` plus `password` from the selected external profile.
- Records only the non-secret credential profile name in evidence.
- Never creates a Taleo candidate account.
- CAPTCHA, MFA, verification codes, assessments, legal declarations, demographic self-ID, and unknown required questions remain manual boundaries.
- Taleo is registered for dry-run inspection, explicit submission, scheduler preparation, and batch release.
- API schemas now accept `taleo` for inspection and submission while discovery providers remain Greenhouse, Lever, and Ashby.

## Verification

```sh
sh scripts/verify.sh
```

Current result: **120 tests passing**, plus live FastAPI server startup, HTTP API smoke, default `discovery_only` mode, and temporary SQLite verification.

Taleo coverage includes:

- strict URL and host recognition
- custom-domain Taleo marker detection
- classic nested-frame multi-page traversal
- newer Taleo control layout
- Apply Online transition
- external credential login without secret evidence leakage
- missing-credential handoff
- account-creation handoff
- post-login MFA handoff
- dry-run zero-submit boundary
- live confirmation requirement

## Truthful certification boundary

The Taleo adapter is deterministic-fixture and full-suite certified. A current public Taleo form has not yet been exercised in this branch because no stable public certification target was pinned. Before enabling unattended Taleo submission, run a watched Chromium dry run on each employer-specific Taleo career section and inspect every screenshot and `wizard_journal` entry.

## Exact next task

Implement **Workday adapter v1** on the external credential loader and shared wizard.

1. Detect Workday Candidate Experience URLs without classifying unrelated Workday tenant pages.
2. Resolve tenant, site, and job identifiers from the application URL without logging query secrets.
3. Support Workday account login only through `credential_service.py`; account creation remains manual.
4. Support Workday's React-style comboboxes and dynamically revealed controls without arbitrary option selection.
5. Keep CAPTCHA, MFA, assessments, legal declarations, demographic self-ID, and unknown required questions as named human handoffs.
6. Preserve wizard neutrality. Do not add a Workday-specific traversal loop.
7. Add deterministic fixtures for direct-apply, login-first, dynamic-question, validation, and final-confirmation flows.
8. Add a zero-submit dry-run certification workflow.

## Device verification commands

```sh
pip install '.[automation]'
playwright install chromium
JOBSNIFFING_PLAYWRIGHT_HEADLESS=0 sh scripts/termux-run.sh
```

For Taleo, create or select one job with `source=taleo`, run inspection with `live=false`, inspect redacted evidence, and use `live=true` only after every visible value and navigation action is correct.
