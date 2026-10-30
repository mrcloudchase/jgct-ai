#!/usr/bin/env python3
"""Find and fetch the full text of a source, save it as plain text, report where it came from.

  python3 -I tools/fulltext.py locate <id> [<id> ...]   # OA lookup only: Europe PMC + Unpaywall; one JSON line per id
  python3 -I tools/fulltext.py get <id> [--url URL]     # fetch full text to state/cache/fulltext/<stem>.txt

<id> is pmid:<n>, doi:<doi>, or a bare PMID. `get` tries, in order:
  1. PMC XML from Europe PMC (fullTextXML), then NCBI PMC efetch, then the PMC website article
     page (browser UA; reaches non-OA free/author-manuscript PMC articles) -> full_text_source "PMC<id>"
  2. Unpaywall OA locations (PDF or landing HTML), then the DOI landing page -> full_text_source "<url>"
  3. --url, if given (a PDF or HTML page you located yourself); tried first. A PMC or Europe PMC
     article URL is read from the PMC website and reported as "PMC<id>"
  --accept saves the --url text even if the length/section heuristic says it is not full text
  (for non-English articles or short complete items such as a conference abstract page)
Text whose words do not match the expected title (Europe PMC metadata) is refused as a wrong article.
It prints `FULLTEXT_SOURCE <value>`, `TEXT <path>`, `CHARS <n>` on success, or `NO_FULLTEXT <routes tried>`.
The text keeps section headings, paragraphs, table rows and figure captions (PMC XML), or the
page text of a PDF (pypdf). A result is only full text if you then read it and it contains the
article body; abstract-only landing pages are refused by a length/heading heuristic but check anyway.

Downloads are untrusted: run with `python3 -I`; raw files go to state/cache/ (gitignored).
"""
import io, json, os, re, site, sys, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CACHE = os.path.join(ROOT, "state", "cache", "fulltext")
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
EU = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
MAIL = os.environ.get("UNPAYWALL_EMAIL", "jgct-ai-research@example.org")
UA = "Mozilla/5.0 (X11; Linux x86_64) jgct-ai/1.0 (research knowledge base; mailto:%s)" % MAIL
# The PMC website answers a custom UA with reCAPTCHA but serves the article to a plain browser UA.
BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def get(url, tries=2, binary=False, timeout=30, ua=UA):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
                ctype = r.headers.get("Content-Type", "")
                return (data if binary else data.decode("utf-8", "replace")), ctype, r.geturl()
        except Exception as e:
            last = e
            if getattr(e, "code", None) in (401, 403, 404, 410):
                break
            time.sleep(2 + 2 * i)
    raise last


def norm(i):
    i = i.strip()
    if i.isdigit():
        return "pmid", i
    k, v = i.split(":", 1)
    return k, v


def epmc_meta(kind, val):
    q = f"EXT_ID:{val} AND SRC:MED" if kind == "pmid" else f'DOI:"{val}"'
    try:
        r = json.loads(get(EPMC + "search?format=json&resultType=core&query=" + urllib.parse.quote(q))[0])
        res = r["resultList"]["result"]
        return res[0] if res else {}
    except Exception:
        return {}


def unpaywall(doi):
    try:
        return json.loads(get(f"https://api.unpaywall.org/v2/{urllib.parse.quote(doi)}?email={MAIL}")[0])
    except Exception as e:
        return {"error": str(e)}


def locate(i):
    kind, val = norm(i)
    m = epmc_meta(kind, val)
    doi = val if kind == "doi" else m.get("doi")
    out = {"id": i, "title": m.get("title"), "pmid": m.get("pmid") or (val if kind == "pmid" else None), "doi": doi, "pmcid": m.get("pmcid"),
           "isOpenAccess": m.get("isOpenAccess"), "inEPMC": m.get("inEPMC"), "inPMC": m.get("inPMC"), "oa_urls": []}
    if doi:
        u = unpaywall(doi)
        for loc in u.get("oa_locations") or []:
            for k in ("url_for_pdf", "url_for_landing_page", "url"):
                if loc.get(k) and loc[k] not in out["oa_urls"]:
                    out["oa_urls"].append(loc[k])
        out["unpaywall_is_oa"] = u.get("is_oa")
    for f in (m.get("fullTextUrlList") or {}).get("fullTextUrl", []):
        if f.get("availabilityCode") in ("OA", "F", "Free") and f.get("url") not in out["oa_urls"]:
            out["oa_urls"].append(f["url"])
    return out


def xtext(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip() if el is not None else ""


def pmc_text(x):
    root = ET.fromstring(x)
    body = root.find(".//body")
    if body is None:
        return None
    out = []
    t = root.find(".//article-meta//article-title")
    out.append("# " + xtext(t))
    ab = root.find(".//article-meta/abstract")
    if ab is not None:
        out.append("\n## Abstract\n" + xtext(ab))
    skip = set()
    for el in body.iter():
        if el in skip:
            continue
        if el.tag == "title":
            out.append("\n## " + xtext(el))
        elif el.tag == "p":
            out.append(xtext(el))
        elif el.tag == "table-wrap":
            out.append("\n[TABLE] " + xtext(el.find("label")) + " " + xtext(el.find("caption")))
            for tr in el.findall(".//tr"):
                out.append(" | ".join(xtext(td) for td in tr))
            for f in el.findall(".//table-wrap-foot"):
                out.append("[TABLE FOOT] " + xtext(f))
            skip.update(el.iter())
        elif el.tag == "fig":
            out.append("\n[FIGURE] " + xtext(el.find("label")) + " " + xtext(el.find("caption")))
            skip.update(el.iter())
    for tw in root.findall(".//back//table-wrap") + root.findall(".//floats-group//table-wrap"):
        out.append("\n[TABLE] " + xtext(tw.find("label")) + " " + xtext(tw.find("caption")))
        for tr in tw.findall(".//tr"):
            out.append(" | ".join(xtext(td) for td in tr))
    for f in root.findall(".//floats-group//fig"):
        out.append("\n[FIGURE] " + xtext(f.find("label")) + " " + xtext(f.find("caption")))
    return "\n".join(out)


class _H(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "section", "table", "figcaption"}

    def __init__(self):
        super().__init__(); self.parts = []; self.skip = 0

    def handle_starttag(self, tag, a):
        if tag in ("script", "style", "nav", "header", "footer", "noscript"):
            self.skip += 1
        if tag in self.BLOCK:
            self.parts.append("\n")
        if tag in ("td", "th"):
            self.parts.append(" | ")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "header", "footer", "noscript") and self.skip:
            self.skip -= 1

    def handle_data(self, d):
        if not self.skip:
            self.parts.append(d)


def html_text(h):
    p = _H(); p.feed(h)
    t = "".join(p.parts)
    return re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", t)).strip()


def pdf_text(b):
    try:
        import pypdf
    except ImportError:
        sys.path.append(site.getusersitepackages())
        import pypdf
    r = pypdf.PdfReader(io.BytesIO(b))
    return "\n".join(f"\n[PAGE {n + 1}]\n" + (p.extract_text() or "") for n, p in enumerate(r.pages))


def pmc_html_text(pmc):
    """Article body from the PMC website (covers free-to-read and author-manuscript articles that
    are outside the OA subset, for which fullTextXML/efetch return no body)."""
    # PMC answers bursts with a reCAPTCHA page: back off and retry slowly, never try to solve it.
    for wait in (0, 30, 90, 180):
        time.sleep(wait)
        h = get(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc}/", ua=BROWSER_UA)[0]
        k = h.find('aria-label="Article content"')
        if k >= 0 or "recaptcha" not in h.lower():
            break
    if k < 0:
        return None
    m = re.search(r'name="citation_pmid"\s+content="(\d+)"', h) or re.search(r'content="(\d+)"\s+name="citation_pmid"', h)
    pmc_html_text.pmid = m.group(1) if m else None
    h = h[k:]
    t = html_text("<section " + h)
    return t


def looks_full(t):
    """Heuristic: body-length text with at least two typical section words."""
    if not t or len(t) < 6000:
        return False
    s = t.lower()
    return sum(w in s for w in ("introduction", "case report", "case presentation", "discussion", "methods", "results", "references", "conclusion")) >= 2


PMC_URL = re.compile(r"(?:ncbi\.nlm\.nih\.gov/pmc/articles/|pmc\.ncbi\.nlm\.nih\.gov/articles/|europepmc\.org/articles/)(?:PMC)?(\d+)", re.I)


def fetch_url(u):
    m = PMC_URL.search(u)
    if m:
        pmc = "PMC" + m.group(1)
        return pmc_html_text(pmc), pmc
    data, ctype, final = get(u, binary=True)
    if data[:4] == b"%PDF" or "pdf" in ctype:
        return pdf_text(data), final
    h = data.decode("utf-8", "replace")
    # follow citation_pdf_url meta if the page offers one and the HTML itself is thin
    t = html_text(h)
    if not looks_full(t):
        m = re.search(r'<meta[^>]+name="citation_pdf_url"[^>]+content="([^"]+)"', h) or re.search(r'content="([^"]+)"[^>]+name="citation_pdf_url"', h)
        if m:
            d2, c2, f2 = get(urllib.parse.urljoin(final, m.group(1)), binary=True)
            if d2[:4] == b"%PDF":
                return pdf_text(d2), f2
    return t, final


def title_ok(text, title):
    """True unless the expected title is known and few of its content words occur in the text
    (guards against a wrong article behind a PMCID or URL; PMC once served a tuberculosis paper
    under PMID 26894074). Non-Latin texts pass."""
    if not title or not text:
        return True
    words = {w for w in re.findall(r"[a-z]{5,}", title.lower())}
    if len(words) < 3:
        return True
    low = text.lower()
    if len(re.findall(r"[a-z]", low)) < len(low) * 0.3:
        return True
    return sum(w in low for w in words) / len(words) >= 0.5


def save(stem, text, src):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, stem + ".txt")
    open(p, "w").write(text)
    print("FULLTEXT_SOURCE", src); print("TEXT", os.path.relpath(p, ROOT)); print("CHARS", len(text))
    return 0


def get_full(i, url=None, accept=False):
    kind, val = norm(i)
    stem = (kind + "-" + val).replace("/", "_")
    tried = []
    if url:
        try:
            t, final = fetch_url(url)
            got = getattr(pmc_html_text, "pmid", None) if final.startswith("PMC") else None
            if kind == "pmid" and got and got != val:
                tried.append(f"{url}: page is PMID {got}, not {val}")
                t = None
            if t and (looks_full(t) or accept):
                return save(stem, t, final if final.startswith("PMC") else url)
            tried.append(f"{url}: too short/not body ({len(t or '')} chars)")
        except Exception as e:
            tried.append(f"{url}: {e}")
    loc = locate(i)
    pmc = loc.get("pmcid")
    if pmc:
        for name, u in (("epmc", EPMC + pmc + "/fullTextXML"), ("ncbi", EU + "efetch.fcgi?db=pmc&id=" + pmc.replace("PMC", ""))):
            try:
                x = get(u)[0]
                t = pmc_text(x)
                if t and len(t) > 2500 and not title_ok(t, loc.get("title")):
                    tried.append(f"{name} {pmc}: text does not match the expected title (wrong article?)")
                elif t and len(t) > 2500:
                    return save(stem, t, pmc)
                tried.append(f"{name} {pmc}: no body")
            except Exception as e:
                tried.append(f"{name} {pmc}: {e}")
        try:
            t = pmc_html_text(pmc)
            got = getattr(pmc_html_text, "pmid", None)
            if t and kind == "pmid" and got and got != val:
                tried.append(f"pmc-html {pmc}: page is PMID {got}, not {val} (wrong PMCID mapping)")
            elif t and looks_full(t) and not title_ok(t, loc.get("title")):
                tried.append(f"pmc-html {pmc}: text does not match the expected title (wrong article?)")
            elif t and looks_full(t):
                return save(stem, t, pmc)
            else:
                tried.append(f"pmc-html {pmc}: no body ({len(t or '')} chars)")
        except Exception as e:
            tried.append(f"pmc-html {pmc}: {e}")
    else:
        tried.append("no PMCID")
    urls = loc["oa_urls"] + ([f"https://doi.org/{loc['doi']}"] if loc.get("doi") else [])
    for u in urls:
        if "europepmc.org" in u or "ncbi.nlm.nih.gov/pmc" in u:
            continue
        try:
            t, final = fetch_url(u)
            if looks_full(t) and not title_ok(t, loc.get("title")):
                tried.append(f"{u}: text does not match the expected title (wrong article?)")
            elif looks_full(t):
                return save(stem, t, final if final.startswith("http") else u)
            tried.append(f"{u}: not full text ({len(t or '')} chars)")
        except Exception as e:
            tried.append(f"{u}: {str(e)[:80]}")
    print("NO_FULLTEXT", " ; ".join(tried))
    return 1


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "locate":
        for a in args:
            print(json.dumps(locate(a)), flush=True)
    elif cmd == "get":
        url = None
        accept = "--accept" in args
        if accept:
            args.remove("--accept")
        if "--url" in args:
            k = args.index("--url"); url = args[k + 1]; del args[k:k + 2]
        sys.exit(get_full(args[0], url, accept))
    else:
        print(__doc__); sys.exit(2)
