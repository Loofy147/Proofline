# Proofline

Proofline is an early-stage project exploring **AI deliverable assurance**: evidence-led review of research, data, spreadsheets, generated files, and interactive interfaces.

## Status

The repository is in foundation setup. The previous local MVP and evidence artifacts are prototypes, not a production service. See the [engineering foundation PR](https://github.com/Loofy147/Proofline/pull/1); its CI must pass before merge.

## Guiding rule

**Demonstrate, don't advertise.** Every result should distinguish what was executed, what evidence supports it, what failed, and what has not been tested.

## Proposed first vertical slice

1. Intake a local deliverable and its source/evidence files.
2. Run deterministic checks where possible (starting with CSV/data quality).
3. Record inputs, versions, outputs, checks, failures, and limitations.
4. Export an evidence pack a reviewer can inspect and reproduce.

## Principles

- Do not overwrite customer originals.
- Treat model output as a claim, not proof.
- Prefer deterministic verification over agreement between models.
- Mark checks `PASS`, `FAIL`, or `NOT TESTED`; never infer success from a missing error.
- Keep customer files local by default until a deliberate security design justifies a hosted workflow.
- Start with a narrow paid service; let repeated customer needs decide what becomes software.

## Engineering and review

- [Architecture proposal](docs/ARCHITECTURE.md)
- [Local-first ADR](docs/ADR/0001-local-first-vertical-slice.md)
- [Structured review protocol](docs/REVIEW_PROTOCOL.md)
- [Inside/outside operating model](docs/OPERATING_MODEL.md)
- [Roadmap](docs/ROADMAP.md)
- [Risk register](docs/RISK_REGISTER.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Contributing](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
