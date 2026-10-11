# ADR-0001: Local-first MVP

- Status: Proposed
- Date: 2026-10-11
- Decision owner: repository owner

## Context

The existing prototype checks CSV files locally and generates audit packets. The first business experiment is a fixed-scope assurance service before a multi-tenant SaaS investment.

## Decision

Start with deterministic CSV assurance and an inspectable evidence pack. Add spreadsheet, research, and browser adapters only with explicit acceptance criteria and independent verification methods.

## Consequences

Benefits: small scope, easier reproduction, less customer-data exposure. Costs: manual service delivery remains necessary, domain rules must be declared, and some users may prefer hosted collaboration.

## Revisit when

Paid pilots reveal repeated needs beyond CSV checks, or local processing is a measurable barrier.
