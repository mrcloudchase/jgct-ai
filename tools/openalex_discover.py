"""OpenAlex discovery for JGCT: page through /works?search=<q>, write JSONL with id, doi, pmid, type, year, title,
venue, abstract (reconstructed verbatim from abstract_inverted_index). Then optionally compare with ledger.
Usage (pass '' as search to use only the filter, e.g. 'title_and_abstract.search:juvenile granulosa'):
  python3 -I openalex_discover.py fetch '<search>' <out.jsonl> [extra_filter]
  python3 -I openalex_discover.py compare <out.jsonl> <repo_root>     # prints items whose pmid/doi is not in the ledger
Polite pool: set OPENALEX_MAILTO env var; set OPENALEX_API_KEY to add api_key (no-key requests share a $0.10/day IP budget)."""
import sys, json, os, time, urllib.request, urllib.error, urllib.parse, subprocess
def recon(inv):
    if not inv: return None
    pos = {}
    for w, ps in inv.items():
        for p in ps: pos[p] = w
    return " ".join(pos[i] for i in sorted(pos))
def fetch(q, out, filt=None):
    page, n = 1, 0
    mail = os.environ.get("OPENALEX_MAILTO", "")
    with open(out, "w") as fh:
        while page:
            params = {"per-page": "200", "page": str(page)}  # page-based: cursor paging returned HTTP 401 without an API key (2026-10-30)
            if q: params["search"] = q
            if filt: params["filter"] = filt
            if mail: params["mailto"] = mail
            if os.environ.get("OPENALEX_API_KEY"): params["api_key"] = os.environ["OPENALEX_API_KEY"]
            url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
            for attempt in range(5):
                try:
                    d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "jgct-ai"}), timeout=120)); break
                except urllib.error.HTTPError as e:
                    print("HTTP", e.code, "retrying", file=sys.stderr); time.sleep(5 * (attempt + 1))
            else:
                print("giving up; partial results kept", file=sys.stderr); break
            for w in d["results"]:
                ids = w.get("ids", {})
                pmid = ids.get("pmid", "").rsplit("/", 1)[-1] or None
                src = ((w.get("primary_location") or {}).get("source") or {})
                fh.write(json.dumps(dict(id=w["id"], doi=(w.get("doi") or "").replace("https://doi.org/", "").lower() or None,
                    pmid=pmid, type=w.get("type"), year=w.get("publication_year"), title=w.get("title"),
                    venue=src.get("display_name"), venue_type=src.get("type"), lang=w.get("language"),
                    abstract=recon(w.get("abstract_inverted_index")), landing=(w.get("primary_location") or {}).get("landing_page_url"))) + "\n")
                n += 1
            page = page + 1 if d["results"] and page * 200 < min(d["meta"]["count"], 10000) else None
            time.sleep(0.2)
    print("fetched", n, "works ->", out)
def compare(inp, root):
    led = os.path.join(root, "tools", "ledger.py")
    missing = []
    for line in open(inp):
        w = json.loads(line)
        keys = ([f"pmid:{w['pmid']}"] if w["pmid"] else []) + ([f"doi:{w['doi']}"] if w["doi"] else [])
        if not keys: keys = [f"openalex:{w['id'].rsplit('/',1)[-1]}"]
        found = False
        for k in keys:
            r = subprocess.run([sys.executable, led, "get", k], capture_output=True, text=True, cwd=root)
            if r.stdout.strip() and "not found" not in r.stdout: found = True; break
        if not found:
            w["ledger_key"] = keys[0]; missing.append(w)
            print(json.dumps(dict(key=keys[0], type=w["type"], year=w["year"], venue=w["venue"], title=(w["title"] or "")[:150], has_abs=bool(w["abstract"]))))
    print(len(missing), "not in ledger", file=sys.stderr)
    json.dump(missing, open(inp + ".missing.json", "w"), indent=1)
if __name__ == "__main__":
    if sys.argv[1] == "fetch": fetch(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
    else: compare(sys.argv[2], sys.argv[3])
