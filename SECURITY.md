# Security Policy

Proofline is an early-stage project; support and response times are not yet guaranteed.

## Reporting a vulnerability

Please do not publish exploit details, secrets, or customer data in a public issue. Use GitHub's private vulnerability reporting feature if it is enabled for this repository. Otherwise contact the repository owner privately through their GitHub profile and provide a minimal reproducible description.

Include affected commit/version, impact, prerequisites, and a safe reproduction where possible. Do not attach real customer data.

## Current security boundaries

- The current prototype is local-first and has no server-side authentication or multi-tenant isolation.
- Do not upload confidential customer files to an unreviewed hosted deployment.
- Never commit credentials, API keys, cookies, tokens, private URLs, or customer data.
- Treat uploaded files, web pages, model outputs, and generated artifacts as untrusted input.
- Before adding a backend, define retention/deletion, access control, encryption, tenant isolation, audit logging, backup/restore, and incident response.

Security-sensitive changes require explicit reviewer attention and a documented threat assessment.
