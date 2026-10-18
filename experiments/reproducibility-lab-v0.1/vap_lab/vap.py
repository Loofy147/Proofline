"""VAP v0.1 document construction and digest verification."""
from __future__ import annotations

import re
import time
import uuid
from typing import Any

from .canonical import digest_json
from .evaluator import STATUSES


_PROFILES = {
    "vap.verdict-core.v0.1": ("vap.attestation.v0.1", "vap-verdict-core-v0.1"),
    "vap.verdict-core.v0.2": ("vap.attestation.v0.2", "vap-verdict-core-v0.2"),
}


def verdict_digest(core: dict[str, Any]) -> str:
    if core.get("verdict") not in STATUSES:
        raise ValueError("unknown verdict status")
    profile = core.get("profile")
    if profile not in _PROFILES:
        raise ValueError("unsupported verdict-core profile")
    return digest_json({"domain": _PROFILES[profile][1], "core": core})


def build_vap(core: dict[str, Any], telemetry: dict[str, Any], *, timestamp_utc: int | None = None, run_id: str | None = None) -> dict[str, Any]:
    if core.get("verdict") not in STATUSES:
        raise ValueError("unknown verdict status")
    profile = core.get("profile")
    if profile not in _PROFILES:
        raise ValueError("unsupported verdict-core profile")
    stamp = int(time.time()) if timestamp_utc is None else timestamp_utc
    return {
        "schema_version": _PROFILES[profile][0],
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


def _is_nonnegative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_telemetry(telemetry: Any, core: dict[str, Any]) -> bool:
    """Validate telemetry structure and per-profile metric invariants.

    VAP telemetry is unsigned and excluded from the verdict digest. Validation
    detects inconsistencies but does not authenticate the reported measurements.
    """
    telemetry_fields = {
        "total_wall_clock_ms", "runtime_preflight", "case_runs", "host_kernel",
        "target_cpu_time_ns", "target_peak_memory_bytes", "resource_measurement_status",
    }
    if not isinstance(telemetry, dict) or set(telemetry) != telemetry_fields:
        return False
    if not _is_nonnegative_int(telemetry.get("total_wall_clock_ms")):
        return False
    if telemetry.get("host_kernel") is not None and not isinstance(telemetry.get("host_kernel"), str):
        return False
    for field in ("target_cpu_time_ns", "target_peak_memory_bytes"):
        if not (telemetry.get(field) is None or _is_nonnegative_int(telemetry.get(field))):
            return False

    profile = core.get("profile")
    if profile == "vap.verdict-core.v0.1":
        if telemetry.get("resource_measurement_status") != "NOT_COLLECTED_IN_V0.1":
            return False
        if telemetry["target_cpu_time_ns"] is not None or telemetry["target_peak_memory_bytes"] is not None:
            return False
    elif profile == "vap.verdict-core.v0.2":
        if telemetry.get("resource_measurement_status") not in {"COLLECTED", "PARTIAL", "UNAVAILABLE", "NOT_RUN"}:
            return False
    else:
        return False

    preflight = telemetry.get("runtime_preflight")
    preflight_fields = {"available", "message", "rootless_confirmed", "runtime_identity"}
    if not isinstance(preflight, dict) or set(preflight) != preflight_fields:
        return False
    if not isinstance(preflight.get("available"), bool) or not isinstance(preflight.get("message"), str):
        return False
    rootless_confirmed = preflight.get("rootless_confirmed")
    if rootless_confirmed is not None and not isinstance(rootless_confirmed, bool):
        return False

    runtime_identity = preflight.get("runtime_identity")
    if runtime_identity is None:
        if core.get("runtime_identity_digest") is not None:
            return False
    else:
        identity_fields = {
            "podman_version", "podman_api_version", "oci_runtime_name",
            "oci_runtime_version", "conmon_version", "cgroup_version", "rootless",
        }
        if not isinstance(runtime_identity, dict) or set(runtime_identity) != identity_fields:
            return False
        for field in ("podman_version", "oci_runtime_name", "oci_runtime_version", "conmon_version", "cgroup_version"):
            if not isinstance(runtime_identity.get(field), str) or not runtime_identity[field]:
                return False
        api_version = runtime_identity.get("podman_api_version")
        if api_version is not None and not isinstance(api_version, str):
            return False
        if not isinstance(runtime_identity.get("rootless"), bool):
            return False
        try:
            if digest_json(runtime_identity) != core.get("runtime_identity_digest"):
                return False
        except (TypeError, ValueError):
            return False
    if preflight["available"]:
        if rootless_confirmed is not True or runtime_identity is None:
            return False
        if runtime_identity.get("rootless") is not True or runtime_identity.get("cgroup_version") != "v2":
            return False
    elif core.get("cases_attempted") != 0:
        return False

    case_runs = telemetry.get("case_runs")
    if not isinstance(case_runs, list) or len(case_runs) != core.get("cases_attempted"):
        return False
    case_telemetry_fields = {
        "index", "wall_clock_ms", "captured_stdout_bytes", "captured_stderr_bytes",
        "total_observed_output_bytes", "container_started", "oom_killed",
        "container_exit_code", "cpu_time_ns", "peak_memory_bytes", "resource_measurement",
    }
    for index, item in enumerate(case_runs):
        if not isinstance(item, dict) or set(item) != case_telemetry_fields:
            return False
        if item.get("index") != index:
            return False
        for field in ("wall_clock_ms", "captured_stdout_bytes", "captured_stderr_bytes", "total_observed_output_bytes"):
            if not _is_nonnegative_int(item.get(field)):
                return False
        if item["captured_stdout_bytes"] + item["captured_stderr_bytes"] > item["total_observed_output_bytes"]:
            return False
        if not isinstance(item.get("container_started"), bool):
            return False
        oom_killed = item.get("oom_killed")
        if oom_killed is not None and not isinstance(oom_killed, bool):
            return False
        exit_code = item.get("container_exit_code")
        if exit_code is not None and (not isinstance(exit_code, int) or isinstance(exit_code, bool)):
            return False

        cpu_time = item.get("cpu_time_ns")
        peak_memory = item.get("peak_memory_bytes")
        for value in (cpu_time, peak_memory):
            if value is not None and not _is_nonnegative_int(value):
                return False
        measurement = item.get("resource_measurement")
        if profile == "vap.verdict-core.v0.1":
            if cpu_time is not None or peak_memory is not None:
                return False
            if measurement != "NOT_COLLECTED_IN_V0.1":
                return False
        else:
            both_measured = cpu_time is not None and peak_memory is not None
            one_measured = (cpu_time is None) != (peak_memory is None)
            if measurement == "CGROUP_V2_MEASURED":
                if not both_measured:
                    return False
            elif measurement == "CGROUP_V2_PARTIAL":
                if not one_measured:
                    return False
            elif measurement == "UNAVAILABLE":
                if cpu_time is not None or peak_memory is not None:
                    return False
            elif measurement == "NOT_RUN":
                if cpu_time is not None or peak_memory is not None or item["container_started"]:
                    return False
            else:
                return False

    if profile == "vap.verdict-core.v0.2":
        statuses = [item["resource_measurement"] for item in case_runs]
        has_any_metric = any(
            item["cpu_time_ns"] is not None or item["peak_memory_bytes"] is not None
            for item in case_runs
        )
        all_measured = bool(case_runs) and all(
            item["resource_measurement"] == "CGROUP_V2_MEASURED"
            for item in case_runs
        )
        all_not_run = bool(case_runs) and all(status == "NOT_RUN" for status in statuses)
        top_status = telemetry["resource_measurement_status"]
        cpu_total = sum(item["cpu_time_ns"] for item in case_runs) if all_measured else None
        memory_peak = max((item["peak_memory_bytes"] for item in case_runs), default=None) if all_measured else None

        if top_status == "COLLECTED":
            if not all_measured or telemetry["target_cpu_time_ns"] != cpu_total:
                return False
            if telemetry["target_peak_memory_bytes"] != memory_peak:
                return False
        elif top_status == "PARTIAL":
            if not has_any_metric or all_measured:
                return False
            if telemetry["target_cpu_time_ns"] is not None or telemetry["target_peak_memory_bytes"] is not None:
                return False
        elif top_status == "UNAVAILABLE":
            if has_any_metric or not case_runs or all_not_run:
                return False
            if telemetry["target_cpu_time_ns"] is not None or telemetry["target_peak_memory_bytes"] is not None:
                return False
        elif top_status == "NOT_RUN":
            if not (core.get("cases_attempted") == 0 or all_not_run):
                return False
            if telemetry["target_cpu_time_ns"] is not None or telemetry["target_peak_memory_bytes"] is not None:
                return False
    return True

def verify_vap_document(vap: dict[str, Any]) -> bool:
    """Validate VAP v0.1 or v0.2 structure and recompute its verdict digest.

    Both profiles are unsigned prototypes. Structural verification never
    authenticates telemetry, a signer, or authorizes financial settlement.
    """
    if not isinstance(vap, dict):
        return False
    required = {"schema_version", "run_id", "timestamp_utc", "verdict_core", "verdict_digest", "telemetry", "attestation"}
    if set(vap) != required:
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
    if not isinstance(core, dict):
        return False
    profile = core.get("profile")
    if profile not in _PROFILES or vap.get("schema_version") != _PROFILES[profile][0]:
        return False
    core_fields = {
        "profile", "task_id", "task_digest", "source_digest", "source_file_count", "source_total_bytes",
        "test_suite_digest", "runtime_image", "runner_version", "runtime_identity_digest", "policy_digest", "verdict", "reason",
        "cases_total", "cases_attempted", "cases_passed", "case_results"
    }
    if set(core) != core_fields:
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
    if not _valid_telemetry(vap.get("telemetry"), core):
        return False
    if core["cases_attempted"] == 0:
        if core["verdict"] != "INFRASTRUCTURE_FAILURE" or case_results:
            return False
    elif core["verdict"] != aggregate_status(case_results):
        return False

    attestation = vap.get("attestation")
    if not isinstance(attestation, dict) or set(attestation) != {"status", "algorithm", "signer", "signature"}:
        return False
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
