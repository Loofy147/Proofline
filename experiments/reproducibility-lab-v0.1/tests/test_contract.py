import json
import tempfile
import unittest
from pathlib import Path

from vap_lab.canonical import canonical_bytes, digest_json, load_json_strict
from vap_lab.contract import validate_task
from vap_lab.evaluator import classify_case
from vap_lab.vap import build_vap, verdict_digest
from vap_lab.source import snapshot_source
from vap_lab.runner import PodmanRootlessRunner
from vap_lab.vap import verify_vap_document


VALID_TASK = {
    "schema_version": "vap.task.v0.1",
    "task_id": "unit-test-001",
    "runtime_profile": {
        "engine": "podman-rootless",
        "image": "registry.example/python@sha256:" + "a" * 64,
        "network": "none",
        "read_only_rootfs": True,
        "cap_drop": ["ALL"],
        "tmpfs_mb": 16,
        "limits": {
            "timeout_seconds": 5,
            "memory_mb": 256,
            "cpus": "1.0",
            "pids_max": 32,
            "max_output_bytes": 65536,
            "max_input_bytes": 65536,
            "max_source_bytes": 1048576,
            "max_source_files": 64,
        },
        "command": ["python3", "/workspace/solution.py"],
    },
    "verification_policy": {
        "sealed_test_hash": "sha256:" + "b" * 64,
        "protocol": "stdin_stdout_exact_v1",
    },
}


class CanonicalJsonTests(unittest.TestCase):
    def test_canonical_bytes_ignore_object_key_order(self):
        self.assertEqual(canonical_bytes({"b": 2, "a": 1}), b'{"a":1,"b":2}')

    def test_float_values_are_rejected(self):
        with self.assertRaises(ValueError):
            canonical_bytes({"unsafe": 0.1})

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            load_json_strict('{"x":1,"x":2}')

    def test_digest_json_is_stable(self):
        self.assertEqual(digest_json({"x": "é"}), digest_json({"x": "e\u0301"}))


class TaskContractTests(unittest.TestCase):
    def test_valid_task_passes(self):
        validate_task(VALID_TASK)

    def test_mutable_image_tag_is_rejected(self):
        task = json.loads(json.dumps(VALID_TASK))
        task["runtime_profile"]["image"] = "python:latest"
        with self.assertRaises(ValueError):
            validate_task(task)

    def test_network_enabled_task_is_rejected(self):
        task = json.loads(json.dumps(VALID_TASK))
        task["runtime_profile"]["network"] = "bridge"
        with self.assertRaises(ValueError):
            validate_task(task)

    def test_extra_command_shell_is_rejected(self):
        task = json.loads(json.dumps(VALID_TASK))
        task["runtime_profile"]["command"] = ["sh", "-c", "python3 /workspace/solution.py"]
        with self.assertRaises(ValueError):
            validate_task(task)

    def test_inline_code_command_is_rejected(self):
        task = json.loads(json.dumps(VALID_TASK))
        task["runtime_profile"]["command"] = ["python3", "-c", "print(1)"]
        with self.assertRaises(ValueError):
            validate_task(task)

    def test_busybox_shell_applet_is_rejected(self):
        task = json.loads(json.dumps(VALID_TASK))
        task["runtime_profile"]["command"] = ["busybox", "sh", "-c", "python3 /workspace/solution.py"]
        with self.assertRaises(ValueError):
            validate_task(task)

    def test_env_shell_launcher_is_rejected(self):
        task = json.loads(json.dumps(VALID_TASK))
        task["runtime_profile"]["command"] = ["env", "bash", "-c", "python3 /workspace/solution.py"]
        with self.assertRaises(ValueError):
            validate_task(task)

    def test_env_split_string_shell_launcher_is_rejected(self):
        task = json.loads(json.dumps(VALID_TASK))
        task["runtime_profile"]["command"] = ["env", "-S", "bash -c 'python3 /workspace/solution.py'"]
        with self.assertRaises(ValueError):
            validate_task(task)

    def test_preflight_fails_closed_without_podman(self):
        runner = PodmanRootlessRunner(VALID_TASK, podman_binary="/no/such/podman")
        self.assertFalse(runner.preflight().available)


class VerdictTests(unittest.TestCase):
    def test_permission_error_text_is_not_security_evidence(self):
        result = classify_case(return_code=13, stdout=b"", stderr=b"PermissionError", expected=b"ok\n")
        self.assertEqual(result.status, "FAIL_TESTS")

    def test_success_requires_zero_exit_and_exact_output(self):
        self.assertEqual(classify_case(return_code=0, stdout=b"ok\n", stderr=b"", expected=b"ok\n").status, "PASS")
        self.assertEqual(classify_case(return_code=0, stdout=b"ok", stderr=b"", expected=b"ok\n").status, "FAIL_TESTS")

    def test_nonzero_exit_is_fail_not_policy_violation(self):
        result = classify_case(return_code=1, stdout=b"", stderr=b"denied", expected=b"ok\n")
        self.assertEqual(result.status, "FAIL_TESTS")

    def test_resource_limit_is_separate_from_test_failure(self):
        result = classify_case(return_code=None, stdout=b"", stderr=b"", expected=b"ok", termination="timeout")
        self.assertEqual(result.status, "RESOURCE_EXHAUSTED")

    def test_policy_violation_requires_external_confirmed_observation(self):
        result = classify_case(return_code=1, stdout=b"", stderr=b"", expected=b"ok", confirmed_policy_violation=True)
        self.assertEqual(result.status, "POLICY_VIOLATION")

    def test_infrastructure_failure_is_not_a_code_verdict(self):
        result = classify_case(return_code=None, stdout=b"", stderr=b"", expected=b"ok", termination="infrastructure")
        self.assertEqual(result.status, "INFRASTRUCTURE_FAILURE")

    def test_verdict_digest_excludes_telemetry_and_timestamps(self):
        core = {
            "profile": "vap.verdict-core.v0.1", "task_id": "t1",
            "task_digest": "sha256:" + "c" * 64,
            "source_digest": "sha256:" + "a" * 64,
            "source_file_count": 1, "source_total_bytes": 1,
            "test_suite_digest": "sha256:" + "b" * 64,
            "runtime_image": "registry.example/python@sha256:" + "d" * 64,
            "runner_version": "test", "runtime_identity_digest": "sha256:" + "1" * 64, "policy_digest": "sha256:" + "e" * 64,
            "verdict": "PASS", "reason": "all_cases_passed",
            "cases_total": 1, "cases_attempted": 1, "cases_passed": 1,
            "case_results": [{
                "index": 0, "status": "PASS", "reason": "exact_output_match", "exit_code": 0,
                "stdout_digest": "sha256:" + "f" * 64, "stderr_digest": "sha256:" + "0" * 64,
            }],
        }
        self.assertEqual(verdict_digest(core), verdict_digest(core))
        self.assertEqual(len({verdict_digest(core) for _ in range(100)}), 1)
        original_digest = verdict_digest(core)
        changed_runtime = dict(core, runtime_identity_digest="sha256:" + "2" * 64)
        self.assertNotEqual(original_digest, verdict_digest(changed_runtime))
        vap_a = build_vap(core, {"wall_ms": 10}, timestamp_utc=100)
        vap_b = build_vap(core, {"wall_ms": 99}, timestamp_utc=999)
        self.assertEqual(vap_a["verdict_digest"], vap_b["verdict_digest"])
        self.assertNotEqual(vap_a["telemetry"], vap_b["telemetry"])
        self.assertTrue(verify_vap_document(vap_a))
        vap_b["verdict_core"]["verdict"] = "FAIL_TESTS"
        self.assertFalse(verify_vap_document(vap_b))


class SourceSnapshotTests(unittest.TestCase):
    def test_source_snapshot_is_stable(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "solution.py").write_text("print('x')\n", encoding="utf-8")
            first = snapshot_source(root, max_bytes=1024, max_files=8)
            second = snapshot_source(root, max_bytes=1024, max_files=8)
            self.assertEqual(first.digest, second.digest)
            self.assertEqual(first.file_count, 1)

    def test_symlink_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "src"
            root.mkdir()
            outside = Path(td) / "outside.txt"
            outside.write_text("secret", encoding="utf-8")
            (root / "link.txt").symlink_to(outside)
            with self.assertRaises(ValueError):
                snapshot_source(root, max_bytes=1024, max_files=8)

    def test_git_metadata_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("credential=not-for-submission", encoding="utf-8")
            with self.assertRaises(ValueError):
                snapshot_source(root, max_bytes=1024, max_files=8)


if __name__ == "__main__":
    unittest.main()
