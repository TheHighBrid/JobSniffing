# Autonomy Sprint Handoff

**Checkpoint:** 2026-07-15  
**Branch:** `autonomy/workday-v1`  
**PR:** #12 into `autonomy/taleo-v1`  
**Baseline:** **134 tests passing**.

Read `docs/AUTONOMY_PROGRESS.md` first. It is the durable project map.

## Completed

The existing state machine, verified profile, factual documents, prepared answers, nine gates, evidence trail, external credentials, DOM primitives, shared wizard, scheduler, batch release, Greenhouse, Lever, Ashby, Taleo, and Workday layers are complete at their stated verification boundaries. Do not rebuild them.

Workday v1 includes strict Candidate Experience job recognition, query-free tenant/site/job evidence, bounded Apply, external existing-account login, account-creation and MFA handoffs, exact React combobox matching, dynamic question rescans, validation recovery, dry-run zero-submit behavior, and confirmation evidence.

## Next task

The next `next` command means **iCIMS iframe and SPA adapter v1**.

Create:

```text
autonomy/icims-v1
```

from:

```text
autonomy/workday-v1
```

Stack the next draft PR into `autonomy/workday-v1`.

## Start here

```sh
cd JobSniffing
git fetch origin
git switch autonomy/workday-v1
bash scripts/materialize-autonomy.sh
sh scripts/verify.sh
```

Confirm **134 tests** before changing code. Then inspect current JobTomatik branches and PRs for iCIMS URL recognition, embedded-frame handling, SPA controls, fixtures, and certification workflows.

## iCIMS architecture

iCIMS should own only the platform doorway: hosted/custom-domain recognition, bounded Apply transition, same-origin iframe or SPA application-surface resolution, and optional existing-account login boundary. Delegate traversal, filling, validation, loop protection, screenshots, journal, final Submit separation, and confirmation to the shared wizard.

Never create an iCIMS-specific page loop.

## Required tests

- strict iCIMS hosted URL recognition
- unrelated employer-page rejection
- custom-domain explicit iCIMS marker
- embedded application iframe
- SPA application shell
- bounded Apply transition
- login/account-creation handoff
- CAPTCHA and assessment handoff
- custom selects, radios, and checkboxes
- dynamic questions
- validation recovery
- dry-run final boundary
- successful confirmation evidence
- uncertain submission
- secret and URL-query redaction

## Safety

CAPTCHA, anti-bot, MFA, verification codes, assessments, account creation, legal declarations, demographic self-ID, government portals, and unknown required questions remain human boundaries. Never fabricate. Never persist secrets. Never mark `submitted` without confirmation evidence.

## After iCIMS

1. SmartRecruiters
2. real-form fixtures
3. live certification and drift checks
4. unattended-release hardening
