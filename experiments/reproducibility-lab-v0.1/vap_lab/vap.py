"""VAP v0.1 document construction and digest verification."""
from __future__ import annotations

import re
import time
import uuid
from typing import Any

from .canonical import digest_json
from .evaluator import STATUSES


def verdict_digest(core: dict[str, Any]) -> str:
    if core.get("verdict") not in STATUSES:
        raise ValueError("unknown verdict status")
    return digest_json({"domain": "vap-verdict-core-v0.1", "core": core})


def build_vap(core: dict[str, Any], telemetry: dict[str, Any], *, timestamp_utc: int | None = None, run_id: str | None = None) -> dict[str, Any]:
    if core.get("verdict") not in STATUSES:
        raise ValueError("unknown verdict status")
    stamp = int(time.time()) if timestamp_utc is None else timestamp_utc
    return {
        "schema_version": "vap.attestation.v0.1",
        "run_id": run_id or str(uuid.uuid4()),
        "timestamp_utc": stamp,
        "verdict_core": core,
        "verdict_digest": verdict_digest(core),
        "telemetry": telemetry,
        "attestation": {
            "status": "UNSIGNED_LOCAL_PROTOTYPE",
            "algorithm": None,
            "signer": None,
            "signature": None,
        },
    }


def verify_vap_document(vap: dict[str, Any]) -> bool:
    """Validate the v0.1 envelope and recompute its verdict digest.

    This verifies structure/integrity only. It does not authenticate a signer
    or authorize settlement.
    """
    if not isinstance(vap, dict):
        return False
    required = {"schema_version", "run_id", "timestamp_utc", "verdict_core", "verdict_digest", "telemetry", "attestation"}
    if set(vap) != required or vap.get("schema_version") != "vap.attestation.v0.1":
        return False
    if not isinstance(vap.get("timestamp_utc"), int) or isinstance(vap.get("timestamp_utc"), bool) or vap["timestamp_utc"] < 0:
        return False
    if not isinstance(vap.get("run_id"), str) or not isinstance(vap.get("telemetry"), dict):
        return False
    try:
        uuid.UUID(vap["run_id"])
    except (ValueError, AttributeError):
        return False

    core = vap.get("verdict_core")
    core_fields = {
        "profile", "task_id", "task_digest", "source_digest", "source_file_count", "source_total_bytes",
        "test_suite_digest", "runtime_image", "runner_version", "runtime_identity_digest", "policy_digest", "verdict", "reason",
        "cases_total", "cases_attempted", "cases_passed", "case_results"
    }
    if not isinstance(core, dict) or set(core) != core_fields or core.get("profile") != "vap.verdict-core.v0.1":
        return False
    if core.get("verdict") not in STATUSES or not isinstance(core.get("case_results"), list):
        return False
    for field in ("task_digest", "source_digest", "test_suite_digest", "policy_digest"):
        value = core.get(field)
        if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
            return False
        if any(ch not in "0123456789abcdef" for ch in value[7:]):
            return False
    runtime_digest = core.get("runtime_identity_digest")
    if runtime_digest is not None and (not isinstance(runtime_digest, str) or len(runtime_digest) != 71 or not runtime_digest.startswith("sha256:") or any(ch not in "0123456789abcdef" for ch in runtime_digest[7:])):
        return False
    image = core.get("runtime_image")
    if not isinstance(image, str) or not re.fullmatch(r"[A-Za-z0-9._/:+-]+@sha256:[0-9a-f]{64}", image):
        return False
    for field in ("source_file_count", "source_total_bytes", "cases_total", "cases_attempted", "cases_passed"):
        value = core.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return False
    if not isinstance(core.get("task_id"), str) or not isinstance(core.get("runner_version"), str) or not isinstance(core.get("reason"), str):
        return False
    case_results = core["case_results"]
    if core["source_file_count"] < 1 or core["cases_total"] < 1 or core["cases_attempted"] != len(case_results):
        return False
    if core["cases_attempted"] > core["cases_total"] or core["cases_passed"] > core["cases_attempted"]:
        return False
    case_fields = {"index", "status", "reason", "exit_code", "stdout_digest", "stderr_digest"}
    for index, case in enumerate(case_results):
        if not isinstance(case, dict) or set(case) != case_fields:
            return False
        if case.get("index") != index or case.get("status") not in STATUSES or not isinstance(case.get("reason"), str):
            return False
        if case.get("exit_code") is not None and (not isinstance(case.get("exit_code"), int) or isinstance(case.get("exit_code"), bool)):
            return False
        for field in ("stdout_digest", "stderr_digest"):
            value = case.get(field)
            if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:") or any(ch not in "0123456789abcdef" for ch in value[7:]):
                return False
    if sum(1 for case in case_results if case["status"] == "PASS") != core["cases_passed"]:
        return False
    if core["cases_attempted"] == 0:
        if core["verdict"] != "INFRASTRUCTURE_FAILURE" or case_results:
            return False
    elif core["verdict"] != aggregate_status(case_results):
        return False

    attestation = vap.get("attestation")
    if not isinstance(attestation, dict) or set(attestation) != {"status", "algorithm", "signer", "signature"}:
        return False
    # v0.1 deliberately accepts only the unsigned prototype envelope.
    if attestation != {"status": "UNSIGNED_LOCAL_PROTOTYPE", "algorithm": None, "signer": None, "signature": None}:
        return False
    try:
        return vap.get("verdict_digest") == verdict_digest(core)
    except (KeyError, TypeError, ValueError):
        return False


def aggregate_status(case_results: list[dict[str, Any]]) -> str:
    statuses = [case["status"] for case in case_results]
    for status in ("POLICY_VIOLATION", "RESOURCE_EXHAUSTED", "INFRASTRUCTURE_FAILURE", "INVALID_SUBMISSION"):
        if status in statuses:
            return status
    if all(status == "PASS" for status in statuses):
        return "PASS"
    return "FAIL_TESTS"
