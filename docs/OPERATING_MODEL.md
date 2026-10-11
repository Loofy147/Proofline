# Proofline Operating Model: Inside and Outside the Repository

**Purpose:** keep implementation, independent criticism, and customer learning connected without turning reviews into bureaucracy.

## Inside the project: continuous engineering loop

1. **Frame:** issue states user problem, evidence, scope, acceptance criteria, risks, and exclusions.
2. **Plan:** author records design choice and alternatives; reviewer challenges assumptions before expensive implementation.
3. **Build:** small PR, tests, minimum permissions, no secrets/customer data.
4. **Verify:** CI executes deterministic tests; independent calculations/sources are used for high-impact claims.
5. **Review:** reviewer inspects code, evidence, failure cases, security/privacy, UX, and rollback.
6. **Release:** checklist completed; version and known limitations recorded.
7. **Observe:** inspect failures, support burden, and user outcomes; create follow-up issues.

## Outside the project: independent assessment

Run a separate review when a milestone or customer pilot completes. Keep it outside the author's implementation loop where practical.

### Review packet
- Exact commit/tag and deliverable hashes.
- Product goal and acceptance criteria.
- CI results and test commands.
- Sample inputs and expected outputs (synthetic or customer-approved).
- Evidence ledger and unresolved claims.
- Known limitations, risks, cost, and external dependencies.
- Customer feedback with permission and sensitive details removed.

### Review roles
- **Builder:** explains intent and reproduces the result.
- **Adversarial reviewer:** tries to falsify the success claim; looks for missing tests, weak evidence, and failure cases.
- **Independent verifier:** recalculates/checks high-impact outputs using a different method or tool.
- **Product reviewer:** assesses whether the result solves a paid customer problem and whether the scope should change.
- **Owner:** chooses fixes, accepts documented residual risk, or stops the work.

One person may temporarily fill multiple roles, but the report must disclose this. Model-generated reviews are useful for finding hypotheses; they are not independent verification by themselves.

## Review cadence

- **Every PR:** tests, code review, risk/evidence check.
- **Every milestone:** architecture and threat-model delta review.
- **After each pilot:** outcome and pricing review; update risks and roadmap.
- **Monthly while active:** dependency/action updates, unresolved risk review, cost/complexity check, and whether scope remains customer-led.

## Decision record

Each review ends with:
- Decision: accept / accept with follow-ups / revise / stop.
- Blocking findings and owner.
- Non-blocking improvements.
- Checks run and evidence links.
- What remains untested.
- Next review date or trigger.

## Anti-patterns to avoid

- Treating CI green as proof of product correctness.
- Asking two models to agree and calling that independent verification.
- Adding agents, connectors, databases, or orchestration before a customer need is shown.
- Treating a roadmap or report as completed implementation.
- Leaving a review with only a long critique and no prioritized next action.
