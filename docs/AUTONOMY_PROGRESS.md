# JobSniffing autonomy progress

Branch: `autonomy/credentials-v1`

This branch continues `autonomy/shared-primitives-v1` and Sonnet's `consolidation-v1`. It does not replace the existing architecture.

## Step 1 complete: external credential loader

Implemented:

- Versioned provider/profile JSON stored outside the repository
- Default path `~/.config/jobsniffing/credentials.json`
- Optional `JOBSNIFFING_CREDENTIALS_FILE` override
- Repository-local path rejection
- Owner-only POSIX permission enforcement
- Current-user ownership enforcement
- 64 KiB size limit
- Strict primitive-only schema validation
- Profile resolution by explicit profile, application hostname, company slug, then `default`
- Safe credential status containing provider/profile names only
- Redacted `CredentialResolution.__repr__`
- SMTP integration preferring `smtp/default`
- Legacy `SMTP_*` environment variables retained only as a compatibility fallback
- `scripts/init-credentials.sh`
- Documentation and Git ignore guardrails

No secrets are written to SQLite, evidence, screenshots, exports, logs, or Git.

## Verification

Local source-tree verification completed with:

- 100 passing tests
- FastAPI server smoke
- HTTP API smoke
- Temporary SQLite database
- Default `discovery_only` mode

The credential-specific tests cover missing files, insecure permissions, repository-local placement, profile priority, host/company matching, invalid nested values, error redaction, representation redaction, SMTP precedence, and transport failure behaviour.

## Materialization

```sh
git switch autonomy/credentials-v1
bash scripts/materialize-autonomy.sh
```

The materializer restores Sonnet's consolidation, applies the 89-test autonomy layer, applies the transparent credential overlay, applies final security hardening, and runs the full verification script.

## Exact next step

Build the adapter-neutral shared multi-page wizard engine before implementing Taleo:

1. Bounded step traversal and loop protection
2. Navigation control classification separate from final submit
3. Question extraction and verified answer filling on every step
4. Iframe-aware scope traversal
5. Redacted step metadata and screenshots
6. Autosave and recoverable validation handling
7. Mandatory handoff for CAPTCHA, MFA, assessments, legal declarations, demographic self-ID, unknown required questions, and unexpected account walls
8. Page-shaped fake tests

Taleo begins only after this shared wizard engine is green.