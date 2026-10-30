"""For GRCT/JGCT samples found by cbio_grct_scan.py, pull sample/patient clinical data and mutations.
Usage (from repo root): python3 -I tools/cbio_grct_detail.py <study_id> [hits.json]"""
import json, sys, urllib.request, collections
BASE = "https://www.cbioportal.org/api"
import os; os.makedirs("state/cache/cbio", exist_ok=True)
sid = sys.argv[1]; hits = json.load(open(sys.argv[2] if len(sys.argv) > 2 else "state/cache/cbio/hits.json"))
def call(url, body=None):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
        headers={"Accept": "application/json", "Content-Type": "application/json", "User-Agent": "jgct-ai"})
    return json.load(urllib.request.urlopen(req, timeout=300))
samples = sorted({h["sample"] for h in hits if h["study"] == sid})
patients = sorted({h["patient"] for h in hits if h["study"] == sid})
print(sid, len(samples), "samples", len(patients), "patients")
sc = call(f"{BASE}/clinical-data/fetch?clinicalDataType=SAMPLE&projection=SUMMARY", {"identifiers": [{"entityId": s, "studyId": sid} for s in samples]})
pc = call(f"{BASE}/clinical-data/fetch?clinicalDataType=PATIENT&projection=SUMMARY", {"identifiers": [{"entityId": p, "studyId": sid} for p in patients]})
clin = collections.defaultdict(dict)
for r in sc: clin[r["sampleId"]][r["clinicalAttributeId"]] = r["value"]
pclin = collections.defaultdict(dict)
for r in pc: pclin[r["patientId"]][r["clinicalAttributeId"]] = r["value"]
profs = [p["molecularProfileId"] for p in call(f"{BASE}/studies/{sid}/molecular-profiles") if p["molecularAlterationType"] == "MUTATION_EXTENDED"]
muts = collections.defaultdict(list)
for prof in profs:
    for m in call(f"{BASE}/molecular-profiles/{prof}/mutations/fetch?projection=DETAILED", {"sampleIds": samples}):
        muts[m["sampleId"]].append(f'{m["gene"]["hugoGeneSymbol"]} {m.get("proteinChange")}')
out = []
for s in samples:
    p = s.rsplit("-", 2)[0] if s.startswith("P-") else None
    pid = [h["patient"] for h in hits if h["sample"] == s][0]
    out.append(dict(sample=s, sample_clin=clin[s], patient_clin=pclin[pid], mutations=muts[s]))
json.dump(out, open(f"state/cache/cbio/detail_{sid}.json", "w"), indent=1)
print("profiles", profs, "; wrote", f"state/cache/cbio/detail_{sid}.json")
