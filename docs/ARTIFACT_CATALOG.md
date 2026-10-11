# Artifact Catalog and Provenance

Historical prototypes shaped Proofline. Their old reports and limitations remain authoritative unless the relevant checks are rerun against the exact committed bytes.

| Artifact | Role | Available evidence | Boundary |
|---|---|---|---|
| Capability Lab 01 | Synthetic sales analysis | Python, CSV, JSON summary, report | Synthetic figures only |
| Capability Lab 02 | Interactive explorer | HTML, source, trace and verification files | Local demonstration |
| Capability Lab 03 | Correctness, performance, statistical audit | Question set, scorer, benchmark code/results, report | Timing depends on environment; answer-set match does not prove generalization |
| Live evidence ledger | Source-linked claims and workbook demo | Claim ledger, reviewed workbook, formula audit and source trace | Recalculation does not validate assumptions; historical UI interactions were not fully verified |
| Claude dossier iterations | Overview, low-level explanation and operation traces | User-supplied HTML snapshots and dossier archive | Artifact descriptions do not independently prove hidden runtime behavior |
| Proofline local MVP | Unified workbench and CSV audit | Browser tests, source, CLI, reports and manifest | Prototype, no hosted service or customer validation |

## What is in this repository

Executable app, Python CSV audit, tests, CI and core documentation are source-controlled. The complete consolidation seed archive was preserved separately while embedded/third-party assets and repository-size cost are reviewed. The complete historical binaries are not all individual Git blobs in this commit; this is an explicit transfer gap, not a claim of completion.

The preserved local seed ZIP SHA-256 is:

a260da58ad7c8ab1bad110c808cc642238050b09762cb88ba6c1c668ff61e99b

Before publishing historical artifacts, record source hash, date received, ownership/license, embedded resources, original/derived status, and which tests were rerun. Inspection does not grant redistribution rights.

## Inclusion policy

Keep executable source, minimal test fixtures, useful reports, and provenance in Git. Keep large duplicate render bundles as versioned archives/releases after licensing review. Never call an old artifact verified just because it is inventoried here.
