# CI/CD and Pipelines

## Pull-request gates

The `.github/workflows/ci.yml` workflow runs two groups:

1. Python matrix (3.11, 3.12, 3.13): repository contract, unit tests, synthetic CSV fixture audit, Python compilation, and whitespace check.
2. Chromium interaction tests: installs the pinned Playwright development dependency and Chromium, then exercises navigation, embedded self-tests, CSV analysis/filter/export, malformed input, intake export, mobile width, and JavaScript errors.

It runs for pull requests, pushes to `main`, and manual dispatch. The workflow declares read-only contents permissions and disables persisted checkout credentials. GitHub Actions are pinned to full commit SHAs; runners are pinned to `ubuntu-24.04` so the image does not silently move with the `ubuntu-latest` alias.

## Security workflows

- `.github/workflows/codeql.yml` runs CodeQL against Python and JavaScript using the `security-extended` query suite. It runs on pull requests targeting `main`, pushes to `main`, manual dispatch, and a weekly schedule. Findings are uploaded to GitHub code scanning.
- `.github/workflows/python-security.yml` runs Bandit against `verify_csv.py` and `scripts/`, with medium/high severity and medium/high confidence thresholds. It also runs `pip-audit` against both declared development and security requirements. It runs on pull requests targeting `main`, pushes to `main`, manual dispatch, and a weekly schedule.
- `requirements-security.txt` pins the direct scanner versions. Dependabot checks both GitHub Actions and Python requirement files weekly.

These are static and dependency checks, not a complete security assessment. They may need follow-up triage, targeted tests, or configuration checks. A clean scan does not prove that every bug or vulnerability is absent, and a reported finding is not automatically a confirmed exploit.

## Local reproduction

    python scripts/validate_repo.py
    python -m unittest discover -s tests -v
    python verify_csv.py examples/demo_sales.csv --out ./proofline-output
    python -m pip install -r requirements-dev.txt
    python -m playwright install chromium
    python tests/browser_test.py

Security checks (Python 3.12 or newer):

    python -m pip install -r requirements-dev.txt -r requirements-security.txt
    bandit -q -ll -ii -r verify_csv.py scripts
    pip-audit -r requirements-dev.txt -r requirements-security.txt

## Deployment

No deployment job is configured yet. A future deployment pipeline needs a staging environment, least-privilege deployment identity, immutable build/version, post-deploy health check, smoke tests, and a rollback mechanism. Approval gates are needed for migrations or external side effects.

A green CI run proves only that the named tests passed on that commit. It does not certify factual correctness, accessibility, security, or fitness for every customer use.
