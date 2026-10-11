# Architecture: current MVP and proposed next layers

**Status:** local-first MVP implemented; cross-artifact assurance remains incremental.
**Last reviewed:** 2026-10-11.

## Current executable components

- **index.html:** self-contained browser workbench with overview, audit intake, CSV analysis, filtering and export, evidence catalog, and pilot-service description. Selected files are read in the browser; the page has no server backend.
- **verify_csv.py:** Python standard-library CLI that parses a CSV, records source file size and SHA-256, checks header and row structure, missing/duplicate data, profiles columns, performs the optional sales arithmetic check when matching fields exist, and emits JSON plus a column-profile CSV.
- **tests/** and GitHub Actions: unit/contract checks across Python 3.11, 3.12 and 3.13, plus Chromium interaction tests.
- **docs/**: product intent, review protocols, quality gates, risks, and artifact provenance.

## Current data flows

### Browser
Selected CSV → local parse → structural/domain checks → on-page findings and row table → filtered CSV/JSON/Markdown download.

The filtered CSV export prefixes formula-like text with an apostrophe to reduce spreadsheet formula injection risk. This is a mitigation, not a guarantee for every spreadsheet importer. A generated intake packet records objective, sources, constraints and checks; every planned check starts as NOT TESTED. Intake itself does not fetch sources or execute research/browser checks.

### CLI
Local CSV path → size/encoding/strict-quoting checks → structure and configured numeric checks → report JSON and column-profile CSV. Exit code 0 indicates no configured errors (warnings may be present), 1 indicates check failure, and 2 indicates input/runtime failure.

## Proposed layers

1. **Intake:** objective, source files/URLs, constraints, acceptance criteria.
2. **Adapters:** extend deterministic CSV checks; then independent spreadsheet recalculation, source-claim review, and browser behavior.
3. **Evidence model:** input identity, tool/runtime version, check definition, result, output artifact, source evidence and limitations.
4. **Review:** independent calculation/source challenge and human disposition.
5. **Report pack:** reproducible machine-readable and human-readable evidence.
6. **Interface:** show evidence and unknowns without implying unrun checks passed.

## Trust boundaries

- User files and remote content are untrusted.
- Model assertions are hypotheses until supported by a reproducible check or cited source.
- A test result applies only to its recorded input, commit, environment and criteria.
- Hashes prove byte identity, not truth or safety.
- A spreadsheet engine recalculating formulas proves evaluation, not that formulas or assumptions are correct.
- A rendered page does not prove every interaction, accessibility behavior, or published deployment.
- Agreement between models is not independent verification.

## Local-first default

Keep customer files local by default. A hosted multi-customer service is a separate architecture decision requiring threat modeling, authentication/authorization, tenant isolation, retention/deletion, encryption, backups, incident response, and operational ownership.

## Non-goals for the current slice

- General autonomous agent platform.
- Automatic trust in AI-generated answers or truth certification.
- Multi-tenant cloud storage, billing, or hosted monitoring.
- Model API orchestration, email/calendar connectors, or scheduled execution.
- Automatic publication or external side effects.

See the local-first ADR, review protocol, quality gates and operating model before changing trust boundaries.
