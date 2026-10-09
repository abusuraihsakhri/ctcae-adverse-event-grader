#!/usr/bin/env python3
"""
CTCAE Adverse Event Grader
Legacy illustrative vascular-factor score, NOT validated CTCAE grading.
For supported NCI CTCAE v5 grading, use ctcae_grading.py.
"""
import argparse, csv, sys

FACTORS = [
        ("Smoking",1),
        ("Hypertension",1),
        ("Diabetes",1),
        ("Prior stroke",2),
        ("Vascular disease",1)
]

THRESHOLDS = [(2,"low"),(4,"moderate"),(100,"high")]

def calculate_score(present):
    """present: dict factor->bool or row dict with 1/0."""
    score=0; detail={}
    for name,w in FACTORS:
        # accept 1/0, true/false, yes/no, present key in dict
        val = present.get(name, present.get(name.lower().replace(" ","_"), 0))
        is_pos = str(val).lower() in ("1","true","yes","y") or val==1 or val is True
        # also auto-map common csv columns: age, sex, etc.
        if not is_pos and name=="Age>60":
            try: is_pos = float(present.get("age",0))>60
            except: pass
        if not is_pos and name=="Male":
            is_pos = str(present.get("sex","")).upper()=="M"
        if is_pos:
            score+=w
            detail[name]=w
    # tier
    tier="low"
    for thr,label in THRESHOLDS:
        if score<=thr: tier=label; break
        tier=label
    return {"score": score, "tier": tier, "detail": detail}

def assess_row(row):
    # row is dict from csv
    # map csv columns to present
    present = {}
    for k,v in row.items():
        present[k]=v
        present[k.lower()]=v
    # also map snake
    return calculate_score(present)

def process_csv(inp,out):
    """Process a CSV file and write results. Returns list of result dicts."""
    import csv
    import os

    if not os.path.isfile(inp):
        raise FileNotFoundError(f"Input CSV file not found: {inp}")

    with open(inp, newline="", encoding="utf-8-sig") as f:
        r=csv.DictReader(f)
        fn=r.fieldnames
        if not fn:
            raise ValueError(f"Input CSV file has no headers: {inp}")
        rows=list(r)

    results=[]
    for row in rows:
        res=assess_row(row)
        merged={**row, "score": res["score"], "tier": res["tier"], "detail": ";".join(res["detail"].keys())}
        results.append(merged)

    out_dir = os.path.dirname(out)
    if out_dir and not os.path.isdir(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    with open(out,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=list(fn)+["score","tier","detail"]); w.writeheader(); w.writerows(results)
    return results

def build_parser():
    p=argparse.ArgumentParser(prog="ctcae-legacy", description="Legacy non-CTCAE illustrative factor scoring")
    sub=p.add_subparsers(dest="cmd", required=True)
    s=sub.add_parser("single"); s.add_argument("--age", type=float); s.add_argument("--sex"); 
    for name,_ in FACTORS:
        s.add_argument("--"+name.lower().replace(" ","_").replace(">","_gt_").replace("/","_"), default="0")
    s.add_argument("--json")
    b=sub.add_parser("batch"); b.add_argument("--input", required=True); b.add_argument("--output", required=True)
    return p

def main(argv=None):
    import json as _json
    p=build_parser(); a=p.parse_args(argv)
    if a.cmd=="single":
        if a.json:
            present=_json.loads(a.json)
        else:
            present={k: getattr(a,k) for k in vars(a) if k not in ("cmd","json")}
        res=calculate_score(present); print(res); return 0
    if a.cmd=="batch":
        res=process_csv(a.input, a.output); print(f"Processed {len(res)} -> {a.output}"); return 0
    p.print_help(); return 1

if __name__=="__main__":
    import sys; sys.exit(main())
