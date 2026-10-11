# CI/CD and Pipelines

## Pull-request gates

The workflow runs two groups:

1. Python matrix (3.11, 3.12, 3.13): repository contract, unit tests, synthetic CSV fixture audit, Python compilation, and whitespace check.
2. Chromium interaction tests: installs the pinned Playwright development dependency and Chromium, then exercises navigation, embedded self-tests, CSV analysis/filter/export, malformed input, intake export, mobile width, and JavaScript errors.

It runs for pull requests, pushes to main, and manual dispatch. The workflow declares read-only contents permissions, disables persisted checkout credentials, and pins actions by full commit SHA.

## Local reproduction

    python scripts/validate_repo.py
    python -m unittest discover -s tests -v
    python verify_csv.py examples/demo_sales.csv --out ./proofline-output
    python -m pip install -r requirements-dev.txt
    python -m playwright install chromium
    python tests/browser_test.py

## Deployment

No deployment job is configured yet. A future deployment pipeline needs a staging environment, least-privilege deployment identity, immutable build/version, post-deploy health check, smoke tests, and a rollback mechanism. Approval gates are needed for migrations or external side effects.

A green CI run proves only that the named tests passed on that commit. It does not certify factual correctness, accessibility, security, or fitness for every customer use.
