# Contributing to Proofline

Proofline is early-stage. Prefer small, reviewable changes tied to a user outcome.

## Development loop

1. Open/update an issue with the user problem, evidence, scope, and acceptance criteria.
2. Create a short-lived branch from main.
3. Make the smallest change that satisfies the criteria.
4. Add tests for intended behavior and at least one relevant failure or edge case.
5. Run locally: python scripts/validate_repo.py; python -m unittest discover -s tests -v; and, for UI changes, python tests/browser_test.py.
6. Open a PR and record the exact commands and actual results.
7. Resolve blocking findings and rerun affected tests before merge.

## PR expectations

- Explain user value, included scope, and deliberate exclusions.
- Map acceptance criteria to actual test results.
- Include screenshots for UI changes and sample outputs for data/export changes.
- Preserve original files; never commit customer data, tokens, secrets, private URLs, or credentials.
- Justify new runtime dependencies and document security/data-handling implications.
- State anything not tested; do not describe intended tests as passed.

## Review severity

- Blocking: correctness/security/privacy/data-loss issue, unsupported core claim, or acceptance criteria not verified.
- Major: likely user harm, reliability issue, misleading status, or material maintainability risk.
- Minor: local usability, clarity, or non-critical maintainability issue.
- Suggestion: optional improvement with stated trade-off.

Every finding should state evidence, impact, reproduction, and how a fix will be verified.
