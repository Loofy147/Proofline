import csv, json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class VerifyCsvTests(unittest.TestCase):
 def run_cli(self,text):
  td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); root=Path(td.name); source=root/'sample.csv'; source.write_text(text,encoding='utf-8'); out=root/'out'
  proc=subprocess.run([sys.executable,str(ROOT/'verify_csv.py'),str(source),'--out',str(out)],capture_output=True,text=True)
  fs=list(out.glob('*_audit.json')) if out.exists() else []
  return proc,json.loads(fs[0].read_text(encoding='utf-8')) if fs else None,out
 def test_valid_sales(self):
  p,r,o=self.run_cli('product,unit_price_usd,units_sold,revenue_usd\nA,2,3,6\nB,4,5,20\nC,1.5,2,3\n'); self.assertEqual(p.returncode,0,p.stderr); self.assertEqual(r['summary']['status'],'PASS'); self.assertEqual(r['summary']['data_rows'],3); self.assertTrue((o/'sample_column_profile.csv').exists())
 def test_ragged_row_fails(self):
  p,r,_=self.run_cli('a,b\n1,2\n3\n'); self.assertEqual(p.returncode,1); self.assertIn('RAGGED_ROWS',[e['code'] for e in r['errors']])
 def test_duplicate_header_fails(self):
  p,r,_=self.run_cli('x,x\n1,2\n'); self.assertEqual(p.returncode,1); self.assertIn('DUPLICATE_HEADERS',[e['code'] for e in r['errors']])
 def test_sales_mismatch_fails(self):
  p,r,_=self.run_cli('unit_price_usd,units_sold,revenue_usd\n2,3,7\n4,5,20\n1.5,2,3\n'); self.assertEqual(p.returncode,1); self.assertEqual(r['optional_domain_check_sales_revenue']['violations'],1)
 def test_multiline_quote(self):
  p,r,_=self.run_cli('name,note\nA,"line one\nline two"\nB,plain\n'); self.assertEqual(p.returncode,0,p.stderr); self.assertEqual(r['summary']['data_rows'],2)
 def test_malformed_quotes(self):
  p,_,_=self.run_cli('name,note\nA,"unclosed\n'); self.assertEqual(p.returncode,2); self.assertIn('Malformed CSV',p.stderr)
 def test_empty_file(self):
  p,_,_=self.run_cli(''); self.assertEqual(p.returncode,2)
 def test_profile_csv_neutralizes_formula_like_header(self):
  p,_,out=self.run_cli('=1+1,-12.5\n1,2\n3,4\n5,6\n')
  self.assertEqual(p.returncode,0,p.stderr)
  with (out/'sample_column_profile.csv').open('r',newline='',encoding='utf-8-sig') as handle:
   rows=list(csv.DictReader(handle))
  self.assertEqual(rows[0]['column'],"'=1+1")
  self.assertEqual(rows[1]['column'],"-12.5")
 def test_profile_csv_neutralizes_other_formula_prefixes(self):
  p,_,out=self.run_cli('+1+1,@cmd,-cmd\n1,2,3\n4,5,6\n7,8,9\n')
  self.assertEqual(p.returncode,0,p.stderr)
  with (out/'sample_column_profile.csv').open('r',newline='',encoding='utf-8-sig') as handle:
   rows=list(csv.DictReader(handle))
  self.assertEqual([row['column'] for row in rows],["'+1+1","'@cmd","'-cmd"])
if __name__=='__main__': unittest.main(verbosity=2)
