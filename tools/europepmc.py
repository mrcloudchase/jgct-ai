#!/usr/bin/env python3
"""Europe PMC helpers. Broader than PubMed: includes preprints, Agricola, patents, and open access full text.

  python3 tools/europepmc.py search '<query>' [--limit 1000] [--preprints]
  python3 tools/europepmc.py abstract <PMID> [<PMID> ...]     # verbatim title, abstract, journal, year, DOI, pubtypes
  python3 tools/europepmc.py fulltext <PMID or PMCID>
  python3 tools/europepmc.py citations <PMID> [--limit 100]
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET

import requests

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest"
HEADERS = {"User-Agent": "jgct-ai (https://github.com/mrcloudchase/jgct-ai)"}


def search(query: str, limit: int, preprints: bool) -> list[dict]:
    q = f"({query}) AND SRC:PPR" if preprints else query
    out, cursor = [], "*"
    while len(out) < limit:
        r = requests.get(f"{BASE}/search", headers=HEADERS, timeout=60,
                         params={"query": q, "format": "json", "pageSize": min(100, limit - len(out)),
                                 "cursorMark": cursor, "resultType": "lite"})
        r.raise_for_status()
        data = r.json()
        for h in data.get("resultList", {}).get("result", []):
            out.append({"id": h.get("id"), "source": h.get("source"), "pmid": h.get("pmid"), "pmcid": h.get("pmcid"),
                        "doi": h.get("doi"), "title": h.get("title"), "journal": h.get("journalTitle"),
                        "year": h.get("pubYear"), "open_access": h.get("isOpenAccess") == "Y",
                        "url": f"https://europepmc.org/article/{h.get('source')}/{h.get('id')}"})
        nxt = data.get("nextCursorMark")
        if not nxt or nxt == cursor or not data.get("resultList", {}).get("result"):
            break
        cursor = nxt
    return out


def fulltext(ident: str) -> str | None:
    pmcid = ident if ident.upper().startswith("PMC") else None
    if not pmcid:
        r = requests.get(f"{BASE}/search", headers=HEADERS, timeout=60,
                         params={"query": f"EXT_ID:{ident} AND SRC:MED", "format": "json", "resultType": "lite"})
        r.raise_for_status()
        hits = r.json().get("resultList", {}).get("result", [])
        pmcid = hits[0].get("pmcid") if hits else None
    if not pmcid:
        return None
    r = requests.get(f"{BASE}/{pmcid}/fullTextXML", headers=HEADERS, timeout=120)
    if r.status_code != 200 or not r.text.strip():
        return None
    root = ET.fromstring(r.text)
    body = root.find(".//body")
    text = " ".join(t.strip() for t in (body if body is not None else root).itertext() if t.strip())
    return text or None


def abstracts(pmids: list[str]) -> list[dict]:
    """Verbatim metadata and abstract text for PubMed IDs, in batches, via Europe PMC core results."""
    out = []
    for i in range(0, len(pmids), 25):
        chunk = pmids[i:i + 25]
        q = "(" + " OR ".join(f"EXT_ID:{p}" for p in chunk) + ") AND SRC:MED"
        r = requests.get(f"{BASE}/search", headers=HEADERS, timeout=120,
                         params={"query": q, "format": "json", "pageSize": 100, "resultType": "core"})
        r.raise_for_status()
        for h in r.json().get("resultList", {}).get("result", []):
            out.append({"pmid": h.get("pmid"), "pmcid": h.get("pmcid"), "doi": h.get("doi"), "title": h.get("title"),
                        "journal": h.get("journalInfo", {}).get("journal", {}).get("title"),
                        "year": h.get("pubYear"), "first_author": h.get("authorString", "").split(",")[0] or None,
                        "pubtypes": h.get("pubTypeList", {}).get("pubType", []), "language": h.get("language"),
                        "open_access": h.get("isOpenAccess") == "Y", "abstract": h.get("abstractText") or "",
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{h.get('pmid')}/"})
    found = {o["pmid"] for o in out}
    for p in pmids:
        if p not in found:
            out.append({"pmid": p, "abstract": "", "error": "not found in Europe PMC"})
    return out


def citations(pmid: str, limit: int) -> list[dict]:
    r = requests.get(f"{BASE}/MED/{pmid}/citations", headers=HEADERS, timeout=60,
                     params={"format": "json", "pageSize": min(1000, limit)})
    r.raise_for_status()
    return [{"pmid": c.get("id"), "title": c.get("title"), "year": c.get("pubYear"), "journal": c.get("journalAbbreviation")}
            for c in r.json().get("citationList", {}).get("citation", [])][:limit]


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("query"); s.add_argument("--limit", type=int, default=1000); s.add_argument("--preprints", action="store_true")
    a = sub.add_parser("abstract"); a.add_argument("pmids", nargs="+")
    f = sub.add_parser("fulltext"); f.add_argument("ident")
    c = sub.add_parser("citations"); c.add_argument("pmid"); c.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()
    if args.cmd == "search":
        print(json.dumps(search(args.query, args.limit, args.preprints), indent=1))
    elif args.cmd == "abstract":
        print(json.dumps(abstracts(args.pmids), indent=1, ensure_ascii=False))
    elif args.cmd == "fulltext":
        t = fulltext(args.ident)
        if t is None:
            print("NO_FULL_TEXT", file=sys.stderr); sys.exit(2)
        print(t)
    else:
        print(json.dumps(citations(args.pmid, args.limit), indent=1))


if __name__ == "__main__":
    main()
