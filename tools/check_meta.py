#!/usr/bin/env python3
"""Cross-check pmid records' doi, year, and title against PubMed esummary (catches typos in hand-entered metadata).

  python3 tools/check_meta.py     # prints mismatches; exit 1 if any
"""
import glob, json, os, sys, urllib.request
import yaml

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
recs = {}
for f in glob.glob(os.path.join(ROOT, "knowledge/records/pmid-*.yaml")):
    r = yaml.safe_load(open(f)); recs[r["pmid"]] = (os.path.basename(f), r)
bad = 0
ids = list(recs)
for i in range(0, len(ids), 150):
    u = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=" + ",".join(ids[i:i + 150])
    s = json.load(urllib.request.urlopen(u, timeout=60))["result"]
    for pid in ids[i:i + 150]:
        d = s.get(pid, {}); fn, r = recs[pid]
        doi = next((a["value"] for a in d.get("articleids", []) if a["idtype"] == "doi"), None)
        if (r.get("doi") or "").lower() != (doi or "").lower():
            print(f"{fn}: doi {r.get('doi')} != pubmed {doi}"); bad += 1
        if str(r["year"]) not in (d.get("pubdate", "") + d.get("epubdate", "")):
            print(f"{fn}: year {r['year']} not in pubmed dates {d.get('pubdate')} / {d.get('epubdate')}"); bad += 1
        t1 = "".join(ch for ch in r["title"].lower() if ch.isalnum())[:40]
        t2 = "".join(ch for ch in d.get("title", "").lower() if ch.isalnum())[:40]
        if t1 != t2:
            print(f"{fn}: title differs: {r['title'][:60]} | {d.get('title','')[:60]}"); bad += 1
print(f"{len(recs)} pmid records checked, {bad} mismatches")
sys.exit(1 if bad else 0)
