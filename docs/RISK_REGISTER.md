# Initial Risk Register

Scores are qualitative: likelihood and impact are Low / Medium / High. Revisit after each pilot and release.

| ID | Risk | Likelihood | Impact | Mitigation / evidence required | Owner |
|---|---|---:|---:|---|---|
| R-01 | Users mistake model-generated assertions for verified facts | Medium | High | Separate model suggestions from deterministic/source evidence; explicit status and provenance | Product |
| R-02 | Validator reports PASS while relevant rules were never configured | Medium | High | Report scope and ruleset; distinguish NOT TESTED; acceptance criteria required | Engineering |
| R-03 | Customer confidential data is exposed through logs or artifacts | Medium | High | Local-first, data minimization, redact logs, no customer fixtures in repo | Security |
| R-04 | CSV formula injection affects spreadsheet users opening exported CSV | Medium | High | Filtered CSV export prefixes formula-like text; test whitespace/control-character bypasses and target spreadsheet apps | Engineering |
| R-05 | Benchmark results are misrepresented across environments | Medium | Medium | Record runtime, dependencies, hardware context, raw outputs; avoid universal rankings | QA |
| R-06 | CI action compromise or excessive token permissions | Low/Medium | High | Minimal permissions, pin third-party actions to full SHAs, review action updates | DevOps |
| R-07 | Tests validate implementation assumptions rather than user requirements | Medium | High | Independent expected outputs, negative cases, external review, real pilot outcomes | QA |
| R-08 | Product is overbuilt before willingness to pay is established | High | High | Sell narrow fixed-scope service first; review after each pilot | Founder |
| R-09 | Original artifacts are overwritten or lose provenance | Low/Medium | High | Immutable inputs, hashes, derived-output lineage and versioned reports | Engineering |
| R-10 | A visually correct UI has inaccessible or broken controls | Medium | Medium/High | Keyboard tests, browser interaction tests, viewport and accessibility checks | QA |
