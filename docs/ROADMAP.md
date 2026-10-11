# Roadmap

This is a hypothesis-driven sequence, not a commitment to build every item.

## Stage 0 — Repository foundation
- [x] Initialize repository and review/engineering standards.
- [ ] CI runs tests and repository contract checks on every PR.
- [ ] Configure branch protection and required status checks in GitHub settings.
- [ ] Import the existing MVP only after local checks and artifact provenance are reviewed.

## Stage 1 — First repeatable paid outcome
- [ ] Define a versioned evidence-pack schema.
- [ ] Harden CSV validator: malformed quoting, encoding, size limits, formula-like cells in exports, and explicit ruleset version.
- [ ] Add golden fixtures and independent expected results.
- [ ] Produce a report with input hash, tool version, checks, findings, and reproduction instructions.
- [ ] Run three real pilot jobs with customer permission and no unnecessary sensitive data.
- [ ] Measure review time, useful defects found, false positives, and willingness to pay.

## Stage 2 — Cross-artifact verification
- [ ] Spreadsheet adapter: recalculate with an independent engine and compare relevant cells to an independent calculation.
- [ ] Research adapter: claim-by-claim citations, source dates, direct support, and uncertainty labels.
- [ ] Browser QA adapter: test actual controls and exports, not only static rendering.
- [ ] Unified evidence pack and cross-checks between displayed figures and source artifacts.

## Stage 3 — Productization gate
Only consider hosted accounts, multi-tenant storage, payments, connectors, and scheduled runs after pilot evidence supports them. Before launch, complete threat modeling, access controls, retention/deletion, backup/restore, monitoring, incident response, and cost controls.
