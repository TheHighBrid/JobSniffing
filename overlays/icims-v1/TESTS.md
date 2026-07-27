# iCIMS deterministic fixture coverage

- strict hosted URL parsing and query redaction
- unrelated and weak-marker page rejection
- custom-domain iCIMS frame and SPA markers
- hosted multi-page application
- embedded iframe application
- bounded SPA Apply transition
- external existing-account credential login
- missing credentials and candidate-profile creation handoff
- post-login MFA handoff
- assessment handoff
- dynamic ARIA combobox questions
- bounded validation recovery
- dry-run final-submit boundary
- confirmation evidence
- uncertain submission handling
- API inspection and submission registration

Local result: **147 tests passed** plus FastAPI, HTTP, SQLite, and default-mode smoke checks.
