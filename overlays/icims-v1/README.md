# iCIMS v1 stacked overlay

This transparent overlay applies the locally verified iCIMS adapter delta to the verified Workday v1 source tree.

- decoded patch SHA-256: `3339cfb5c89c32ebfea42cf0ec74874f2be772a0f04d7dda13ed6ad9f92f3826`
- compressed patch SHA-256: `a8c4b2301182c10b856355eb3f3aac432c50974f2cdf048e1154c98a25218ae3`
- patch strip level: `-p5`
- verified result after application: **147 tests passed**, plus FastAPI, HTTP, SQLite, and default-mode smoke checks

Apply only after the complete Workday v1 source tree is present:

```sh
bash overlays/icims-v1/apply.sh
bash overlays/icims-v1/finalize.sh
sh scripts/verify.sh
```

The overlay contains no credentials, candidate answers, screenshots, or application data.
