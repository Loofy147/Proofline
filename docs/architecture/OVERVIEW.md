# Architecture Overview

## Current executable surface

- index.html: self-contained local browser UI for audit intake, CSV checks, evidence library and pilot scope.
- verify_csv.py: standard-library CSV audit CLI that writes JSON findings and a column-profile CSV.

The browser UI reads selected files locally and does not require a backend or model API. The evidence library is a catalog, not an automated source verifier.

## Proposed layers

1. Intake: objective, files/sources, constraints, acceptance criteria.
2. Adapters: CSV, spreadsheet recalculation, source claim review, browser behavior.
3. Evidence records: input hash, tool version, status, outputs, findings, limits.
4. Independent/human review.
5. Report-pack generation.
6. Interface showing evidence and unknowns.

## Trust boundaries

Hashes prove byte identity, not truth. Formula recalculation proves evaluation, not assumptions. Rendered pages do not prove interaction or accessibility. Model agreement is not independent verification. Customer input and remote content are untrusted.
