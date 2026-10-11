import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RepositoryContractTests(unittest.TestCase):
    def test_repository_validator_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_repo.py")],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("REPOSITORY VALIDATION: PASS", result.stdout)

    def test_review_protocol_requires_not_tested_state(self):
        text = (ROOT / "docs" / "REVIEW_PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("NOT TESTED", text)
        self.assertIn("BLOCKED", text)
        self.assertIn("Two models agreeing is not proof.", text)

    def test_ci_runs_for_pull_requests_and_is_read_only(self):
        text = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("pull_request:", text)
        self.assertIn("contents: read", text)
        self.assertIn("persist-credentials: false", text)

if __name__ == "__main__":
    unittest.main(verbosity=2)
