import json
import tempfile
import unittest
from pathlib import Path

from vap_lab.runner import PodmanRootlessRunner, load_test_suite
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

    def test_command_mounts_only_the_submission_tree(self):
        command = self.runner._command(Path("/tmp/vap-stage"), "vap-test-run")
        volume_args = [command[i + 1] for i, arg in enumerate(command[:-1]) if arg == "--volume"]
        self.assertEqual(len(volume_args), 1)
        self.assertEqual(volume_args[0], "/tmp/vap-stage:/workspace:ro,Z")
        self.assertFalse(any("test" in argument.lower() for argument in volume_args))


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
