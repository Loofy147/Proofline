# Reproducibility Lab v0.1

Status: **experimental research module** inside Proofline. This is separate from Proofline's current CSV-audit product vertical. It does not include blockchain settlement, wallet management, signature authority, or payment integration. An unsigned VAP never authorizes payment.

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
- Dedicated Linux CI executes seven real rootless-Podman scenarios against an OCI image resolved and pinned by digest.
- VAP integrity validation and fail-closed behavior tests.

## Not implemented

- Trusted seccomp/eBPF/audit observer. A policy violation is never inferred from stderr or a guest self-report.
- Actual cgroup CPU-time and peak-memory collection. These fields remain null.
- VAP signing, independent verifier quorum, zkVM/TEE attestation, disputes, or on-chain settlement.
- A production hidden-test service. Included demo tests are public fixtures and not appropriate as a funded production test suite.

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

This folder is an isolated research experiment. It does not change Proofline's current product acceptance rules or production path. Promotion into a supported product vertical requires real Podman adversarial runs, an independent replay, a reviewed observer model, and a product-demand decision.
