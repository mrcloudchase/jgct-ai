#!/usr/bin/env python3
"""Scan every public cBioPortal study for samples labelled granulosa (OncoTree GRCT/JGCT/AGCT or cancer-type text).

  python3 -I tools/cbio_grct_scan.py <out.json>

Retries each request 4 times and prints the failures, so an incomplete scan is visible (the
previous version swallowed errors and under-reported: 1 or 77 rows vs 278 on 2026-10-30)."""
import json, sys, time, urllib.request, concurrent.futures as cf
BASE="https://www.cbioportal.org/api"
def get(url,tries=4):
    last=None
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"jgct-ai"})
            return json.load(urllib.request.urlopen(req,timeout=120))
        except Exception as e:
            last=e; time.sleep(2*(i+1))
    raise last
studies=[s["studyId"] for s in get(BASE+"/studies?projection=SUMMARY")]
fails=[]
def scan(sid):
    hits=[]
    for attr in ("ONCOTREE_CODE","CANCER_TYPE_DETAILED","CANCER_TYPE"):
        try: rows=get(f"{BASE}/studies/{sid}/clinical-data?clinicalDataType=SAMPLE&attributeId={attr}&projection=SUMMARY")
        except Exception as e:
            fails.append((sid,attr,str(e)[:60])); continue
        for r in rows:
            v=str(r.get("value",""))
            if "granulosa" in v.lower() or v.upper() in ("GRCT","JGCT","AGCT"):
                hits.append(dict(study=sid,sample=r["sampleId"],patient=r["patientId"],attr=attr,value=v))
    return hits
allh=[]
with cf.ThreadPoolExecutor(4) as ex:
    for h in ex.map(scan,studies): allh+=h
json.dump(allh,open(sys.argv[1],"w"),indent=1)
import collections
print(len(studies),"studies;",len(allh),"rows;",collections.Counter((h["study"],h["value"]) for h in allh))
print("FAILS",len(fails),fails[:15])
