import subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RepositoryContractTests(unittest.TestCase):
 def test_validator(self):
  r=subprocess.run([sys.executable,str(ROOT/'scripts/validate_repo.py')],cwd=ROOT,text=True,capture_output=True); self.assertEqual(r.returncode,0,r.stdout+r.stderr)
 def test_ci_minimum_permissions_and_browser_suite(self):
  t=(ROOT/'.github/workflows/ci.yml').read_text(); self.assertIn('contents: read',t); self.assertIn('persist-credentials: false',t); self.assertIn('chromium-interactions:',t)
 def test_intake_does_not_claim_execution(self):
  t=(ROOT/'index.html').read_text(); self.assertIn('NOT TESTED',t); self.assertIn('NOT EXECUTED',t)
if __name__=='__main__':unittest.main(verbosity=2)
