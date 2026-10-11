from pathlib import Path
from playwright.sync_api import sync_playwright
import os,tempfile
ROOT=Path(__file__).resolve().parents[1]
def main():
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path=os.environ.get('CHROMIUM_PATH') or None)
  page=browser.new_page(viewport={'width':1280,'height':900},accept_downloads=True); errors=[]; page.on('pageerror',lambda err:errors.append(str(err)))
  page.goto((ROOT/'index.html').as_uri()+'?selftest=1'); assert page.title().startswith('Proofline')
  checks=page.evaluate('window.__PROOFLINE_SELFTEST__'); assert len(checks)==11 and all(x['status']=='PASS' for x in checks),checks
  for name in ['intake','csv','library','service','overview']:
   page.locator('[data-nav='+name+']').click(); assert page.locator('#view-'+name).is_visible()
  page.locator('[data-nav=csv]').click(); page.get_by_role('button',name='Load synthetic sample').click(); assert 'PASS' in page.locator('#csv-message').inner_text(); assert page.locator('#row-count').inner_text().startswith('90 matching')
  page.locator('#row-filter').fill('Atlas'); assert page.locator('#row-count').inner_text().startswith('30 matching')
  with page.expect_download() as ev: page.locator('#export-csv').click()
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/ev.value.suggested_filename; ev.value.save_as(f); lines=f.read_text(encoding='utf-8').splitlines(); assert len(lines)==31,len(lines); assert all('Atlas' in line for line in lines[1:])
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'formula.csv'; f.write_text('label\n=1+1\n-12.5\n+SUM(1,2)\n',encoding='utf-8')
   page.locator('#csv-file').set_input_files(str(f))
   page.wait_for_function("document.querySelector('#csv-message').textContent.includes('PASS')")
   with page.expect_download() as formula_event: page.locator('#export-csv').click()
   formula_download=formula_event.value
   with tempfile.TemporaryDirectory() as outdir:
    csv_path=Path(outdir)/formula_download.suggested_filename; formula_download.save_as(csv_path)
    exported=csv_path.read_text(encoding='utf-8')
    assert "'=1+1" in exported, exported
    assert "'+SUM(1,2)" in exported, exported
    assert '-12.5' in exported, exported
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'bad.csv'; f.write_text('a,b\n1,2\n3\n',encoding='utf-8'); page.locator('#csv-file').set_input_files(str(f)); page.wait_for_function("document.querySelector('#csv-message').textContent.includes('FAIL')"); assert 'RAGGED_ROWS' in page.locator('#csv-findings').inner_text()
  page.locator('[data-nav=intake]').click(); page.locator('#job-title').fill('QA test'); page.locator('#job-objective').fill('All checks begin NOT TESTED.'); page.locator('button[type=submit]').click(); assert 'NOT TESTED' in page.locator('#packet-status').inner_text()
  with page.expect_download() as ev: page.locator('#packet-json').click()
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/ev.value.suggested_filename; ev.value.save_as(f); assert 'NOT EXECUTED' in f.read_text(encoding='utf-8')
  page.set_viewport_size({'width':390,'height':844}); page.locator('[data-nav=overview]').click(); assert not page.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth'); assert not errors,errors
  browser.close(); print('BROWSER TESTS: PASS — navigation, embedded self-tests, filtered export round-trip, malformed input, intake export, mobile width, JS errors')
if __name__=='__main__': main()
