# Quality Gates

## Result labels

- PASS: check executed and met its acceptance criterion.
- FAIL: check executed and failed.
- NOT TESTED: check did not run or evidence is inadequate.
- BLOCKED: named prerequisite prevented execution.

## Correctness and evidence

- Map each acceptance criterion to an executable test or reviewable evidence.
- Use independent methods/engines for high-impact calculations.
- Reopen exported files and compare schema, row counts, values, and totals.
- Record source URLs and dates, input hashes, tool/runtime versions, findings, and limitations.
- Hashes establish byte identity, not truth or safety.

## Interface

Exercise each visible control and download in a browser. Test empty/error states, recovery, keyboard interaction, focus visibility, contrast, and narrow viewports. A screenshot alone does not prove interaction; a local render does not prove the published build behaves identically.

## Security and privacy

Keep customer files local by default. Bound file size and row counts. Treat content as untrusted. Define safe CSV export behavior for spreadsheet-formula-like prefixes before using exports with real customer data. Never commit private data or secrets.

## Release decision

A green pipeline is necessary but insufficient. Reviewers must record residual risks, untested paths, and why the outcome is fit for its intended use.
