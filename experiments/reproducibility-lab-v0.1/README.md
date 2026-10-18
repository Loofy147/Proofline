# Reproducibility Lab — Versioned VAP profiles

Status: **experimental research module** inside Proofline. The legacy VAP v0.1 verifier remains available; the current runner emits VAP v0.2 with best-effort cgroup v2 resource telemetry. This is separate from Proofline's current CSV-audit product vertical. It does not include blockchain settlement, wallet management, signature authority, or payment integration. Neither unsigned profile authorizes payment.

## Purpose

Test whether a software submission can be evaluated in a bounded, content-addressed execution environment, then recorded in a Verifiable Attestation Package (VAP) that another verifier can inspect and attempt to reproduce.

## Implemented boundary

- Strict task and test-suite profile validation.
- Restricted canonical-JSON profile for hashes; it does not claim full RFC 8785 compatibility.
- Content-addressed source snapshotting; symlinks, special files, unsafe paths, and Git metadata are rejected.
- Rootless Podman preflight. Linux, rootless mode, cgroup v2, runtime identity, and a digest-pinned image already present locally are required.
- Container execution without network, with a read-only root filesystem, dropped capabilities, no-new-privileges, CPU/memory/PID limits, and bounded stdin/stdout/stderr.
- Expected outputs are retained by the host harness and never mounted in the candidate container.
- Verdict digest excludes timestamps and variable telemetry. It binds task/source/test/policy commitments and the runtime identity.
- VAP verification validates telemetry shape and consistency with the committed runtime-identity digest; the envelope remains unsigned, so telemetry is not tamper-proof.
- Dedicated Linux CI executes eight real rootless-Podman scenarios against an immutable OCI image digest, including an explicit cgroup v2 CPU/memory measurement challenge.
- The sandbox suite runs twice on separate GitHub-hosted Ubuntu 24.04 workers, uploads verifier-checked VAPs, and fails if task/source/test/policy commitments, runtime identity, or verdict-core results differ. Timestamps and non-verdict telemetry are excluded from core comparison by design.
- This is cross-worker replay within one CI provider/control plane, not independent-provider or independent-trust-domain attestation.
- VAP integrity validation and fail-closed behavior tests.

## Not implemented

- Trusted seccomp/eBPF/audit observer. A policy violation is never inferred from stderr or a guest self-report.

- Trusted seccomp/eBPF/audit observation of forbidden behavior, VAP signing, independent verifier quorum, zkVM/TEE attestation, disputes, or on-chain settlement.
- A production hidden-test service. Included demo tests are public fixtures and not appropriate as a funded production test suite.
- Independent-provider replay. Both CI workers share one provider/control plane.
- Authenticity of VAP v0.2 telemetry. cgroup counters are measured by the runner but remain unsigned and descriptive; verifier checks only internal consistency.

## Requirements

- Python 3.11+
- Linux
- Podman in rootless mode with cgroup v2
- A locally preloaded OCI image referenced by immutable digest

Podman is called with pull disabled. Missing runtime or image causes a closed failure; the submission is never executed directly on the host.

## Checks

From this directory:

    python3 -m unittest discover -s tests -v
    python3 -m vap_lab.cli preflight --task examples/task.demo.json
    python3 -m vap_lab.cli verify-vap --vap evidence/local-run.vap.json
    # CI-only adversarial sandbox suite (requires rootless Podman + cgroup v2)
    VAP_TEST_IMAGE='docker.io/library/python@sha256:...' python3 tests/podman_integration.py

The preflight command is expected to fail when Podman, cgroup v2, or the pinned example image is unavailable. That is an infrastructure status, not a verdict on the candidate.

## Security boundary

Rootless Podman is defense in depth, not a proof of complete host-compromise resistance. Run untrusted submissions only on a disposable, no-secrets runner. The host observer and actual resource telemetry remain open requirements. Never use this unsigned local prototype to authorize financial settlement.

## Proofline relationship

This folder is an isolated research experiment. It does not change Proofline's current product acceptance rules or production path. Promotion into a supported product vertical requires real Podman adversarial runs, replay on a different trust domain, a reviewed trusted-observer model, signed attestation and dispute policy, and a product-demand decision.
