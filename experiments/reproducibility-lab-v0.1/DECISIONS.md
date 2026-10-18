# Decisions — Reproducibility Lab v0.1

## DR-001: Keep the runner fail-closed

- Status: ACCEPTED
- Decision: never execute untrusted source on the host when Podman is absent or its security properties cannot be established.
- Evidence: unit test verifies missing-Podman preflight failure.

## DR-002: Separate verdict from telemetry

- Status: ACCEPTED
- Decision: timestamp, run ID, elapsed time, and variable host telemetry are outside the verdict digest. The measured runtime identity is included in the judgment-bearing core.
- Rationale: execution noise must not silently change a stable verdict, while a different runtime identity should be visible.

## DR-003: Never infer a policy violation from candidate output

- Status: ACCEPTED
- Decision: POLICY_VIOLATION requires an independently trusted observer. Text in stderr, exit codes, or the candidate's own report is not proof.
- Open gap: seccomp/eBPF/audit observation is not implemented.

## DR-004: Defer payment and zkVM

- Status: DEFERRED
- Decision: no wallet, token, signing key, slashing, settlement contract, or zkVM prover until real Podman adversarial runs and an independent replay succeed.
- Exit criteria: rootless Podman + cgroup-v2 preflight; clean/wrong/timeout/output-flood runs; no secret-test mount; measured resource limits; captured runtime identity; independent replay; reviewed host-observer design.


## DR-005: Real container integration is a merge gate

- Status: ACCEPTED
- Evidence: GitHub Actions run [39145753470](https://github.com/Loofy147/Proofline/actions/runs/39145753470), commit \`48935a39bd468f7c7fa16e1b5f1ba5610c6121df\`, passed seven scenarios on a Linux GitHub-hosted runner using rootless Podman with cgroup v2.
- Image: \`docker.io/library/python@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f\`.
- Covered: correct output, wrong output, read-only source, blocked outbound network, no inherited host proxy variables, timeout, and output flood.
- The first live run exposed an input-delivery bug: stdin was piped to Podman without interactive stdin. The runner now passes \`--interactive\`, and the command flag is regression-tested.

## DR-006: VAP telemetry must be structurally consistent

- Status: ACCEPTED
- Decision: The verifier validates telemetry shape, counter ranges, case-run count, disclosure of uncollected resource measurements, and equality between the telemetry runtime identity and the identity digest committed by the verdict core.
- Limitation: VAP v0.1 is unsigned. Validation catches malformed or internally inconsistent telemetry; it cannot prove that otherwise well-formed telemetry was not edited.

## Open gaps

1. Podman's effective seccomp policy is not yet pinned and no trusted seccomp/eBPF/audit observer is consumed.
2. CPU-time and peak-memory telemetry are not implemented; the schema accepts only null for these v0.1 fields.
3. VAP is unsigned and cannot authenticate an operator or authorize payment.
4. The runner sends test inputs to the candidate; production threat modeling must consider feedback leakage.
5. No independent-host replay or Wasmtime/WASM comparison has been executed.
