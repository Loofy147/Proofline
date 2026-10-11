# Architecture: initial direction

**Status:** proposed, not implemented.  
**Decision owner:** repository owner.  
**Last reviewed:** 2026-10-11.

## Product shape

Proofline aims to verify AI-assisted deliverables, initially for research reports, spreadsheets, CSVs, and interactive artifacts. It should produce an evidence pack with inputs, provenance, checks, outputs, failures, and limitations.

## Proposed layers

1. **Intake:** capture job objective, files, sources, constraints, and acceptance criteria.
2. **Adapters:** deterministic validators for CSV/data, spreadsheet recalculation, source/citation review, and browser behavior.
3. **Evidence model:** normalized records for inputs, checks, observed outputs, environment, timestamps, and artifacts.
4. **Review orchestration:** human-readable status and independent review; model suggestions are not verification evidence by themselves.
5. **Reporting/export:** generate machine-readable and human-readable evidence packs.
6. **Interface:** show status as PASS, FAIL, or NOT TESTED, with a path to inspect supporting evidence.

## Trust boundaries

- User files and remote content are untrusted.
- A model's assertion is a hypothesis until supported by a reproducible check or cited source.
- A test result applies only to its stated scope, environment, and revision.
- Hashes prove byte identity, not truth or safety.
- A spreadsheet engine successfully recalculating formulas proves evaluation, not that formulas or input assumptions are correct.
- A clean browser render does not prove every interaction or accessibility behavior.

## Local-first default

The first vertical slice should run locally and avoid uploading files. A hosted multi-customer service is a separate architecture decision requiring threat modeling, authorization, tenant isolation, retention/deletion, encryption, backups, and operational ownership.

## Proposed first vertical slice

Given a CSV plus a declared schema/ruleset, produce:
- source SHA-256 and byte size;
- deterministic structural and domain checks;
- explicit warnings and failures;
- a JSON report and human-readable summary;
- reproducible command and tool version.

## Non-goals for the first slice

- General autonomous agent platform.
- Automatic trust in AI-generated answers.
- Multi-tenant cloud storage or billing.
- Automatic publication or external side effects.
- Broad claims of factual verification from file structure alone.

See [ADR 0001](ADR/0001-local-first-vertical-slice.md) and [review protocol](REVIEW_PROTOCOL.md).
