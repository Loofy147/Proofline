import unittest

from vap_lab.canonical import digest_bytes, digest_json
from vap_lab.replay import compare_replay_reports
from vap_lab.vap import build_vap


def make_vap(*, podman_version="5.0.0", stdout=b"ok\n", timestamp=1, task_id="task-1"):
    identity = {
        "podman_version": podman_version,
        "podman_api_version": "5.0.0",
        "oci_runtime_name": "crun",
        "oci_runtime_version": "crun version 1.16",
        "conmon_version": "conmon version 2.1",
        "cgroup_version": "v2",
        "rootless": True,
    }
    core = {
        "profile": "vap.verdict-core.v0.1",
        "task_id": task_id,
        "task_digest": digest_json({"task_id": task_id}),
        "source_digest": digest_json({"source": "candidate"}),
        "source_file_count": 1,
        "source_total_bytes": 10,
        "test_suite_digest": digest_json({"case": "one"}),
        "runtime_image": "registry.example/python@sha256:" + "a" * 64,
        "runner_version": "reproducibility-lab/0.1.0",
        "runtime_identity_digest": digest_json(identity),
        "policy_digest": digest_json({"policy": "fixed"}),
        "verdict": "PASS",
        "reason": "all_cases_passed",
        "cases_total": 1,
        "cases_attempted": 1,
        "cases_passed": 1,
        "case_results": [{
            "index": 0,
            "status": "PASS",
            "reason": "exact_output",
            "exit_code": 0,
            "stdout_digest": digest_bytes(stdout),
            "stderr_digest": digest_bytes(b""),
        }],
    }
    telemetry = {
        "total_wall_clock_ms": 1,
        "runtime_preflight": {
            "available": True,
            "message": "test fixture",
            "rootless_confirmed": True,
            "runtime_identity": identity,
        },
        "case_runs": [{
            "index": 0,
            "wall_clock_ms": 1,
            "captured_stdout_bytes": len(stdout),
            "captured_stderr_bytes": 0,
            "total_observed_output_bytes": len(stdout),
            "container_started": True,
            "oom_killed": False,
            "container_exit_code": 0,
            "cpu_time_ns": None,
            "peak_memory_bytes": None,
            "resource_measurement": "NOT_COLLECTED_IN_V0.1",
        }],
        "host_kernel": "test-kernel",
        "target_cpu_time_ns": None,
        "target_peak_memory_bytes": None,
        "resource_measurement_status": "NOT_COLLECTED_IN_V0.1",
    }
    run_id = "00000000-0000-4000-8000-" + f"{timestamp:012x}"
    return build_vap(core, telemetry, timestamp_utc=timestamp, run_id=run_id)


def report(label, *vaps):
    return {
        "schema_version": "vap.cross-runner-replay-report.v0.1",
        "runner_label": label,
        "results": [{"task_id": vap["verdict_core"]["task_id"], "vap": vap} for vap in vaps],
    }


class CrossRunnerReplayTests(unittest.TestCase):
    def test_ignores_run_timestamp_and_uuid_when_verdict_core_matches(self):
        first = make_vap(timestamp=1)
        second = make_vap(timestamp=2)
        result = compare_replay_reports(report("runner-a", first), report("runner-b", second))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["matched_case_count"], 1)

    def test_reports_runtime_identity_drift_as_a_verdict_core_difference(self):
        first = make_vap(podman_version="5.0.0")
        second = make_vap(podman_version="5.0.1")
        result = compare_replay_reports(report("runner-a", first), report("runner-b", second))
        self.assertEqual(result["status"], "MISMATCH")
        self.assertIn("runtime_identity_digest", result["mismatches"][0]["differences"])

    def test_reports_case_output_difference(self):
        first = make_vap(stdout=b"ok\n")
        second = make_vap(stdout=b"bad\n")
        result = compare_replay_reports(report("runner-a", first), report("runner-b", second))
        self.assertEqual(result["status"], "MISMATCH")
        self.assertIn("case_results", result["mismatches"][0]["differences"])

    def test_rejects_tampered_vap_even_if_report_is_well_formed(self):
        vap = make_vap()
        vap["verdict_core"]["reason"] = "tampered"
        with self.assertRaisesRegex(ValueError, "invalid or unverifiable VAP"):
            compare_replay_reports(report("runner-a", vap), report("runner-b", make_vap(timestamp=2)))

    def test_reports_missing_scenario(self):
        first = make_vap(task_id="task-1")
        second = make_vap(task_id="task-1")
        third = make_vap(task_id="task-2")
        result = compare_replay_reports(
            report("runner-a", first, third),
            report("runner-b", second),
        )
        self.assertEqual(result["status"], "MISMATCH")
        self.assertIn("missing_from_right", result["mismatches"][0]["differences"])


if __name__ == "__main__":
    unittest.main()
