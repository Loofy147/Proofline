#!/usr/bin/env python3
"""Deterministic local CSV quality audit. Standard-library only."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, sys
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

MAX_BYTES=10*1024*1024
MAX_ROWS=100_000
NUMERIC=re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$")

def number(value):
    value=value.strip()
    if not value or not NUMERIC.fullmatch(value): return None
    try:
        result=Decimal(value)
        return result if result.is_finite() else None
    except InvalidOperation: return None

def analyze(path: Path):
    if not path.is_file(): raise FileNotFoundError("Input file not found: "+str(path))
    size=path.stat().st_size
    if size>MAX_BYTES: raise ValueError(f"Input exceeds {MAX_BYTES} bytes")
    raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
    try: text=raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc: raise ValueError("CSV must be UTF-8; UTF-8 BOM is accepted") from exc
    try: parsed=list(csv.reader(io.StringIO(text,newline=""),strict=True))
    except csv.Error as exc: raise ValueError("Malformed CSV quoting: "+str(exc)) from exc
    if not parsed: raise ValueError("CSV is empty")
    if len(parsed)-1>MAX_ROWS: raise ValueError(f"Input exceeds {MAX_ROWS} data rows")
    headers=[h.strip() for h in parsed[0]]
    if not headers or not any(headers): raise ValueError("CSV has no usable header")
    errors=[]; warnings=[]
    empty=[i+1 for i,h in enumerate(headers) if not h]
    duplicates=sorted(k for k,n in Counter(h.casefold() for h in headers if h).items() if n>1)
    if empty: errors.append({"code":"EMPTY_HEADER","columns_1_based":empty})
    if duplicates: errors.append({"code":"DUPLICATE_HEADERS","names":duplicates})
    raw_rows=parsed[1:]
    blank_rows=sum(1 for r in raw_rows if not any(x.strip() for x in r))
    rows=[r for r in raw_rows if any(x.strip() for x in r)]
    ragged=[{"csv_record":i+2,"expected_fields":len(headers),"actual_fields":len(r)} for i,r in enumerate(raw_rows) if any(x.strip() for x in r) and len(r)!=len(headers)]
    if ragged: errors.append({"code":"RAGGED_ROWS","count":len(ragged),"examples":ragged[:10]})
    blank_cells=0; counts=Counter()
    for row in rows:
        padded=(row+[""]*max(0,len(headers)-len(row)))[:len(headers)]
        blank_cells+=sum(1 for x in padded if not x.strip())
        counts[json.dumps([x.strip() for x in padded],ensure_ascii=False,separators=(",",":"))]+=1
    dup_groups=sum(1 for n in counts.values() if n>1); dup_extra=sum(n-1 for n in counts.values() if n>1)
    profiles=[]
    for i,h in enumerate(headers):
        vals=[(r[i].strip() if i<len(r) else "") for r in rows]; nonempty=[v for v in vals if v]
        good=[n for n in (number(v) for v in nonempty) if n is not None]
        numeric=len(nonempty)>=3 and len(good)/len(nonempty)>=.7
        profile={"column_index_1_based":i+1,"column":h or f"(blank header #{i+1})","nonempty_values":len(nonempty),"missing_values":len(vals)-len(nonempty),"inferred_type":"numeric" if numeric else "text_or_mixed"}
        if numeric and good:
            total=sum(good,Decimal("0")); profile.update({"numeric_values":len(good),"min":str(min(good)),"max":str(max(good)),"sum":str(total),"mean":str(total/Decimal(len(good)))})
        profiles.append(profile)
    sales={"applicable":False,"checked_rows":0,"violations":0,"examples":[]}
    idx={h.casefold():i for i,h in enumerate(headers) if h}
    required={"unit_price_usd","units_sold","revenue_usd"}
    if required.issubset(idx):
        sales["applicable"]=True
        for line,row in enumerate(raw_rows,start=2):
            if not any(x.strip() for x in row): continue
            sales["checked_rows"]+=1; padded=(row+[""]*max(0,len(headers)-len(row)))[:len(headers)]
            p,u,v=(number(padded[idx[k]]) for k in ("unit_price_usd","units_sold","revenue_usd"))
            if p is None or u is None or v is None or abs(p*u-v)>Decimal("0.000001"):
                sales["violations"]+=1
                if len(sales["examples"])<10: sales["examples"].append({"csv_record":line,"reason":"unit_price_usd × units_sold must equal revenue_usd"})
        if sales["violations"]: errors.append({"code":"SALES_ARITHMETIC_MISMATCH","count":sales["violations"],"examples":sales["examples"]})
    if blank_rows: warnings.append({"code":"BLANK_ROWS","count":blank_rows})
    if blank_cells: warnings.append({"code":"MISSING_CELLS","count":blank_cells})
    if dup_groups: warnings.append({"code":"DUPLICATE_ROWS","groups":dup_groups,"extra_copies":dup_extra})
    if not rows: errors.append({"code":"NO_DATA_ROWS"})
    return {"schema_version":"proofline.csv-audit.v1","generated_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
      "input":{"filename":path.name,"bytes":size,"sha256":digest,"encoding":"utf-8-sig"},"limits":{"max_bytes":MAX_BYTES,"max_rows":MAX_ROWS},
      "summary":{"status":"FAIL" if errors else ("PASS_WITH_WARNINGS" if warnings else "PASS"),"data_rows":len(rows),"header_columns":len(headers),"blank_rows":blank_rows,"missing_cells_in_nonblank_rows":blank_cells,"duplicate_row_groups":dup_groups,"duplicate_row_extra_copies":dup_extra,"structural_error_count":len(errors),"warning_count":len(warnings)},
      "columns":profiles,"errors":errors,"warnings":warnings,"optional_domain_check_sales_revenue":sales,
      "scope_note":"Checks structure and configured numeric consistency only. It does not establish source authenticity, real-world truth, or decision suitability. Numeric inference uses dot-decimal syntax."}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv",type=Path); parser.add_argument("--out",type=Path,default=Path("proofline-output")); args=parser.parse_args()
    try:
        report=analyze(args.csv); args.out.mkdir(parents=True,exist_ok=True)
        jp=args.out/(args.csv.stem+"_audit.json"); cp=args.out/(args.csv.stem+"_column_profile.csv")
        jp.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
        with cp.open("w",encoding="utf-8-sig",newline="") as f:
            fields=["column_index_1_based","column","nonempty_values","missing_values","inferred_type","numeric_values","min","max","sum","mean"]
            writer=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); writer.writeheader(); writer.writerows(report["columns"])
        print(json.dumps({"status":report["summary"]["status"],"rows":report["summary"]["data_rows"],"columns":report["summary"]["header_columns"],"errors":report["summary"]["structural_error_count"],"warnings":report["summary"]["warning_count"],"json_report":str(jp),"column_profile":str(cp)},indent=2))
        return 1 if report["summary"]["status"]=="FAIL" else 0
    except Exception as exc:
        print(f"proofline: {type(exc).__name__}: {exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())