#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python scripts/validate_repo.py
python -m unittest discover -s tests -v
python verify_csv.py examples/demo_sales.csv --out "${TMPDIR:-/tmp}/proofline-demo-audit"
if python -c 'import playwright' >/dev/null 2>&1; then python tests/browser_test.py; else echo 'NOT RUN: Playwright not installed; browser tests are not claimed as passed.'; fi
