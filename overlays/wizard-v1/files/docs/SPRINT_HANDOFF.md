# Autonomy Sprint Handoff

**Working branch:** `autonomy/wizard-v1`  
**Canonical base:** `autonomy/credentials-v1`, continuing Sonnet/Fable `consolidation-v1`.

## Mission

Continue JobSniffing toward reliable in-scope autonomy without rebuilding the consolidation layer or weakening its safety invariants.

## Locked safety lines

- CAPTCHA, reCAPTCHA, hCaptcha, Turnstile, and generic anti-bot challenges always route to `manual_intervention_required`. Never solve or bypass them.
- 2FA/MFA and verification codes always route to the user.
- HireVue, HackerRank, Codility, personality, cognitive, and similar assessments always route to the user. Never answer an employer assessment autonomously.
- Legal declarations and demographic self-identification require explicit human attestation.
- Government portals remain discovery, preparation, and manual-submit only.
- `submitted` requires stored confirmation-kind evidence.
- Unknown answers remain unknown. Never fabricate qualifications, dates, education, certifications, or experience.
- Live submission remains blocked unless `JOBSNIFFING_ALLOW_LIVE_SUBMISSION=1` and all non-bypassable gates pass.

## Completed

### Sonnet/Fable consolidation and autonomy foundation

- JobSniffing remains the canonical lightweight repository.
- Verified candidate profile, question engine, ATS-safe document generation, nine submission gates, evidence trail, and strict state machine remain intact.
- Shared DOM controls, two-pass inspection, Greenhouse/Lever/Ashby adapters, scheduled discovery, batch release, and external credentials remain intact.
- External credentials stay outside the repository under `~/.config/jobsniffing/credentials.json`, with owner-only permissions and secret-safe diagnostics.

### Step 2 complete: adapter-neutral multi-page wizard

- `wizard.py` owns bounded ATS traversal and is not tied to one platform.
- Navigation controls are classified as Next, Review, or final Submit. Intermediate controls are never mistaken for final submission based only on `type=submit`.
- Dry runs may traverse Next and Review to inspect reachable pages but never activate final Submit.
- Every step performs pre-fill and post-fill CAPTCHA/MFA/assessment/account-wall detection.
- Accessible iframe scopes are searched for application surfaces.
- Questions are extracted and verified answers are filled on every step.
- Human-only legal declarations and demographic self-identification stop the run with a named reason.
- Post-fill fingerprints exclude candidate values and protect against repeated structures.
- URL visit caps and total step caps stop navigation loops.
- Validation receives one bounded re-fill/retry attempt, then fails closed.
- Step journals contain question/control metadata but no candidate answers, email, phone, URL query strings, or secret values.
- Screenshots temporarily blur text inputs, textareas, content-editable fields, and file names in the main page and accessible frames.
- Existing Greenhouse, Lever, and Ashby adapters now inherit the wizard through the backward-compatible `run_single_page_form` entry point.

### Patterns borrowed from JobTomatik

The implementation deliberately borrowed proven concepts, not JobTomatik's heavier runtime stack:

- Measure navigation from a post-fill fingerprint.
- Separate intermediate navigation from final submission.
- Use bounded structure and URL loop protection.
- Extract validation messages and allow only bounded recovery.
- Search embedded frames for the active application surface.
- Preserve a redacted, step-by-step audit journal.
- Re-check human-only challenges after safe field filling and before any navigation action.

Redis, Celery, PostgreSQL, retained-browser sessions, remote-control panels, and distributed worker machinery were not imported into this step.

## Verification

```sh
sh scripts/verify.sh
```

Current result: **110 tests passing**, plus live FastAPI server, HTTP smoke, default `discovery_only` mode, and temporary SQLite verification.

## Exact next task

Implement **Taleo adapter v1** on the shared wizard engine.

1. Detect Taleo hosted application and career-section URLs without misclassifying generic Oracle pages.
2. Resolve the active application surface, including nested frames.
3. Support Taleo's classic multi-page controls through wizard selectors, not Taleo-specific traversal loops.
4. Detect account creation/login boundaries and resolve credentials only through `credential_service.py`.
5. Map verified profile and prepared answers to Taleo controls without guesses.
6. Preserve strict manual handoff for CAPTCHA, MFA, assessments, legal declarations, demographic self-ID, and unknown required questions.
7. Add deterministic Page-shaped fixtures for old and newer Taleo layouts.
8. Add a dry-run certification workflow that proves final Submit is never clicked.

Do not begin Workday until Taleo is green and the shared wizard remains adapter-neutral.

## Device verification commands

```sh
pip install '.[automation]'
playwright install chromium
JOBSNIFFING_PLAYWRIGHT_HEADLESS=0 sh scripts/termux-run.sh
```

For each ATS, run one job with `live=false`, inspect every redacted screenshot and `wizard_journal`, then use `live=true` only after all visible values are correct.
