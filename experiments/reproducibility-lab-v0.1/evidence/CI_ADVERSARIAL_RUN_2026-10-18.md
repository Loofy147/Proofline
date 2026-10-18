# CI adversarial container run — 2026-10-18

Status: **PASS** for the seven defined scenarios. This is prototype test evidence, not a security certification.

- Workflow: [reproducibility-lab](https://github.com/Loofy147/Proofline/actions/runs/39145753470)
- Commit: \`48935a39bd468f7c7fa16e1b5f1ba5610c6121df\`
- Platform: GitHub-hosted Ubuntu 24.04 runner
- Container runtime: rootless Podman; cgroup v2 confirmed
- Test image: \`docker.io/library/python@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f\`

## Scenario results

| Scenario | Expected result | Observed result |
|---|---|---|
| Correct solution + stdin | PASS | PASS |
| Incorrect output | FAIL_TESTS | FAIL_TESTS |
| Attempt to write the submission source | The source mount must be read-only | PASS |
| Attempt outbound network connection | Connection must be blocked | PASS |
| Host proxy-variable sentinels | No sentinel may reach the candidate | PASS |
| Infinite loop | RESOURCE_EXHAUSTED | RESOURCE_EXHAUSTED |
| Output flood | RESOURCE_EXHAUSTED | RESOURCE_EXHAUSTED |

Each scenario emitted a VAP accepted by the verifier, and the original submission remained unchanged.

## Interpretation and limitations

- The image was resolved to an immutable digest during CI setup; each scenario used the digest with automatic image pulling disabled.
- The run included the VAP telemetry validator and the stdin-enabled runner.
- These scenarios do not prove resistance to kernel or container-runtime escapes.
- Target CPU-time and peak-memory measurements remain unimplemented.
- No trusted security-policy observer, VAP signature, independent-host replay, or payment settlement exists in v0.1.
- The VAP remains unsigned and must not authorize bounty payouts.
