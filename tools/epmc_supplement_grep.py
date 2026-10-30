"""Fetch a congress-supplement full text from Europe PMC (fallback NCBI PMC efetch) and print each
abstract-sized unit (sec / boxed-text / sub-article) that matches a regex, verbatim (tags stripped).
Usage: [WINDOW=25] python3 -I epmc_supplement_grep.py <PMCID> [regex] [cache_dir]
Default regex: juvenile[ -]granulosa|JGCT|juvenile type granulosa
Supplements outside the PMC OA subset have no XML; the PMC website text (via fulltext.py) is used
instead and each match is printed with a window of surrounding lines (--window N, default 25),
overlapping windows merged. Read the window and widen it until the whole abstract is in view."""
import sys, re, os, html, urllib.request
pmc = sys.argv[1]; pat = re.compile(sys.argv[2] if len(sys.argv) > 2 else r"juvenile[ -](type )?granulosa|JGCT", re.I)
cache = sys.argv[3] if len(sys.argv) > 3 else "state/cache/supp"
fn = os.path.join(cache, pmc + ".xml")
if not os.path.exists(fn):
    for url in (f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmc}/fullTextXML",
                f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmc.replace('PMC','')}&retmode=xml"):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "jgct-ai"}), timeout=300).read()
            if b"<body" in data or b"<sec" in data or b"<sub-article" in data:
                open(fn, "wb").write(data); break
        except Exception as e:
            print("fetch failed", url, e, file=sys.stderr)
if not os.path.exists(fn):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fulltext
    tfn = os.path.join(cache, pmc + ".txt")
    if not os.path.exists(tfn):
        t = fulltext.pmc_html_text(pmc)
        if not t:
            sys.exit("no full text for " + pmc)
        os.makedirs(cache, exist_ok=True); open(tfn, "w").write(t)
    lines = open(tfn, encoding="utf-8", errors="replace").read().splitlines()
    w = int(os.environ.get("WINDOW", "25"))
    hits = [i for i, l in enumerate(lines) if pat.search(l)]
    spans = []
    for i in hits:
        a, b = max(0, i - w), min(len(lines), i + w + 1)
        if spans and a <= spans[-1][1]:
            spans[-1][1] = b
        else:
            spans.append([a, b])
    for n, (a, b) in enumerate(spans, 1):
        print(f"===== {pmc} window {n} (lines {a + 1}-{b}) =====\n" + "\n".join(lines[a:b]) + "\n")
    print(f"[{pmc}] {len(hits)} matching lines in {len(spans)} windows; text {len(lines)} lines (PMC website)", file=sys.stderr)
    sys.exit(0)
x = open(fn, encoding="utf-8", errors="replace").read()
def clean(s):
    s = re.sub(r"<(title|p|sec|label)[^>]*>", "\n", s)
    return re.sub(r"[ \t]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
# candidate units: innermost <sec> elements at the level that contains a title; fall back to paragraphs
units = re.findall(r"<sub-article.*?</sub-article>", x, re.S) or []
if not units:
    # split on top-level secs inside body
    body = re.search(r"<body.*?</body>", x, re.S)
    body = body.group(0) if body else x
    # split on <sec ...><title> boundaries
    parts = re.split(r"(?=<sec[ >])", body)
    units = parts
seen = 0
for u in units:
    if pat.search(u):
        t = clean(u)
        if pat.search(t):
            seen += 1
            print(f"===== {pmc} unit {seen} =====\n{t[:6000]}\n")
print(f"[{pmc}] {seen} matching units; xml {len(x)} chars", file=sys.stderr)
