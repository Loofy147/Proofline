# Review Protocol

## Before implementation

Record the user problem, evidence it exists, acceptance criteria, alternatives, risks, exclusions, and recovery plan. Challenge assumptions before scope grows.

## Before merge

Review correctness, evidence quality, security/privacy, malformed inputs, failure handling, independent calculations, accessibility, export behavior, complexity, cost, and rollback.

Every finding needs severity, evidence/location, impact, reproduction, and a verification step.

## Independent challenge

Try to falsify the success claim. For important values, use an independent method or engine. Model-generated critique provides hypotheses; agreement between models is not proof.

## After a pilot

Compare intended and observed task time, useful defects, false positives, support burden, cost, and willingness to pay. Material gaps become issues and roadmap decisions.

## Status labels

- PASS: executed and met criteria.
- FAIL: executed and failed.
- NOT TESTED: evidence absent or inadequate.
- BLOCKED: named prerequisite stopped execution.

Conclude with accept / accept with follow-ups / revise / stop and one prioritized next action.
