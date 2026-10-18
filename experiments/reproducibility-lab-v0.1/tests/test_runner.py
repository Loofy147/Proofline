import json
import tempfile
import unittest
from pathlib import Path

from vap_lab.runner import PodmanRootlessRunner, extract_runtime_identity, load_test_suite
from test_contract import VALID_TASK


class PodmanCommandTests(unittest.TestCase):
    def setUp(self):
        self.task = json.loads(json.dumps(VALID_TASK))
        self.runner = PodmanRootlessRunner(self.task, podman_binary="podman")

    def test_command_enforces_required_isolation_flags(self):
        command = self.runner._command(Path("/tmp/vap-stage"), "vap-test-run")
        joined = " ".join(command)
        for required in ("--pull=never", "--network=none", "--read-only", "--cap-drop=ALL", "--security-opt=no-new-privileges", "--pids-limit 32", "--memory 256m", "--cpus 1.0", "--user=65532:65532"):
            self.assertIn(required, joined)
        self.assertIn("registry.example/python@sha256:" + "a" * 64, command)
        self.assertEqual(command[command.index("--entrypoint") + 1], "python3")
        self.assertIn("--http-proxy=false", command)
        self.assertIn("--interactive", command)

    def test_command_mounts_only_the_submission_tree(self):
        command = self.runner._command(Path("/tmp/vap-stage"), "vap-test-run")
        volume_args = [command[i + 1] for i, arg in enumerate(command[:-1]) if arg == "--volume"]
        self.assertEqual(len(volume_args), 1)
        self.assertEqual(volume_args[0], "/tmp/vap-stage:/workspace:ro,Z")
        self.assertFalse(any("test" in argument.lower() for argument in volume_args))


class RuntimeIdentityTests(unittest.TestCase):
    def test_identity_captures_oci_runtime_and_conmon_from_podman_info(self):
        info = {
            "host": {
                "security": {"rootless": True},
                "cgroupVersion": "v2",
                "ociRuntime": {"name": "crun", "version": "crun version 1.16", "package": "crun-1.16"},
                "conmon": {"version": "conmon version 2.1", "package": "conmon-2.1"},
            }
        }
        version = {"Client": {"Version": "4.9.3", "APIVersion": "4.9.3"}}
        identity = extract_runtime_identity(info, version, cgroup_version="v2")
        self.assertEqual(identity["podman_version"], "4.9.3")
        self.assertEqual(identity["oci_runtime_name"], "crun")
        self.assertEqual(identity["oci_runtime_version"], "crun version 1.16")
        self.assertEqual(identity["conmon_version"], "conmon version 2.1")
        self.assertEqual(identity["cgroup_version"], "v2")
        self.assertIs(identity["rootless"], True)

    def test_missing_runtime_identity_is_rejected(self):
        info = {
            "host": {
                "security": {"rootless": True},
                "cgroupVersion": "v2",
                "ociRuntime": {},
                "conmon": {},
            }
        }
        version = {"Client": {"Version": "4.9.3", "APIVersion": "4.9.3"}}
        with self.assertRaisesRegex(ValueError, "runtime identity"):
            extract_runtime_identity(info, version, cgroup_version="v2")


class TestSuiteTests(unittest.TestCase):
    def test_valid_suite_digest_is_computed_from_canonical_content(self):
        fixture = Path(__file__).parents[1] / "examples" / "public-demo-tests.json"
        suite, digest = load_test_suite(fixture)
        self.assertEqual(suite["schema_version"], "vap.tests.v0.1")
        self.assertEqual(len(suite["cases"]), 2)
        self.assertRegex(digest, r"^sha256:[0-9a-f]{64}$")

    def test_unknown_test_case_fields_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            suite_path = Path(td) / "tests.json"
            suite_path.write_text(json.dumps({"schema_version": "vap.tests.v0.1", "cases": [{"stdin": "", "expected_stdout": "", "secret": "x"}]}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_test_suite(suite_path)


if __name__ == "__main__":
    unittest.main()
