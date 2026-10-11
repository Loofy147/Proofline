# Security Policy

Proofline is an early-stage project; response times are not guaranteed.

## Reporting

Do not publish exploit steps, credentials, or customer data in a public issue. Use GitHub private vulnerability reporting if enabled. Otherwise contact the repository owner privately through their GitHub profile and share a minimal, redacted reproduction.

## Current boundaries

- The current app is local-first; it has no backend authentication or multi-tenant isolation.
- Do not use an unreviewed hosted deployment for confidential customer files.
- Never commit credentials, tokens, cookies, private URLs, or personal/client data.
- Treat uploaded files, web pages, and model outputs as untrusted input.
- Before hosting customer data, review access control, tenant isolation, retention/deletion, encryption, logs, backups, and incident response.
