"""Verdict classification that never infers security violations from stderr."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

STATUSES = {
    "PASS",
    "FAIL_TESTS",
    "POLICY_VIOLATION",
    "RESOURCE_EXHAUSTED",
    "INFRASTRUCTURE_FAILURE",
    "INVALID_SUBMISSION",
}


@dataclass(frozen=True)
class CaseResult:
    status: str
    exit_code: Optional[int]
    stdout: bytes
    stderr: bytes
    reason: str


def classify_case(
    *,
    return_code: Optional[int],
    stdout: bytes,
    stderr: bytes,
    expected: bytes,
    termination: str = "normal",
    confirmed_policy_violation: bool = False,
) -> CaseResult:
    """Classify only from exit/output and trusted execution metadata.

    stderr is retained for a digest and diagnostics; its contents are never
    treated as proof that a policy violation occurred.
    """
    if confirmed_policy_violation:
        return CaseResult("POLICY_VIOLATION", return_code, stdout, stderr, "external_policy_observer_confirmed")
    if termination in {"timeout", "output_limit", "resource_limit", "oom_confirmed"}:
        return CaseResult("RESOURCE_EXHAUSTED", return_code, stdout, stderr, termination)
    if termination in {"infrastructure", "not_started", "unknown_abort"}:
        return CaseResult("INFRASTRUCTURE_FAILURE", return_code, stdout, stderr, termination)
    if return_code is None:
        return CaseResult("INFRASTRUCTURE_FAILURE", None, stdout, stderr, "missing_exit_code")
    if return_code != 0:
        return CaseResult("FAIL_TESTS", return_code, stdout, stderr, "nonzero_exit")
    if stdout != expected:
        return CaseResult("FAIL_TESTS", return_code, stdout, stderr, "stdout_mismatch")
    return CaseResult("PASS", return_code, stdout, stderr, "exact_output_match")


def aggregate_verdict(results: list[CaseResult]) -> str:
    if not results:
        return "INVALID_SUBMISSION"
    for status in ("POLICY_VIOLATION", "RESOURCE_EXHAUSTED", "INFRASTRUCTURE_FAILURE", "INVALID_SUBMISSION"):
        if any(result.status == status for result in results):
            return status
    if all(result.status == "PASS" for result in results):
        return "PASS"
    return "FAIL_TESTS"
