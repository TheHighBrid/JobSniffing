# External credentials

JobSniffing reads credentials from a user-owned JSON file outside the repository. Credentials are never written to SQLite, logs, evidence records, screenshots, exports, or Git.

## Create the file

```sh
sh scripts/init-credentials.sh
```

Default location:

```text
~/.config/jobsniffing/credentials.json
```

Override the location only when needed:

```sh
export JOBSNIFFING_CREDENTIALS_FILE="$HOME/private/jobsniffing-credentials.json"
```

The loader rejects files inside the JobSniffing repository. On Android, Termux, Linux, and Ubuntu proot, the file must belong to the current user and must not be readable by the group or other users:

```sh
chmod 600 ~/.config/jobsniffing/credentials.json
```

## Schema

```json
{
  "version": 1,
  "providers": {
    "smtp": {
      "default": {
        "host": "smtp.example.com",
        "port": 587,
        "username": "you@example.com",
        "password": "APP-SPECIFIC-PASSWORD",
        "from_address": "you@example.com",
        "use_tls": true
      }
    },
    "taleo": {
      "bank-name": {
        "username": "you@example.com",
        "password": "ACCOUNT-PASSWORD"
      },
      "default": {
        "username": "fallback@example.com",
        "password": "FALLBACK-PASSWORD"
      }
    },
    "workday": {
      "default": {
        "username": "you@example.com",
        "password": "ACCOUNT-PASSWORD"
      }
    }
  }
}
```

Providers contain named profiles. Login-based adapters resolve profiles in this order:

1. An explicit credential profile attached to the job
2. The application hostname
3. A normalized company name
4. `default`

For example, a Taleo application for `Example Bank` may use a profile named `example-bank`, the exact Taleo hostname, or `default`. Taleo uses existing-account credentials only. Account creation, MFA, and verification codes always remain manual.

## Safety behaviour

The loader fails closed when:

- An explicitly configured file is missing
- The file is inside the repository
- POSIX permissions permit group or other access
- The file belongs to another user
- The file exceeds 64 KiB
- The JSON structure or version is invalid
- A credential value is a nested object or array

Diagnostic status contains only provider and profile names. Credential keys and values are never returned.

## SMTP compatibility

The email adapter now prefers the external `smtp/default` profile. Existing `SMTP_*` environment variables remain as a compatibility fallback, but the external owner-only file is the recommended configuration.

## Taleo login boundary

The Taleo adapter can sign in to an existing candidate account when a matching external `taleo` profile contains `username` or `email`, plus `password`. The adapter never creates a candidate account, accepts account terms, solves CAPTCHA, enters MFA codes, or stores credential values in SQLite, evidence, screenshots, exports, or logs.

## Workday login boundary

The Workday adapter can sign in to an existing Candidate Experience account when a matching external `workday` profile contains `username`, `email`, or `login`, plus `password`. Profile resolution follows explicit profile, application hostname, company slug, then `default`.

The adapter stores only `workday/<profile-name>` as evidence. It never stores usernames or passwords, creates a candidate account, accepts account terms, enters MFA codes, solves CAPTCHA, answers assessments, or writes credential values to SQLite, logs, screenshots, evidence, exports, or Git.
