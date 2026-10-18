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

## Open gaps

1. Podman's default seccomp profile is not pinned, and no trusted host-policy event stream is consumed.
2. CPU-time and peak-memory telemetry are not implemented.
3. VAP is unsigned and cannot authenticate an operator or authorize payment.
4. The runner sends test inputs to the candidate; production threat modeling must consider feedback leakage.
5. No independent-host replay or Wasmtime/WASM comparison has been executed.
