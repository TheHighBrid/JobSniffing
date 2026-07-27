# JobSniffing autonomy progress

Branch: `autonomy/shared-primitives-v1`

This branch deliberately continues Sonnet's `consolidation-v1` rather than replacing or redesigning it.

## Verified locally

`sh scripts/verify.sh` completed with:

- 89 passing tests
- live FastAPI server smoke
- HTTP API smoke
- default `discovery_only` mode
- temporary SQLite database

## Added after Sonnet's 69-test consolidation

### Shared browser autonomy spine

- `dom_kit.py`: text, select, radio, checkbox, accessible-label matching and conservative fuzzy matching
- `handoff.py`: CAPTCHA, anti-bot, 2FA/MFA and assessment detection, always routed to manual intervention
- `confirmation.py`: confirmation text, URL and application-reference evidence
- `browser_form.py`: common single-page ATS runner with screenshots and fail-closed outcomes

### ATS adapters

- Greenhouse refactored onto the common runner
- Lever submission and inspection adapter
- Ashby submission and inspection adapter
- Custom question extraction and field-type-aware answer filling
- Real `live=false` fill-preview path that never clicks submit

### Two-pass applications

1. Inspect the real form and extract its questions.
2. Prepare answers from the verified profile or approved QA bank.
3. Fill only verified answers on the submission pass.
4. Stop for unknown, sensitive, CAPTCHA, MFA or assessment steps.

### Unattended foundation

- persistent public-ATS discovery targets
- scheduled discovery and preparation cycle
- local `autonomy-loop.sh`, without Redis, Celery or Docker
- default `batch_confirm` release policy
- optional `immediate` release policy that still obeys all safety and evidence gates
- batch-ready and batch-release API endpoints

## Hard safety lines

These remain human tasks and are not considered missing autonomy features:

- CAPTCHA or anti-bot challenge
- 2FA or MFA verification code
- employer assessments, including HireVue, HackerRank, Codility and cognitive/personality tests
- legal declarations and voluntary demographic self-identification
- authenticated government-portal submission

The agent may detect, prepare and hand off these steps. It must not bypass or answer them autonomously.

## Live verification still required

The Playwright logic is fake-page tested. It has not yet been validated against live Greenhouse, Lever or Ashby forms with Chromium on the user's device. Start with `live=false`, inspect screenshots, and perform one watched live application per adapter before permitting unattended release.

## Exact next implementation sequence

1. Add a credential loader that reads user-owned JSON outside the repository and never commits secrets.
2. Build a shared multi-page wizard engine.
3. Add Taleo first, with dry-run screenshots and fixture tests.
4. Add Workday account/login/wizard support, with account creation and MFA always handed off.
5. Add iCIMS iframe/SPA support.
6. Add SmartRecruiters submission and investigate its public discovery surface.
7. Capture redacted real-form fixtures and promote adapters from experimental only after watched tests pass.

## Materialize this branch

Run:

```sh
sh scripts/materialize-autonomy.sh
```

The script restores Sonnet's committed consolidation ZIP, applies the verified autonomy overlay, installs test dependencies and runs `scripts/verify.sh`. It does not commit or push automatically.
