#!/usr/bin/env python3
"""Records written from abstracts, for sources whose full text no open route can reach.

  python3 tools/mkabstract.py show pmid:12345 doi:10.1000/x ...     # print title, metadata and abstract to read
  python3 tools/mkabstract.py write batch.json [--cache abstracts.json]  # write records from a batch you authored

batch.json is a list of objects, one per source, each with the ledger id and the fields you wrote after
reading the abstract (study_type, tumor_site, n_jgct_patients, age_range, key_findings, relevance_to_jgct,
and optionally presentation, treatments, alterations, source_tier, notes, overlaps_with, conflicts_with).
Metadata (title, journal, year, first author, DOI, PMCID, language) comes from PubMed efetch for pmid items
and from Semantic Scholar/Crossref for doi items; --cache names a JSON file of previously fetched metadata
keyed by ledger id (as written by a run's abstract fetch) to avoid refetching. Each record gets
evidence_basis: abstract, full_text_source: null, abstract_source: the page the abstract was read from,
and the ledger item is set to abstract_only with the record name. Nothing is written for an item whose
abstract is empty. Existing full_text records are never overwritten.
"""
import argparse, datetime, json, os, re, sqlite3, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mkrecord import write as write_record, ROOT, OUT

UA = {"User-Agent": "jgct-ai/1.0 (knowledge base maintenance)"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


def fetch_pubmed(pmids):
    out = {}
    for i in range(0, len(pmids), 100):
        root = ET.fromstring(get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&retmode=xml&id=" + ",".join(pmids[i:i + 100])))
        for art in root.findall(".//PubmedArticle"):
            pmid = art.findtext(".//PMID")
            a = art.find(".//Article")
            title = "".join(a.find("ArticleTitle").itertext()) if a is not None and a.find("ArticleTitle") is not None else ""
            abst = []
            for t in art.findall(".//Abstract/AbstractText"):
                lab = t.get("Label")
                abst.append((lab + ": " if lab else "") + "".join(t.itertext()))
            year = art.findtext(".//JournalIssue/PubDate/Year") or (art.findtext(".//JournalIssue/PubDate/MedlineDate") or "")[:4] or art.findtext(".//ArticleDate/Year")
            au = art.find(".//AuthorList/Author")
            first = None
            if au is not None:
                first = f"{au.findtext('LastName')} {au.findtext('Initials') or ''}".strip() if au.findtext("LastName") else au.findtext("CollectiveName")
            doi = pmc = None
            for idn in art.findall(".//ArticleIdList/ArticleId"):
                if idn.get("IdType") == "doi": doi = idn.text
                if idn.get("IdType") == "pmc": pmc = idn.text
            out["pmid:" + pmid] = dict(pmid=pmid, title=title.rstrip("."), abstract="\n".join(abst), journal=art.findtext(".//Journal/Title"),
                                       year=year, first_author=first, doi=doi, pmcid=pmc, language=art.findtext(".//Language"),
                                       pubtypes=[p.text for p in art.findall(".//PublicationTypeList/PublicationType")])
        time.sleep(0.4)
    return out


def fetch_doi(doi):
    rec = dict(doi=doi, title=None, abstract="", journal=None, year=None, first_author=None, pmid=None)
    try:
        j = json.loads(get("https://api.semanticscholar.org/graph/v1/paper/DOI:" + urllib.parse.quote(doi, safe="") + "?fields=title,abstract,year,venue,authors,externalIds"))
        rec.update(title=j.get("title"), abstract=j.get("abstract") or "", journal=j.get("venue"), year=str(j.get("year") or ""),
                   first_author=(j.get("authors") or [{}])[0].get("name"), pmid=(j.get("externalIds") or {}).get("PubMed"))
    except Exception:
        pass
    if not rec["abstract"]:
        try:
            j = json.loads(get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")))["message"]
            a0 = (j.get("author") or [None])[0]
            rec.update(title=rec["title"] or "".join(j.get("title") or []), abstract=re.sub("<[^>]+>", "", j.get("abstract") or ""),
                       journal=rec["journal"] or "".join(j.get("container-title") or []),
                       year=rec["year"] or str((j.get("issued", {}).get("date-parts") or [[""]])[0][0]),
                       first_author=rec["first_author"] or (f"{a0.get('family', '')} {a0.get('given', '')}".strip() if a0 else None))
        except Exception:
            pass
    return rec


def metadata(ids, cache):
    meta = {i: cache[i] for i in ids if i in cache}
    pm = [i[5:] for i in ids if i.startswith("pmid:") and i not in meta]
    if pm:
        meta.update(fetch_pubmed(pm))
    for i in ids:
        if i.startswith("doi:") and i not in meta:
            meta[i] = fetch_doi(i[4:]); time.sleep(1)
    return meta


def abstract_url(lid, m):
    if lid.startswith("pmid:"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{lid[5:]}/"
    if m.get("pmid"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{m['pmid']}/"
    return f"https://doi.org/{lid[4:]}"


def cmd_show(args):
    cache = json.load(open(args.cache)) if args.cache and os.path.exists(args.cache) else {}
    for lid, m in metadata(args.ids, cache).items():
        print(f"=== {lid} | {m.get('year')} | {m.get('first_author')} | {m.get('journal')} | {', '.join(m.get('pubtypes') or [])}\n{m.get('title')}\n{m.get('abstract') or '(no abstract)'}\n")


def cmd_write(args):
    cache = json.load(open(args.cache)) if args.cache and os.path.exists(args.cache) else {}
    batch = json.load(open(args.batch))
    meta = metadata([b["id"] for b in batch], cache)
    con = sqlite3.connect(os.path.join(ROOT, "state", "ledger.sqlite"))
    today = datetime.date.today().isoformat()
    n = 0
    for b in batch:
        lid = b.pop("id"); m = meta.get(lid) or {}
        if not m.get("abstract"):
            print("skip (no abstract)", lid); continue
        st, sid = ("pmid", lid[5:]) if lid.startswith("pmid:") else ("doi", lid[4:])
        path = os.path.join(OUT, f"{st}-{sid.replace('/', '_')}.yaml")
        if os.path.exists(path) and "evidence_basis: full_text" in open(path).read():
            print("skip (full-text record exists)", lid); continue
        year = int(str(m.get("year") or b.get("year") or 0)[:4] or 0)
        f = dict(source_type=st, source_id=sid, evidence_basis="abstract", full_text_source=None, abstract_source=abstract_url(lid, m),
                 retrieved_on=today, language=(m.get("language") or "eng")[:2].replace("en", "en") if m.get("language") else "en",
                 pmid=str(m.get("pmid")) if m.get("pmid") else (sid if st == "pmid" else None), doi=m.get("doi") or (sid if st == "doi" else None),
                 pmcid=m.get("pmcid"), title=(m.get("title") or b.get("title") or "").rstrip("."), journal=m.get("journal"), year=year,
                 first_author=m.get("first_author"))
        lang = {"eng": "en", "chi": "zh", "fre": "fr", "ger": "de", "spa": "es", "jpn": "ja", "por": "pt", "ita": "it", "rus": "ru", "tur": "tr", "pol": "pl", "kor": "ko", "dut": "nl", "cze": "cs", "hun": "hu", "per": "fa"}
        if m.get("language"):
            f["language"] = lang.get(m["language"], m["language"][:2])
        f.update(b)
        note = "Written from the abstract only; no open route to the full text was found. Replace with a full-text record when one can be read."
        f["notes"] = (f.get("notes") + " " if f.get("notes") else "") + note
        write_record(**f)
        stem = os.path.basename(path)[:-5]
        con.execute("UPDATE items SET status='abstract_only', record=?, note=COALESCE(note,'') || ?, updated=datetime('now') WHERE id=?",
                    (stem, f" ; {today}: record written from abstract (abstract_only).", lid))
        n += 1
    con.commit()
    print(f"wrote {n} abstract records")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = ap.add_subparsers(dest="cmd", required=True)
    a = s.add_parser("show"); a.add_argument("ids", nargs="+"); a.add_argument("--cache")
    w = s.add_parser("write"); w.add_argument("batch"); w.add_argument("--cache")
    args = ap.parse_args()
    (cmd_show if args.cmd == "show" else cmd_write)(args)


if __name__ == "__main__":
    main()
