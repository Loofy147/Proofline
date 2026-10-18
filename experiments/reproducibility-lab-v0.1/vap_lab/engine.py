"""End-to-end VAP run orchestration."""
from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from .canonical import digest_bytes, digest_json, load_json_strict
from .contract import policy_digest, validate_task
from .evaluator import aggregate_verdict
from .runner import PodmanRootlessRunner, load_test_suite
from .source import snapshot_source, stage_readonly_source
from .vap import build_vap

RUNNER_VERSION = "reproducibility-lab/0.1.0"


def _sha256(data: bytes) -> str:
    return digest_bytes(data)


def _cleanup_readonly_tree(path: Path) -> None:
    if not path.exists():
        return
    for current, dirs, files in os.walk(path, topdown=False):
        for filename in files:
            try:
                os.chmod(Path(current) / filename, 0o600)
            except OSError:
                pass
        for directory in dirs:
            try:
                os.chmod(Path(current) / directory, 0o700)
            except OSError:
                pass
        try:
            os.chmod(current, 0o700)
        except OSError:
            pass
    shutil.rmtree(path, ignore_errors=True)


def run_task(task_path: str | Path, submission_dir: str | Path, test_suite_path: str | Path) -> dict[str, Any]:
    task_raw = Path(task_path).read_bytes()
    task = load_json_strict(task_raw)
    validate_task(task)
    suite, suite_digest = load_test_suite(test_suite_path)
    if suite_digest != task["verification_policy"]["sealed_test_hash"]:
        raise ValueError("sealed test suite digest does not match committed task policy")

    limits = task["runtime_profile"]["limits"]
    source = snapshot_source(submission_dir, max_bytes=limits["max_source_bytes"], max_files=limits["max_source_files"])
    command = task["runtime_profile"]["command"]
    if len(command) > 1 and command[1].startswith("/workspace/"):
        relative_entrypoint = command[1][len("/workspace/"):]
        if not relative_entrypoint or ".." in Path(relative_entrypoint).parts or relative_entrypoint.startswith("/"):
            raise ValueError("invalid workspace entrypoint")
        if relative_entrypoint not in {entry["path"] for entry in source.entries}:
            raise ValueError("configured workspace entrypoint is missing from submission")
    task_digest = digest_json(task)
    runner = PodmanRootlessRunner(task)
    preflight = runner.preflight()
    results: list[dict[str, Any]] = []
    telemetry_cases: list[dict[str, Any]] = []
    total_started = time.monotonic_ns()

    if not preflight.available:
        verdict = "INFRASTRUCTURE_FAILURE"
        attempted = 0
        reason = "runtime_preflight_failed"
    else:
        # Staging is a fresh copy; original submission files are never mounted.
        parent = Path(tempfile.mkdtemp(prefix="vap-stage-parent-"))
        staged = parent / "source"
        try:
            stage_readonly_source(
                submission_dir,
                staged,
                max_bytes=limits["max_source_bytes"],
                max_files=limits["max_source_files"],
            )
            attempted = 0
            for index, case in enumerate(suite["cases"]):
                inp = case["stdin"].encode("utf-8")
                expected = case["expected_stdout"].encode("utf-8")
                if len(inp) > limits["max_input_bytes"]:
                    results.append({
                        "index": index,
                        "status": "RESOURCE_EXHAUSTED",
                        "reason": "input_size_limit",
                        "exit_code": None,
                        "stdout_digest": _sha256(b""),
                        "stderr_digest": _sha256(b""),
                    })
                    telemetry_cases.append({"index": index, "wall_clock_ms": 0, "captured_stdout_bytes": 0, "captured_stderr_bytes": 0, "total_observed_output_bytes": 0, "container_started": False, "oom_killed": None, "container_exit_code": None, "cpu_time_ns": None, "peak_memory_bytes": None, "resource_measurement": "NOT_COLLECTED_IN_V0.1"})
                    attempted += 1
                    break
                result = runner.run_case(staged, inp, expected)
                attempted += 1
                results.append({
                    "index": index,
                    "status": result.case_result.status,
                    "reason": result.case_result.reason,
                    "exit_code": result.case_result.exit_code,
                    "stdout_digest": _sha256(result.case_result.stdout),
                    "stderr_digest": _sha256(result.case_result.stderr),
                })
                telemetry_cases.append({
                    "index": index,
                    "wall_clock_ms": result.telemetry.wall_clock_ms,
                    "captured_stdout_bytes": result.telemetry.stdout_bytes,
                    "captured_stderr_bytes": result.telemetry.stderr_bytes,
                    "total_observed_output_bytes": result.telemetry.total_observed_output_bytes,
                    "container_started": result.telemetry.container_started,
                    "oom_killed": result.telemetry.oom_killed,
                    "container_exit_code": result.telemetry.container_exit_code,
                    "cpu_time_ns": result.telemetry.cpu_time_ns,
                    "peak_memory_bytes": result.telemetry.peak_memory_bytes,
                    "resource_measurement": result.telemetry.cpu_memory_measurement,
                })
                if result.case_result.status != "PASS":
                    break
            verdict = aggregate_verdict([
                _case_result_from_summary(item) for item in results
            ])
            reason = "all_cases_passed" if verdict == "PASS" else "first_nonpass_case"
        finally:
            _cleanup_readonly_tree(parent)

    wall_total_ms = (time.monotonic_ns() - total_started) // 1_000_000
    core = {
        "profile": "vap.verdict-core.v0.1",
        "task_id": task["task_id"],
        "task_digest": task_digest,
        "source_digest": source.digest,
        "source_file_count": source.file_count,
        "source_total_bytes": source.total_bytes,
        "test_suite_digest": suite_digest,
        "runtime_image": task["runtime_profile"]["image"],
        "runner_version": RUNNER_VERSION,
        "runtime_identity_digest": digest_json(preflight.runtime_identity) if preflight.runtime_identity else None,
        "policy_digest": policy_digest(task),
        "verdict": verdict,
        "reason": reason,
        "cases_total": len(suite["cases"]),
        "cases_attempted": attempted,
        "cases_passed": sum(1 for row in results if row["status"] == "PASS"),
        "case_results": results,
    }
    telemetry = {
        "total_wall_clock_ms": int(wall_total_ms),
        "runtime_preflight": {
            "available": preflight.available,
            "message": preflight.message,
            "rootless_confirmed": preflight.rootless,
            "runtime_identity": preflight.runtime_identity,
        },
        "case_runs": telemetry_cases,
        "host_kernel": os.uname().release if hasattr(os, "uname") else None,
        "target_cpu_time_ns": None,
        "target_peak_memory_bytes": None,
        "resource_measurement_status": "NOT_COLLECTED_IN_V0.1",
    }
    return build_vap(core, telemetry)


def _case_result_from_summary(summary: dict[str, Any]):
    from .evaluator import CaseResult
    return CaseResult(summary["status"], summary.get("exit_code"), b"", b"", summary.get("reason", "unknown"))
