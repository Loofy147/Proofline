# ADR 0001: Start local-first with deterministic CSV assurance

- **Status:** Proposed
- **Date:** 2026-10-11
- **Decision owner:** repository owner

## Context

The prior prototype demonstrates local CSV checks, downloadable reports, and a job-intake packet. It does not have accounts, hosted uploads, payments, model APIs, or multi-tenant storage. The intended first business experiment is a paid verification service before building a broad SaaS platform.

## Decision

Start with a local-first, deterministic CSV assurance workflow and an evidence-pack contract. Keep other checks (spreadsheet recalculation, source-claim review, browser QA) as separate adapters until each has reproducible acceptance tests.

## Consequences

### Benefits
- Small, testable scope.
- Customer files can remain local during early pilots.
- Deterministic checks are easier to reproduce than model-only review.
- A clear evidence schema can later unify different validators.

### Costs and risks
- CSV checks alone are not the full product promise.
- Local tooling may be less convenient for non-technical users.
- Domain rules must be explicit and customer-specific.
- Service delivery initially requires human review and operational discipline.

## Revisit when
- At least three pilot jobs reveal recurring needs not served by the CSV workflow.
- Customer feedback shows local execution is a barrier.
- Hosting is necessary to deliver a paid outcome and security/retention requirements are funded.
