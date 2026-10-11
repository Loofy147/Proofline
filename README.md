# Proofline

Proofline is an early-stage project exploring **AI deliverable assurance**: evidence-led review of research, data, spreadsheets, generated files, and interactive interfaces.

## Status

This repository is being prepared for the first implementation. The prior local MVP and evidence artifacts are prototypes, not yet a production service. This README is the bootstrap commit; the engineering foundation is being proposed separately through a pull request.

## Guiding rule

**Demonstrate, don't advertise.** Every result should distinguish what was executed, what evidence supports it, what failed, and what has not been tested.

## Proposed first vertical slice

1. Intake a local deliverable and its source/evidence files.
2. Run deterministic checks where possible (starting with CSV/data quality).
3. record inputs, versions, outputs, checks, failures, and limitations.
4. Export an evidence pack a reviewer can inspect and reproduce.

## Principles

- Do not overwrite customer originals.
- Treat model output as a claim, not proof.
- Prefer deterministic verification over agreement between models.
- Mark checks `PASS`, `FAIL`, or `NOT TESTED`; never infer success from a missing error.
- Keep customer files local by default until a deliberate security design justifies a hosted workflow.
- Start with a narrow paid service; let repeated customer needs decide what becomes software.

See the engineering foundation pull request for CI/CD, review policy, architecture context, threat assumptions, and release gates.