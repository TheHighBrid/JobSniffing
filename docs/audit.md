# JobSniffing audit and readiness report

## Scope

Primary repository:

- `TheHighBrid/JobSniffing`

Reference repositories reviewed:

- `TheHighBrid/HunterXJob`
- `TheHighBrid/JobTomatik`

The supplied `TheHighBrid/HunterXJon/HunterXJob-v2` location could not be resolved. The owner or path appears to contain a typo, and no accessible `HunterXJob-v2` repository was found under the supplied location during this audit.

## Product boundary

JobSniffing 0.2.0 is a local Android job-discovery and human-review workbench. Its production-ready boundary is:

- public Greenhouse, Lever, and Ashby discovery
- manual and JSON imports
- deterministic offline scoring
- editable scoring terms, exclusions, and company blacklists
- local SQLite persistence and deduplication
- filtering, notes, status tracking, CSV export, and diagnostics
- a mobile-friendly localhost dashboard

It does not claim to provide universal browser form submission. No login automation, CAPTCHA bypass, stealth behavior, credential collection, or false submission confirmation is included.

## Reference-repository decisions

### Adopted from HunterXJob

- deterministic scoring without a mandatory paid model
- public ATS adapters before browser automation
- temporary SQLite databases in tests
- explicit review, blocked, failed, and submitted outcomes
- a rule that `submitted` requires a real confirmation signal
- fail-closed behavior for unsupported automation

### Adopted from JobTomatik

- hunt, queue, review, dry-run, and approval workflow concepts
- localhost operation on port 8010
- manual approval before any real-world application action
- Android-oriented operating instructions

### Deliberately excluded from the required runtime

- Redis and Celery
- Docker Compose
- a React build chain
- mandatory Playwright or Chromium
- paid AI-provider credentials
- LinkedIn, Indeed, or Upwork account automation
- stealth or CAPTCHA-bypass techniques

Those components would make the Android installation heavier and less dependable. Future optional automation should remain behind the existing API and status machine.

## Findings and remediation

### Previously addressed by the current repository

- database paths are resolved at call time
- static and template paths are independent of the launch directory
- request and response data are validated with Pydantic
- invalid status changes return stable HTTP errors
- provider identifiers are restricted before building fixed upstream URLs
- installation and startup have automated verification
- Python 3.11, 3.12, and 3.13 are covered by GitHub Actions

### Hardening added by this audit

#### Company blacklist enforcement

A newly saved scoring blacklist rescored existing jobs but did not change their status to `blocked`. A duplicate discovery could also refresh a now-blacklisted job while preserving its nonterminal status.

The remediation:

- applies a new blacklist during `rescore_all`
- applies it during duplicate upserts
- preserves terminal `submitted` and `blocked` records
- deliberately does not auto-unblock records when a blacklist is removed, because that should remain a human decision

#### Malformed ATS entries

One malformed listing in a provider payload could raise `KeyError` or a Pydantic validation error and abort the whole discovery request.

The remediation:

- validates each provider's top-level collection shape
- skips non-object entries
- skips entries without an ID or application URL
- skips entries with invalid field values
- preserves valid listings from the same response
- converts invalid provider shapes into a controlled `DiscoveryError`

#### Android documentation

The setup guide was streamlined so commands are not repeated unnecessarily:

- Termux installs PRoot-Distro
- Ubuntu installs only Git and CA certificates before cloning
- the repository bootstrap script installs Python when needed
- the bootstrap script also installs the project and runs full verification
- native Termux has a complete clone-to-run command path
- Ubuntu 24.04 is named explicitly

## Verification evidence

The synchronized release candidate was checked with:

```sh
python -m compileall -q app tests
python -m pytest -q
```

Result:

```text
24 passed
```

A real process-level check also:

- started Uvicorn on `127.0.0.1` with an isolated port
- used a temporary SQLite database
- received a successful `/health` response
- rendered the dashboard successfully
- terminated the temporary server cleanly

The regression suite covers:

- blacklist application to existing jobs
- blacklist application during duplicate upserts
- preservation of submitted records
- malformed Greenhouse, Lever, and Ashby entries
- mixed valid and invalid provider entries
- invalid provider collection shapes

## Readiness assessment

### Ready for use

- Android browser plus Termux/Ubuntu localhost operation
- public ATS discovery
- manual and JSON imports
- local ranking and filtering
- review queues and status tracking
- CSV export and SQLite backup
- repeated local verification after updates

### Intentionally not implemented

- unattended site login
- universal form filling or submission
- CAPTCHA handling
- inbox monitoring
- Android background scheduling
- provider-specific confirmation detection

A future submission adapter should be site-specific, dry-run-first, and allowed to mark `submitted` only after observing an explicit provider confirmation.

## Environment caveat

The Python test suite and real Uvicorn runtime were executed in the audit environment. The Termux and PRoot-Distro commands were checked against official project documentation, but the audit environment did not expose a physical Android device. Device-specific behavior such as OEM battery killing should therefore be confirmed on the target phone.
