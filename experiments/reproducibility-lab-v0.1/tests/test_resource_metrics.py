import tempfile
import unittest
from pathlib import Path

from vap_lab.resource_metrics import (
    cgroup_v2_path_for_pid,
    read_cgroup_v2_metrics,
)
from vap_lab.vap import build_vap, verify_vap_document
from vap_lab.canonical import digest_bytes, digest_json


def make_v02_vap():
    identity = {
        "podman_version": "5.0.0",
        "podman_api_version": "5.0.0",
        "oci_runtime_name": "crun",
        "oci_runtime_version": "crun version 1.16",
        "conmon_version": "conmon version 2.1",
        "cgroup_version": "v2",
        "rootless": True,
    }
    core = {
        "profile": "vap.verdict-core.v0.2",
        "task_id": "resource-metrics-task",
        "task_digest": digest_json({"task": 1}),
        "source_digest": digest_json({"source": 1}),
        "source_file_count": 1,
        "source_total_bytes": 12,
        "test_suite_digest": digest_json({"tests": 1}),
        "runtime_image": "registry.example/python@sha256:" + "a" * 64,
        "runner_version": "reproducibility-lab/0.2.0",
        "runtime_identity_digest": digest_json(identity),
        "policy_digest": digest_json({"policy": 1}),
        "verdict": "PASS",
        "reason": "all_cases_passed",
        "cases_total": 1,
        "cases_attempted": 1,
        "cases_passed": 1,
        "case_results": [{
            "index": 0, "status": "PASS", "reason": "exact_output",
            "exit_code": 0, "stdout_digest": digest_bytes(b"ok\n"),
            "stderr_digest": digest_bytes(b""),
        }],
    }
    telemetry = {
        "total_wall_clock_ms": 45,
        "runtime_preflight": {
            "available": True, "message": "test fixture",
            "rootless_confirmed": True, "runtime_identity": identity,
        },
        "case_runs": [{
            "index": 0, "wall_clock_ms": 45,
            "captured_stdout_bytes": 3, "captured_stderr_bytes": 0,
            "total_observed_output_bytes": 3, "container_started": True,
            "oom_killed": False, "container_exit_code": 0,
            "cpu_time_ns": 12000, "peak_memory_bytes": 8192,
            "resource_measurement": "CGROUP_V2_MEASURED",
        }],
        "host_kernel": "test-kernel",
        "target_cpu_time_ns": 12000,
        "target_peak_memory_bytes": 8192,
        "resource_measurement_status": "COLLECTED",
    }
    return build_vap(core, telemetry, timestamp_utc=1,
                     run_id="00000000-0000-4000-8000-000000000001")


class CgroupV2PathTests(unittest.TestCase):
    def test_resolves_only_the_pid_cgroup_under_the_supplied_mount(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cgroup_root = root / "cgroups"
            proc_root = root / "proc"
            leaf = cgroup_root / "user.slice" / "libpod-test"
            leaf.mkdir(parents=True)
            (proc_root / "1234").mkdir(parents=True)
            (proc_root / "1234" / "cgroup").write_text(
                "0::/user.slice/libpod-test\n", encoding="utf-8"
            )
            self.assertEqual(
                cgroup_v2_path_for_pid(1234, cgroups_root=cgroup_root, proc_root=proc_root),
                leaf.resolve(),
            )

    def test_rejects_parent_traversal_in_proc_cgroup_path(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cgroup_root = root / "cgroups"
            cgroup_root.mkdir()
            (root / "proc" / "1234").mkdir(parents=True)
            (root / "proc" / "1234" / "cgroup").write_text(
                "0::/../../outside\n", encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                cgroup_v2_path_for_pid(
                    1234, cgroups_root=cgroup_root, proc_root=root / "proc"
                )

    def test_rejects_missing_pid_or_non_unified_hierarchy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            cgroup_root = root / "cgroups"
            cgroup_root.mkdir()
            proc_root = root / "proc"
            (proc_root / "1234").mkdir(parents=True)
            (proc_root / "1234" / "cgroup").write_text(
                "2:cpu,cpuacct:/group\n", encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                cgroup_v2_path_for_pid(
                    1234, cgroups_root=cgroup_root, proc_root=proc_root
                )
            with self.assertRaises(ValueError):
                cgroup_v2_path_for_pid(
                    0, cgroups_root=cgroup_root, proc_root=proc_root
                )


class CgroupV2CounterTests(unittest.TestCase):
    def test_reads_cpu_usage_usec_as_nanoseconds_and_memory_peak_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            cgroup = Path(temp)
            (cgroup / "cpu.stat").write_text(
                "usage_usec 123\nuser_usec 100\nsystem_usec 23\n",
                encoding="utf-8",
            )
            (cgroup / "memory.peak").write_text("8192\n", encoding="utf-8")
            measured = read_cgroup_v2_metrics(cgroup)
            self.assertEqual(measured.cpu_time_ns, 123000)
            self.assertEqual(measured.peak_memory_bytes, 8192)
            self.assertEqual(measured.status, "CGROUP_V2_MEASURED")

    def test_missing_or_malformed_counter_is_not_reported_as_zero(self):
        with tempfile.TemporaryDirectory() as temp:
            cgroup = Path(temp)
            (cgroup / "cpu.stat").write_text("usage_usec invalid\n", encoding="utf-8")
            measured = read_cgroup_v2_metrics(cgroup)
            self.assertIsNone(measured.cpu_time_ns)
            self.assertIsNone(measured.peak_memory_bytes)
            self.assertEqual(measured.status, "UNAVAILABLE")

    def test_one_valid_counter_is_explicitly_partial(self):
        with tempfile.TemporaryDirectory() as temp:
            cgroup = Path(temp)
            (cgroup / "cpu.stat").write_text("usage_usec 4\n", encoding="utf-8")
            measured = read_cgroup_v2_metrics(cgroup)
            self.assertEqual(measured.cpu_time_ns, 4000)
            self.assertIsNone(measured.peak_memory_bytes)
            self.assertEqual(measured.status, "CGROUP_V2_PARTIAL")


class VAPV02ResourceContractTests(unittest.TestCase):
    def test_builds_and_verifies_v02_with_consistent_resource_totals(self):
        vap = make_v02_vap()
        self.assertEqual(vap["schema_version"], "vap.attestation.v0.2")
        self.assertTrue(verify_vap_document(vap))

    def test_rejects_resource_total_that_disagrees_with_per_case_measurement(self):
        vap = make_v02_vap()
        vap["telemetry"]["target_cpu_time_ns"] = 12001
        self.assertFalse(verify_vap_document(vap))

    def test_keeps_unavailable_metrics_null_not_zero(self):
        vap = make_v02_vap()
        run = vap["telemetry"]["case_runs"][0]
        run["cpu_time_ns"] = None
        run["peak_memory_bytes"] = None
        run["resource_measurement"] = "UNAVAILABLE"
        vap["telemetry"]["target_cpu_time_ns"] = None
        vap["telemetry"]["target_peak_memory_bytes"] = None
        vap["telemetry"]["resource_measurement_status"] = "UNAVAILABLE"
        self.assertTrue(verify_vap_document(vap))


if __name__ == "__main__":
    unittest.main()
