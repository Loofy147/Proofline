# Proofline

Proofline is an early-stage, local-first workbench for **AI deliverable assurance**: evidence-led review of research, data, spreadsheets, generated files, and interactive interfaces.

> **Demonstrate, don't advertise.** A model output is a claim, not proof. A test is evidence only for the conditions it actually exercised.

## Current status

The repository contains a self-contained browser MVP, a standard-library Python CSV audit CLI, tests, CI, and implementation/review documentation. It is not yet a production SaaS. No accounts, server-side uploads, model API orchestration, payments, email/calendar actions, or scheduled tasks are included.

## Quick start

Open index.html in a modern browser. The CSV checker reads the selected file locally in the browser. The synthetic sample contains demonstration data only. The intake form exports a job packet; it does not execute the checks listed in that packet.

Python 3.11 or newer is recommended for the CLI and unit tests.

    python verify_csv.py examples/demo_sales.csv --out ./proofline-output
    python -m unittest discover -s tests -v
    python scripts/validate_repo.py

For real Chromium interaction tests, install the development dependency and browser:

    python -m pip install -r requirements-dev.txt
    python -m playwright install --with-deps chromium
    python tests/browser_test.py

## Repository map

- index.html — local browser workbench: overview, audit intake, CSV checker, evidence library, pilot service.
- verify_csv.py — deterministic CSV structure/data-quality CLI; outputs JSON findings and a column-profile CSV.
- tests/ — unit, repository-contract, package-integrity, and browser-interaction tests.
- examples/ — synthetic fixtures only.
- docs/ — architecture, CI/CD, project context, review protocols, risk and release standards, artifact provenance.
- PRODUCT_STRATEGY.md and PILOT_OFFER.md — the current business hypothesis and first proposed service.
- VERIFICATION_REPORT.md — scope and status of checks for this revision; CI results for the exact commit remain authoritative.

## CSV audit contract

Exit codes: 0 = no configured errors (warnings may exist); 1 = data failed a structural/domain check; 2 = input or runtime error. The report records filename, size, SHA-256, row/column profiles, errors, warnings, and limitations.

The checker does not prove source authenticity, factual truth, causal interpretation, or business suitability. Numeric inference uses dot-decimal syntax. Domain checks only run when the corresponding columns are present.

## Engineering workflow

Create a focused branch and PR. State user problem, acceptance criteria, risks, exclusions, tests actually run, and known limits. CI runs a Python 3.11/3.12/3.13 matrix plus Chromium interaction tests. Do not merge until required checks pass; repository branch protection must be confirmed in settings.

Keep PASS, FAIL, NOT TESTED, and BLOCKED distinct. Never commit secrets or customer data. Preserve originals. A green pipeline is necessary but not sufficient for release.

## Documentation

- [Architecture overview](docs/architecture/OVERVIEW.md)
- [CI/CD and pipelines](docs/CI_CD.md)
- [Quality gates](docs/QUALITY_GATES.md)
- [Inside/outside operating model](docs/OPERATING_MODEL.md)
- [Structured review protocol](docs/review/REVIEW_PROTOCOL.md)
- [Agent start-here context](docs/context/AGENT_START_HERE.md)
- [Project context](docs/context/PROJECT_CONTEXT.md)
- [External reviewer context](docs/context/EXTERNAL_CONTEXT.md)
- [Artifact provenance catalog](docs/ARTIFACT_CATALOG.md)
- [Licensing before public redistribution](docs/LICENSING_BEFORE_PUBLIC_RELEASE.md)
- [Risk register](docs/RISK_REGISTER.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Product strategy](PRODUCT_STRATEGY.md)
- [Pilot offer](PILOT_OFFER.md)
