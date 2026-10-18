# VAP Specification v0.1 (Draft)

**Status:** research draft. VAP normalizes evidence from a bounded software-verification run. It does not prove semantic correctness and is not a payment-authorization standard.

## Trust boundaries

1. Task publisher commits acceptance criteria, test-suite digest, runtime-image digest, command, limits, and protocol before accepting submissions or funding.
2. Submitted source bytes are untrusted. Unsafe paths, symlinks, special files, and Git metadata are rejected by v0.1.
3. Runner is a disposable Linux environment without secrets, using an already-present OCI image pinned by digest and rootless Podman with cgroup v2.
4. Expected outputs remain outside the candidate container. Only the current case input is passed through stdin.
5. The prototype has no attestation signer. A future signer must be separate from the runner and revalidate current evidence; it must not share a wallet key with the worker.
6. Settlement is out of scope. A future contract must reject unsigned, malformed, stale, replayed, or policy-incompatible attestations.

## Task commitment

The task profile commits the task ID; immutable OCI image; network disabled; read-only root filesystem; dropped capabilities; bounded tmpfs; direct argv command; CPU, memory, PID, timeout, input, output, source-size and file-count limits; sealed-test digest; and the exact stdin/stdout protocol.

Runtime identity is captured when preflight succeeds and included in the verdict core. The local task file is not an immutable registry: a production publisher must preserve the canonical task digest and bind it to the funded obligation.

## Canonical JSON

VAP v0.1 uses a restricted profile, not full RFC 8785/JCS conformance:

- UTF-8, ASCII object keys and NFC-normalized string values.
- Object keys sorted lexicographically; no insignificant whitespace.
- Floats, non-finite values, negative zero, duplicate keys, invalid Unicode, and integers outside signed 64-bit range are rejected.
- Digests are domain-separated. A profile change requires a new version identifier.

## Source and test commitments

Source entries contain relative POSIX path, byte size, and SHA-256 of the exact file bytes, sorted by path. Symlinks, special files, unsafe paths, Git metadata, over-limit files, and changes detected during snapshotting are rejected.

The test-suite digest hashes the parsed and normalized test-suite object. The publisher controls and retains the suite. Expected outputs do not enter the candidate container or the public VAP.

## Verdict core

The stable verdict core binds task, policy, source, tests, image, runner version and runtime identity, plus final verdict, reason, per-case outcomes and digests of captured stdout/stderr. Raw outputs and expected values are excluded.

    verdict_digest = SHA-256(canonical({"domain":"vap-verdict-core-v0.1","core":verdict_core}))

Timestamp, run UUID, and execution telemetry are outside this digest.

## Verdict semantics

- PASS: exit code zero and exact stdout bytes match expected output.
- FAIL_TESTS: non-zero candidate exit or stdout mismatch.
- POLICY_VIOLATION: an independent trusted observer confirms a violation bound to this run/container. The v0.1 adapter does not emit this status.
- RESOURCE_EXHAUSTED: enforced timeout/output/resource limit or independently confirmed OOM.
- INFRASTRUCTURE_FAILURE: runner unavailable, container did not start, runtime could not provide trustworthy state, or infrastructure abort.
- INVALID_SUBMISSION: the source or configuration violates the accepted input contract.

Stderr text, self-reports, and non-zero exit status are not by themselves evidence of a security violation.

## Telemetry and attestation

Telemetry is descriptive. It may include elapsed time, observed output sizes, container start/exit/OOM metadata, host kernel, and metric availability. Unavailable CPU and peak-memory measurements must be null and marked not collected.

The v0.1 envelope is unsigned and explicitly marked UNSIGNED_LOCAL_PROTOTYPE. A future signed profile must define exact signed bytes, algorithm, key rotation/revocation, freshness, replay protection, task/policy binding, signer isolation, and independent receipt validation.

## Required conformance tests

- Canonical serialization is invariant to object key insertion order.
- Duplicate keys, floats, negative zero, non-finite values, invalid Unicode, and oversized integers are rejected.
- Mutable image tags, network-enabled profiles, shell entrypoints, symlinks, special files, Git metadata, and resource overruns are rejected.
- Non-zero exit/output mismatch cannot become PASS.
- Stderr phrases alone cannot become POLICY_VIOLATION.
- Missing runtime or image cannot fall back to host execution.
- Telemetry and timestamps do not alter the verdict digest; judgment-bearing input changes do.
