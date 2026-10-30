"""Scan all cBioPortal studies for samples whose ONCOTREE_CODE / CANCER_TYPE_DETAILED / CANCER_TYPE mention granulosa (GRCT).
Usage (from repo root): python3 -I tools/cbio_grct_scan.py [base_url] [outfile]   (default https://www.cbioportal.org/api, cbio/hits.json)"""
import json, sys, urllib.request, concurrent.futures as cf
BASE = sys.argv[1] if len(sys.argv) > 1 else "https://www.cbioportal.org/api"
OUT = sys.argv[2] if len(sys.argv) > 2 else "state/cache/cbio/hits.json"
import os; os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
def get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "jgct-ai"})
    return json.load(urllib.request.urlopen(req, timeout=120))
studies = [s["studyId"] for s in get(BASE + "/studies?projection=SUMMARY")]
def scan(sid):
    hits = []
    for attr in ("ONCOTREE_CODE", "CANCER_TYPE_DETAILED", "CANCER_TYPE"):
        try:
            rows = get(f"{BASE}/studies/{sid}/clinical-data?clinicalDataType=SAMPLE&attributeId={attr}&projection=SUMMARY")
        except Exception as e:
            continue
        for r in rows:
            v = str(r.get("value", ""))
            if "granulosa" in v.lower() or v.upper() in ("GRCT", "JGCT", "AGCT"):
                hits.append(dict(study=sid, sample=r["sampleId"], patient=r["patientId"], attr=attr, value=v))
    return hits
allhits = []
with cf.ThreadPoolExecutor(8) as ex:
    for h in ex.map(scan, studies):
        allhits += h
json.dump(allhits, open(OUT, "w"), indent=1)
print(len(studies), "studies scanned;", len(allhits), "hit rows;", len({(h['study'], h['sample']) for h in allhits}), "samples")
