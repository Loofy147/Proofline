# Contributing to Proofline

Proofline is early-stage. Prefer small, reviewable changes that move one user outcome forward.

## Development loop

1. Open or update an issue with the user problem and acceptance criteria.
2. Create a short-lived branch from `main`.
3. Make the smallest change that can satisfy the criteria.
4. Add tests for behavior and at least one relevant failure/edge case.
5. Run locally: `python -m unittest discover -s tests -v` and `python scripts/validate_repo.py`.
6. Open a pull request using the template. Link the issue, describe evidence, and disclose untested behavior.
7. Resolve blocking review feedback and rerun affected tests before merge.

## Pull request expectations

- Explain user value and scope; state what is deliberately out of scope.
- Include test commands and actual outcomes, not intended outcomes.
- Attach screenshots for UI changes and sample outputs for data/export changes.
- Preserve source inputs; never replace originals with transformed artifacts.
- Do not commit customer data, credentials, tokens, private URLs, or personal data.
- Keep dependencies minimal and justify new runtime dependencies.
- Document behavior changes, security implications, migration needs, and rollback.
- Do not label a feature production-ready based only on unit tests or a successful build.

## Review severity

- **Blocking:** correctness/security/privacy/data-loss issue; unverified core claim; tests do not cover acceptance criteria.
- **Major:** likely user harm, reliability issue, misleading status, or material maintainability problem.
- **Minor:** local usability, clarity, or non-critical maintainability improvement.
- **Suggestion:** optional improvement with a stated trade-off.

Reviewers should challenge the implementation, not the author. Every finding should include evidence, impact, and a suggested way to verify a fix.
