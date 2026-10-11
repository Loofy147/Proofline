# Structured Review Protocol

Use this protocol at three checkpoints: before implementation, before merge, and after observing the feature in use.

## A. Pre-implementation challenge

The author writes:
- User/problem statement and target user.
- Current behavior and evidence of the problem.
- Acceptance criteria that can be tested.
- Alternatives considered and why this option wins.
- Failure modes, data sensitivity, and external side effects.
- Rollback/recovery plan when the change is consequential.

The reviewer challenges assumptions before code is written. Avoid designing a large framework for an unvalidated need.

## B. Implementation review

Review in this order:

1. **Correctness:** does behavior satisfy each acceptance criterion?
2. **Evidence:** can every important claim be traced to a test, source, calculation, or explicitly marked human judgment?
3. **Security/privacy:** input trust, secrets, permissions, data retention, unsafe file parsing, external requests.
4. **Failure handling:** malformed input, missing dependency, timeout, partial output, retry safety, and recovery.
5. **Reproducibility:** pinned/runtime versions where relevant, deterministic fixtures, documented commands.
6. **UX/accessibility:** empty/error/loading states, keyboard behavior, contrast, responsive layout, understandable language.
7. **Operations:** logs, observability, cost, rate limits, backups, release/rollback where relevant.
8. **Maintainability:** complexity, dependency burden, clear boundaries, tests for regression.

Each finding should include severity, file/line or reproduction, impact, and a concrete verification step.

## C. Independent challenge

A reviewer who did not author the change should try to disprove the success claim. For high-risk or data-heavy changes, use a second implementation or independent calculation rather than reusing the same logic.

Models may generate review hypotheses, but deterministic tests, source inspection, and human judgment determine disposition. Two models agreeing is not proof.

## D. Post-implementation assessment

After a pilot or release, compare intended vs observed:
- task completion and user time saved;
- defect detection and false-positive rate;
- failed/abandoned runs;
- support burden and runtime/cost;
- customer feedback and willingness to pay;
- new risks or untested assumptions.

Create follow-up issues for material gaps. Close issues only with evidence.

## Decision labels

- **PASS:** acceptance criteria were executed and met in the stated environment.
- **FAIL:** an executed check failed.
- **NOT TESTED:** no adequate evidence; do not convert this to PASS.
- **BLOCKED:** the check could not run due to a named dependency/permission/environment blocker.

## Review output

For each PR, record: decision, blocking findings, non-blocking findings, tests actually run, limitations, and required follow-up. A concise review is preferred over a documentary performance.
