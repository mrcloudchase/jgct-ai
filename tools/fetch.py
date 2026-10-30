#!/usr/bin/env python3
"""Fetch sources from structured APIs (PubMed E-utilities, Europe PMC).

  python3 tools/fetch.py discover-pubmed "<query>" [--max 1000]   # load hits into ledger as 'found', prioritized
  python3 tools/fetch.py discover-epmc "<query>" [--max 1000]     # Europe PMC (adds non-PubMed items, e.g. preprints)
  python3 tools/fetch.py abstract <pmid> [<pmid> ...]             # verbatim title/abstract/metadata from PubMed XML
  python3 tools/fetch.py fulltext <pmid>                          # open-access full text via Europe PMC (PMC XML -> plain text)
  python3 tools/fetch.py cites <pmid> [--dir citing|refs]         # citation chasing via Europe PMC

Raw downloads go to state/cache/ (gitignored); output printed to stdout.
"""
import json, os, re, sys, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger

EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "state", "cache")


def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "jgct-ai/1.0 (research knowledge base)"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            if i == tries - 1:
                raise
            time.sleep(2 + 2 * i)


def priority(title, pubtypes):
    t = (title or "").lower()
    pt = " ".join(pubtypes).lower()
    if "retract" in pt:
        return 5
    p = 30
    if any(k in t for k in ("series", "cohort", "registry", "multicent", "retrospective", "patients", "national", "experience", "outcome", "cases")):
        p = 75
    if any(k in t for k in ("akt1", "gnas", "foxl2", "dicer1", "genom", "sequenc", "mutation", "molecular", "transcriptom", "methyl", "copy number")):
        p = max(p, 85)
    if "guideline" in pt or "consensus" in t or "recommendation" in t or "guideline" in t:
        p = 90
    if "review" in pt or "review" in t:
        p = max(p, 60)
    if "case report" in pt and p < 60:
        p = 30
    if "juvenile" not in t:
        p -= 15  # adult GCT / general SCST papers rank lower unless explicit
    return p


def discover_pubmed(q, mx=1000):
    r = json.loads(get(EU + "esearch.fcgi?db=pubmed&retmode=json&retmax=%d&term=%s" % (mx, urllib.parse.quote(q))))
    ids = r["esearchresult"]["idlist"]
    print("pubmed hits:", r["esearchresult"]["count"], "fetched ids:", len(ids))
    c = ledger.conn(); new = 0
    for i in range(0, len(ids), 200):
        s = json.loads(get(EU + "esummary.fcgi?db=pubmed&retmode=json&id=" + ",".join(ids[i:i + 200])))
        for pid in s["result"].get("uids", []):
            d = s["result"][pid]
            yr = re.match(r"(\d{4})", d.get("pubdate", "") or "")
            pts = d.get("pubtype", [])
            new += ledger.add(c, "pmid:" + pid, d.get("title"), int(yr.group(1)) if yr else None,
                              ";".join(pts), "found", priority(d.get("title"), pts), "pubmed: " + q)
        time.sleep(0.4)
    c.commit(); print("new in ledger:", new)


def discover_epmc(q, mx=1000):
    c = ledger.conn(); new = 0; cursor = "*"; n = 0
    while n < mx:
        r = json.loads(get(EPMC + "search?format=json&pageSize=1000&query=%s&cursorMark=%s" % (urllib.parse.quote(q), urllib.parse.quote(cursor))))
        res = r.get("resultList", {}).get("result", [])
        if not res:
            break
        for d in res:
            n += 1
            if d.get("pmid"):
                iid = "pmid:" + d["pmid"]
            elif d.get("doi"):
                iid = "doi:" + d["doi"].lower()
            else:
                iid = "epmc:%s:%s" % (d.get("source"), d.get("id"))
            pts = d.get("pubTypeList", {}).get("pubType", []) if isinstance(d.get("pubTypeList"), dict) else []
            if d.get("source") == "PPR":
                pts = pts + ["preprint"]
            yr = d.get("pubYear")
            new += ledger.add(c, iid, d.get("title"), int(yr) if yr and yr.isdigit() else None, ";".join(pts), "found",
                              priority(d.get("title"), pts), "europepmc: " + q)
        nc = r.get("nextCursorMark")
        if not nc or nc == cursor:
            break
        cursor = nc
    c.commit(); print("epmc scanned:", n, "new in ledger:", new)


def text(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def abstract(pmids):
    x = get(EU + "efetch.fcgi?db=pubmed&retmode=xml&id=" + ",".join(pmids))
    os.makedirs(CACHE, exist_ok=True)
    root = ET.fromstring(x)
    for a in root.findall(".//PubmedArticle"):
        m = a.find("MedlineCitation"); art = m.find("Article")
        pmid = text(m.find("PMID"))
        doi = next((text(e) for e in a.findall(".//ArticleId") if e.get("IdType") == "doi"), "")
        pmc = next((text(e) for e in a.findall(".//ArticleId") if e.get("IdType") == "pmc"), "")
        au = art.find(".//AuthorList/Author")
        fa = (text(au.find("LastName")) + " " + text(au.find("Initials"))).strip() if au is not None else ""
        yr = text(art.find(".//JournalIssue/PubDate/Year")) or text(art.find(".//ArticleDate/Year")) or text(art.find(".//PubDate/MedlineDate"))[:4]
        pts = [text(p) for p in art.findall(".//PublicationType")]
        lang = text(art.find("Language"))
        print("=" * 80)
        print(f"PMID: {pmid}\nDOI: {doi}\nPMC: {pmc}\nTitle: {text(art.find('ArticleTitle'))}\nJournal: {text(art.find('Journal/Title'))}\nYear: {yr}\nFirst author: {fa}\nLanguage: {lang}\nPubTypes: {'; '.join(pts)}")
        for ab in art.findall(".//Abstract/AbstractText"):
            lab = ab.get("Label")
            print((lab + ": " if lab else "") + text(ab))
        cm = [text(c.find("RefSource")) + " " + c.get("RefType", "") for c in m.findall(".//CommentsCorrections") if "Retract" in c.get("RefType", "")]
        if cm:
            print("RETRACTION NOTICE:", cm)


def fulltext(pmid):
    r = json.loads(get(EPMC + "search?format=json&query=EXT_ID:%s%%20AND%%20SRC:MED&resultType=core" % pmid))
    res = r["resultList"]["result"]
    if not res:
        print("not in Europe PMC"); return 1
    d = res[0]
    pmcid = d.get("pmcid")
    if not pmcid or d.get("isOpenAccess") != "Y" and d.get("inEPMC") != "Y":
        print("NO_OA_FULLTEXT pmcid=%s isOpenAccess=%s inEPMC=%s" % (pmcid, d.get("isOpenAccess"), d.get("inEPMC"))); return 1
    try:
        x = get(EPMC + pmcid + "/fullTextXML")
    except Exception as e:
        try:  # fallback: NCBI PMC efetch (works for many PMC articles Europe PMC 500s on)
            x = get(EU + "efetch.fcgi?db=pmc&id=" + pmcid.replace("PMC", ""))
            if "<body" not in x:
                raise RuntimeError("no body in PMC efetch (likely publisher-restricted)")
        except Exception as e2:
            print("FULLTEXT_FETCH_FAILED", pmcid, e, "| ncbi:", e2); return 1
    os.makedirs(CACHE, exist_ok=True)
    open(os.path.join(CACHE, pmcid + ".xml"), "w").write(x)
    root = ET.fromstring(x)
    body = root.find(".//body")
    out = []
    for el in (body.iter() if body is not None else []):
        if el.tag in ("title",):
            out.append("\n## " + text(el))
        elif el.tag == "p":
            out.append(text(el))
    for tw in root.findall(".//table-wrap"):
        out.append("\n[TABLE] " + text(tw.find("label")) + " " + text(tw.find("caption")))
        for tr in tw.findall(".//tr"):
            out.append(" | ".join(text(td) for td in tr))
    print(f"PMCID {pmcid}\n" + "\n".join(out))


def cites(pmid, direction="citing"):
    ep = "citations" if direction == "citing" else "references"
    r = json.loads(get(EPMC + "MED/%s/%s?format=json&pageSize=1000" % (pmid, ep)))
    key = "citationList" if ep == "citations" else "referenceList"
    items = r.get(key, {}).get("citation" if ep == "citations" else "reference", [])
    c = ledger.conn(); new = 0
    for d in items:
        if not d.get("id") or d.get("source") != "MED":
            continue
        t = d.get("title") or ""
        new += ledger.add(c, "pmid:" + d["id"], t, d.get("pubYear"), None, "found", priority(t, []), f"{ep} of pmid:{pmid}")
    c.commit(); print(f"{ep}: {len(items)} new: {new}")


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    mx = 1000
    if "--max" in args:
        i = args.index("--max"); mx = int(args[i + 1]); del args[i:i + 2]
    if cmd == "discover-pubmed": discover_pubmed(args[0], mx)
    elif cmd == "discover-epmc": discover_epmc(args[0], mx)
    elif cmd == "abstract": abstract(args)
    elif cmd == "fulltext": sys.exit(fulltext(args[0]) or 0)
    elif cmd == "cites":
        d = "citing"
        if "--dir" in args: d = args[args.index("--dir") + 1]
        cites(args[0], d)
    else: print(__doc__)
