# Audit and remediation report

## Scope

Primary repository:

- `TheHighBrid/JobSniffing`

Reference repositories reviewed:

- `TheHighBrid/HunterXJob`
- `TheHighBrid/JobTomatik`

The requested `HunterXJob-v2` repository or nested path was not found under the supplied location during the audit. The supplied URL also contained `HunterXJon`, which does not match the accessible `HunterXJob` repository name.

## Initial findings

The original JobSniffing repository had a useful local-first skeleton, but it was not yet ready for routine use.

### High priority

1. The database path was captured at module import, so later environment changes and test isolation could fail.
2. API request bodies used untyped dictionaries, allowing malformed payloads to reach application logic and potentially produce server errors.
3. Unknown job IDs and invalid transitions were not separated into stable `404` and `409` responses.
4. Static and template paths depended on the launch working directory.
5. Discovery adapters normalized fixture data but there was no live discovery service or endpoint.
6. There was no CI workflow or full startup verifier.

### Medium priority

1. Termux setup had no matching Ubuntu via PRoot-Distro path.
2. A single `.venv` name would be unsafe when sharing the repository between Termux and Ubuntu.
3. The dashboard was read-only and required API commands for ordinary review actions.
4. Board identifiers had no slug restriction.
5. Scoring used substring matching, which could count terms embedded inside unrelated words.

### Product boundary

The automation bridge and Android shell were placeholders. Treating those placeholders as complete would have been misleading. Version 0.2.0 instead defines a production-usable boundary: public discovery, local scoring, review, tracking, and manual handoff.

## Reference-repository decisions

### Adopted from HunterXJob

- public Greenhouse and Lever discovery concepts
- deterministic scoring without mandatory heavy ML
- temporary SQLite databases in tests
- explicit `submitted`, `blocked`, `needs_review`, and `failed` outcomes
- confirmation required before `submitted`
- unsupported automation disabled instead of simulated

### Adopted from JobTomatik

- hunt, queue, review, dry-run, approval philosophy
- localhost port 8010 for the Android device
- real submission disabled by default
- mobile-friendly operational documentation

### Deliberately not adopted into the required runtime

- Redis
- Celery
- Docker Compose
- React frontend build chain
- mandatory Playwright and Chromium
- paid AI provider requirements
- LinkedIn, Indeed, or Upwork account automation
- stealth or CAPTCHA bypass

These would make the Android setup heavier and less dependable. They can remain future optional modules behind the current service interfaces.

## Implemented remediation

- Pydantic request and response models
- HTTP URL validation and field length limits
- safe board-slug validation
- fixed-provider public discovery service
- Greenhouse, Lever, and Ashby normalization
- call-time database configuration
- rollback on failed transactions
- SQLite WAL, foreign keys, busy timeout, and indexes
- duplicate upserts that preserve review status
- word-boundary deterministic scoring
- explicit domain errors mapped to `404`, `409`, `422`, and `502`
- absolute static and template paths
- functional mobile dashboard for scans, manual jobs, and status changes
- separate `.venv-termux` and `.venv-ubuntu` environments
- native Termux and Ubuntu scripts
- end-to-end verification script
- GitHub Actions Python matrix

## Verification evidence

The local release candidate was checked with:

```sh
python -m compileall -q app tests
sh -n scripts/*.sh
python -m pytest -q
./scripts/verify.sh
```

The test suite covers:

- all three discovery payload contracts
- successful and failing mocked provider requests
- word-boundary scoring
- all state-machine rules
- call-time database path configuration
- transaction rollback
- API validation and filtering
- duplicate status preservation
- unknown IDs and invalid transitions
- dashboard rendering outside the repository working directory
- rejection of unsafe board paths
- real Uvicorn startup and health request

## Readiness assessment

**Ready for:** local Android job discovery, deterministic ranking, review queues, notes, original-link handoff, and pipeline tracking.

**Not ready for:** unattended account login, form submission, inbox monitoring, cover-letter generation, or background scheduling. Those are intentionally outside the 0.2.0 completion boundary and must not be represented as implemented.
