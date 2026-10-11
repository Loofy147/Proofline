# Roadmap

This is an evidence-driven plan, not a promise to build every item.

## Stage 0 — Repository foundation

- [x] Create repository and initial engineering/review documentation.
- [x] Integrate the local-first browser MVP and CSV CLI.
- [x] Add a Python 3.11/3.12/3.13 CI matrix and Chromium interaction job.
- [x] Add current architecture, operating context, review protocol, risk, release, and provenance documentation.
- [ ] Configure required branch protection/status checks in GitHub settings (tracked in issue #2).
- [ ] Publish/import the full historical binary bundle after licensing and size review (tracked in issue #3; the local seed archive is preserved by SHA-256).

## Stage 1 — First repeatable paid outcome

- [x] CSV checker emits versioned JSON findings and a column-profile CSV.
- [x] Baseline unit and Chromium tests cover common valid/invalid input and filtered export behavior.
- [x] Filtered CSV export prefixes formula-like cells and has a browser regression test.
- [ ] Expand adversarial CSV tests (control characters, whitespace-prefix variants, encodings, size and row limits).
- [ ] Verify safe-export behavior in the actual spreadsheet applications used by intended customers.
- [ ] Harden source preservation, evidence-pack schema, CLI tool/runtime provenance, and detailed check trace.
- [ ] Interview likely customers and run at least three scoped pilot jobs with permission and appropriately redacted data.
- [ ] Measure review time, useful defects, false positives, completion rate, and willingness to pay.

## Stage 2 — Cross-artifact verification

- [ ] Spreadsheet adapter: recalculate with an independent engine and compare relevant cells to independent calculations.
- [ ] Research adapter: claim-by-claim source support, publication dates, primary-source preference, and uncertainty labels.
- [ ] Browser QA adapter: test actual controls, keyboard behavior, and downloads in the intended published environment.
- [ ] Unified evidence pack linking inputs, hashes, check definitions, outputs, and limitations.

## Stage 3 — Productization gate

Only consider hosting, accounts, multi-tenant storage, payments, connectors, and scheduled workflows after pilot evidence supports them. Before hosted customer data, complete threat modeling, access controls, tenant isolation, retention/deletion, backup/restore, monitoring, incident response, and cost/abuse controls.
