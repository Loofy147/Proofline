import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PackageIntegrityTests(unittest.TestCase):
    def test_app_and_cli_are_present(self):
        self.assertTrue((ROOT / "index.html").is_file())
        self.assertTrue((ROOT / "verify_csv.py").is_file())

    def test_readme_documentation_links_resolve(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        linked = [
            "docs/architecture/OVERVIEW.md",
            "docs/CI_CD.md",
            "docs/QUALITY_GATES.md",
            "docs/OPERATING_MODEL.md",
            "docs/review/REVIEW_PROTOCOL.md",
            "docs/context/AGENT_START_HERE.md",
            "docs/context/PROJECT_CONTEXT.md",
            "docs/context/EXTERNAL_CONTEXT.md",
            "docs/ARTIFACT_CATALOG.md",
            "docs/LICENSING_BEFORE_PUBLIC_RELEASE.md",
            "docs/RISK_REGISTER.md",
            "docs/RELEASE_CHECKLIST.md",
            "PRODUCT_STRATEGY.md",
            "PILOT_OFFER.md",
        ]
        for path in linked:
            with self.subTest(path=path):
                self.assertIn(path, readme)
                self.assertTrue((ROOT / path).is_file(), f"README link target missing: {path}")

    def test_demo_fixture_is_synthetic_and_declared(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        self.assertIn("synthetic", readme)
        fixture = ROOT / "examples" / "demo_sales.csv"
        self.assertTrue(fixture.is_file())
        self.assertIn("unit_price_usd", fixture.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main(verbosity=2)
