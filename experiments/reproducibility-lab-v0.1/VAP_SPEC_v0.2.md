# VAP Specification v0.2 (Draft)

**Status:** experimental and unsigned. VAP v0.2 adds descriptive Linux cgroup v2 CPU and peak-memory counters. It does not prove semantic correctness, authenticate the runner, or authorize bounty/payment settlement.

## Compatibility

- VAP v0.1 remains supported with its original verdict-core v0.1 digest domain and null-only resource metrics.
- VAP v0.2 uses verdict-core v0.2, the domain-separated digest domain vap-verdict-core-v0.2, and vap.attestation.v0.2.
- Profile/schema mismatches must be rejected. A v0.1 record must not be silently reinterpreted under v0.2 or vice versa.

## Resource counters

For each live candidate container, the runner resolves the container host PID from Podman inspect, then parses that PID's unified cgroup v2 entry from /proc/<pid>/cgroup. The resolved cgroup path must remain beneath the cgroup mount; traversal and paths that resolve outside that root are rejected.

- The cpu.stat field usage_usec is converted to cpu_time_ns by multiplying by 1,000.
- memory.peak is recorded as peak_memory_bytes.
- Missing, unreadable, malformed, or out-of-range counters are null, never fabricated as zero.
- The sampler records cumulative CPU usage and the high-water memory reading while the container is alive, then takes a final reading before container removal. Very short-lived tasks may legitimately have unavailable metrics.
- The per-case status is CGROUP_V2_MEASURED, CGROUP_V2_PARTIAL, UNAVAILABLE, or NOT_RUN.

Top-level resource_measurement_status is derived from all attempted cases:

- COLLECTED: both counters exist for every attempted case; target_cpu_time_ns is their sum and target_peak_memory_bytes is the maximum per-case peak.
- PARTIAL: at least one counter was read, but not every attempted case has both; top-level aggregates remain null to avoid false precision.
- UNAVAILABLE: at least one case ran, but neither counter was obtained for any case.
- NOT_RUN: no candidate case was executed, or every attempted case was rejected before container execution.

The verifier checks types, status/field consistency, and exact top-level aggregation when status is COLLECTED. It rejects counters that contradict the declared per-case measurement status. These are consistency checks, not authentication: the unsigned envelope permits a malicious or compromised report producer to forge all telemetry fields together.

## Verdict core and replay

Resource telemetry is deliberately outside the verdict core because CPU time and memory measurements can vary across executions. The core still binds the task, source, sealed test suite, runtime image/identity, policy, runner version, verdict, case outcomes and output digests.

Cross-runner CI executes the same eight scenarios on two separate GitHub-hosted Ubuntu 24.04 workers. It verifies each VAP and requires identical verdict cores. A dedicated allocation fixture requires the sampler to report a positive CPU counter and at least 32 MiB peak memory on each worker. Numeric resource values are not required to be identical.

This is cross-worker replay within one CI provider/control plane—not independent-provider attestation. It cannot rule out shared runner defects, host/kernel escape, provider compromise, or collusion.

## Unsigned trust boundary

The attestation envelope remains explicitly unsigned, with null algorithm, signer, and signature. No signer, trusted syscall observer, independent verifier quorum, hidden-test service, dispute system, replay-protected payout policy, or blockchain settlement is implemented. The runner does not infer POLICY_VIOLATION from stderr or candidate self-report. Network-isolation tests verify only the tested path and do not constitute complete syscall-policy observation.

Do not use VAP v0.2 to authorize bounty payouts, slashing, or other financial settlement.

## Required additional evidence

- Replay on a different trust domain / CI provider.
- A reviewed and independently validated seccomp/eBPF/audit observer with negative tests that kill deliberate policy bypass mutations.
- Signature/key rotation, revocation, freshness, and replay protection, with signer separated from the runner.
- A protected task registry binding publisher, sealed tests, policy, funded obligation and dispute resolution.
- Kernel/container-runtime escape assessment and operational monitoring.
