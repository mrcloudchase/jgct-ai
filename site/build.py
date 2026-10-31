#!/usr/bin/env python3
"""Build the readable site from the knowledge base into _site/.

Everything a reader sees is generated from knowledge/records/*.yaml, knowledge/summary/*.md,
knowledge/topics/*.md and the ledger. The Pages workflow runs this on every push to main and
publishes _site/; it is never committed. To preview locally:

    python3 site/build.py && python3 -m http.server -d _site 8000

Requires the `markdown` and `pyyaml` packages.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "knowledge" / "records"
SUMMARY = ROOT / "knowledge" / "summary"
TOPICS = ROOT / "knowledge" / "topics"
LEDGER = ROOT / "state" / "ledger.sqlite"
RUNS = ROOT / "state" / "runs"
DOCS = ROOT / "_site"
ASSETS_SRC = ROOT / "site" / "assets"

SITE_TITLE = "JGCT Knowledge Base"
REPO_URL = "https://github.com/mrcloudchase/jgct-ai"
TIER_LABEL = {
    "peer_reviewed": "Peer-reviewed article", "guideline": "Guideline", "registry": "Registry report",
    "database": "Database entry", "preprint": "Preprint", "conference_abstract": "Conference abstract",
    "organization": "Organization page", "other": "Other",
}
TYPE_LABEL = {
    "case_report": "Case report", "case_series": "Case series", "cohort": "Cohort study", "genomic": "Genomic study",
    "review": "Review", "meta_analysis": "Meta-analysis", "trial": "Clinical trial", "registry": "Registry report",
    "guideline": "Guideline", "database_entry": "Database entry", "other": "Other",
}
SITE_LABEL = {"ovary": "Ovary", "testis": "Testis", "both": "Ovary and testis", "other": "Other", None: "Not stated"}
CITE_RE = re.compile(r"\[((?:pmid|url|doi|abstract)-[^\]\s,]+(?:\s*,\s*(?:pmid|url|doi|abstract)-[^\]\s,]+)*)\]")
MD = markdown.Markdown(extensions=["tables", "sane_lists", "smarty"])


# ----------------------------------------------------------------------------------------------- data

def load_records() -> dict[str, dict]:
    recs = {}
    for p in sorted(RECORDS.glob("*.yaml")):
        recs[p.stem] = yaml.safe_load(p.read_text())
    return recs


def load_pending() -> list[dict]:
    if not LEDGER.exists():
        return []
    con = sqlite3.connect(LEDGER)
    cols = [r[1] for r in con.execute("pragma table_info(items)")]
    rows = [dict(zip(cols, r)) for r in con.execute("select * from items where status in ('needs_full_text', 'abstract_only')")]
    con.close()
    for r in rows:
        r["year"] = str(r.get("year") or "")[:4]
    rows.sort(key=lambda r: (-int(r["year"] or 0), str(r.get("title") or "")))
    return rows


def last_run_date() -> str:
    files = sorted(RUNS.glob("*.md"))
    return files[-1].stem[:10] if files else date.today().isoformat()


def gene_key(name: str) -> str | None:
    token = re.split(r"[\s(]", name.strip())[0].upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9/-]{1,15}", token) or token in {"CHROMOSOMES", "CHROMOSOME", "GENETIC"}:
        return None
    return token


# ----------------------------------------------------------------------------------------------- html

def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


ABSTRACT_ONLY: set[str] = set()  # record stems whose evidence_basis is abstract; filled in main()


def cite_links(text: str, depth: str) -> str:
    """Turn [pmid-123, url-abc] into links to source pages. `depth` is the relative prefix to the site root.
    A source read only from its abstract is marked with a dagger and a class."""
    def one(i):
        if i in ABSTRACT_ONLY:
            return f"<a class=\"abs\" href=\"{depth}sources/{esc(i)}.html\" title=\"Source {esc(i)}: abstract only, full text not read\">{esc(i)}†</a>"
        return f"<a href=\"{depth}sources/{esc(i)}.html\" title=\"Source {esc(i)}\">{esc(i)}</a>"

    def repl(m):
        ids = [i.strip() for i in m.group(1).split(",")]
        return "<sup class=\"cite\">[" + ", ".join(one(i) for i in ids) + "]</sup>"
    return CITE_RE.sub(repl, text)


MD_LINK_RE = re.compile(r'href="(?!https?://|mailto:|#)([^"#]+?)\.md(#[^"]*)?"')


def md(text: str, depth: str) -> str:
    """Render Markdown; relative links to .md files (topic cross-links) become links to the built pages."""
    MD.reset()
    html_out = MD_LINK_RE.sub(lambda m: f'href="{m.group(1)}.html{m.group(2) or ""}"', MD.convert(text))
    return cite_links(html_out, depth)


def page(title: str, body: str, depth: str, stats: dict, active: str = "", description: str = "") -> str:
    nav = [("index.html", "Home", "home"), ("clinicians.html", "For clinicians", "clinicians"),
           ("families.html", "For families", "families"), ("topics/index.html", "Topics", "topics"),
           ("genes/index.html", "Genes", "genes"),
           ("treatments.html", "Treatments", "treatments"), ("cohorts.html", "Cohorts", "cohorts"),
           ("conflicts.html", "Where sources disagree", "conflicts"), ("sources/index.html", "All sources", "sources"),
           ("pending.html", "Not yet read in full", "pending"), ("about.html", "About", "about")]
    links = "".join(f'<a href="{depth}{href}"{" class=\"active\"" if key == active else ""}>{label}</a>' for href, label, key in nav)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {SITE_TITLE}</title>
<meta name="description" content="{esc(description or 'A knowledge base of everything known about juvenile granulosa cell tumor, built from sources read in full.')}">
<link rel="stylesheet" href="{depth}assets/style.css">
</head>
<body>
<header class="top">
  <a class="brand" href="{depth}index.html">{SITE_TITLE}</a>
  <form class="search" action="{depth}search.html" method="get" role="search">
    <input type="search" name="q" placeholder="Search sources…" aria-label="Search sources">
  </form>
</header>
<div class="layout">
<nav class="side" aria-label="Sections">{links}</nav>
<main>
{body}
</main>
</div>
<footer>
  <p><strong>Not medical advice.</strong> This site synthesizes published sources about juvenile granulosa cell tumor. It describes what those sources report. Decisions about any person's care belong with their care team.</p>
  <p>{stats['n_full']} sources read in full · {stats['n_abstract']} from abstracts only (†) · {stats['n_pending']} not yet read in full · last updated {stats['updated']} · <a href="{REPO_URL}">repository</a> · content CC BY 4.0</p>
</footer>
<script src="{depth}assets/site.js"></script>
</body>
</html>
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def source_link(stem: str, r: dict, depth: str) -> str:
    return f'<a href="{depth}sources/{esc(stem)}.html">{esc(r.get("first_author") or stem)} {esc(r["year"])}</a>'


def source_row(stem: str, r: dict, depth: str) -> str:
    n = r.get("n_jgct_patients")
    dag = ' <span class="abs" title="Abstract only, full text not read">†</span>' if stem in ABSTRACT_ONLY else ''
    return (f'<tr><td>{esc(r["year"])}</td><td><a href="{depth}sources/{esc(stem)}.html">{esc(r["title"])}</a>{dag}'
            f'<div class="muted">{esc(r.get("first_author") or "")}{", " + esc(r["journal"]) if r.get("journal") else ""}</div></td>'
            f'<td>{esc(TYPE_LABEL.get(r["study_type"], r["study_type"]))}</td><td>{esc(SITE_LABEL.get(r.get("tumor_site"), r.get("tumor_site")))}</td>'
            f'<td class="num">{esc(n) if n is not None else ""}</td></tr>')


def table(rows: list[str]) -> str:
    return ('<table class="sources"><thead><tr><th>Year</th><th>Source</th><th>Type</th><th>Site</th><th class="num">JGCT patients</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


# ----------------------------------------------------------------------------------------------- pages

def build_home(recs, stats, intro_md, topics=()):
    tiers = Counter(r["source_tier"] for r in recs.values())
    types = Counter(r["study_type"] for r in recs.values())
    sites = Counter(r.get("tumor_site") for r in recs.values())
    topic_list = ""
    if topics:
        lis = "".join(f'<li><a href="topics/{esc(stem)}.html">{esc(title)}</a></li>' for stem, title, _ in topics)
        topic_list = f'<h2>Topics</h2><p class="muted">One article per subject, from every relevant source. Each opens in plain language before the detail.</p><ul class="cols">{lis}</ul>'
    body = f"""
<h1>Juvenile granulosa cell tumor: what is known</h1>
<p class="lead">A knowledge base built from {stats['n_records']} sources about juvenile granulosa cell tumor (JGCT): {stats['n_full']} read in full, {stats['n_abstract']} known only from their abstracts. It exists for the clinicians and researchers who treat and study this rare tumor, and for the families who have just heard its name.</p>
<div class="doors">
  <a class="door" href="clinicians.html"><h2>For clinicians and researchers</h2><p>Epidemiology, presentation, pathology, molecular biology, staging, treatment, outcomes, and where the literature disagrees. Every sentence cited.</p></a>
  <a class="door" href="families.html"><h2>For parents and patients</h2><p>The same knowledge in plain language, with every term explained, what is established and what is uncertain, and questions worth asking the care team.</p></a>
</div>
<section class="stats">
  <div><span class="big">{stats['n_full']}</span>sources read in full</div>
  <div><span class="big">{sum(1 for r in recs.values() if (r.get('n_jgct_patients') or 0) >= 10)}</span>series of 10 or more patients</div>
  <div><span class="big">{tiers.get('guideline', 0)}</span>guidelines</div>
  <div><span class="big">{stats['n_abstract']}</span>known from the abstract only</div>
</section>
{topic_list}
<h2>How to read this site</h2>
<ul>
  <li><strong>Every claim is cited.</strong> A small bracketed code such as <sup class="cite">[<a href="sources/index.html">pmid-40272823</a>]</sup> is a source. Click it to see what was taken from that source and where its full text was read.</li>
  <li><strong>Full text first, abstracts marked.</strong> Most sources were read start to finish. Where no open route to the full text exists, the record rests on the abstract alone and every citation of it carries a dagger, like <sup class="cite">[<a class="abs" href="pending.html">pmid-6711799†</a>]</sup>. All of those are listed under <a href="pending.html">Not yet read in full</a>, where help with full text is most useful.</li>
  <li><strong>Disagreements are shown, not settled.</strong> Where sources conflict, both are presented under <a href="conflicts.html">Where sources disagree</a>.</li>
  <li><strong>Go deeper by topic.</strong> <a href="topics/index.html">Topics</a> holds one synthesized article per subject, written from every relevant source.</li>
  <li><strong>Browse by evidence.</strong> <a href="genes/index.html">Genes</a> lists every reported alteration by gene. <a href="treatments.html">Treatments</a> lists every regimen and outcome reported. <a href="cohorts.html">Cohorts</a> lists the larger series and registries.</li>
</ul>
<h2>What is in the base</h2>
<table class="kv">
<tr><th>By source type</th><td>{", ".join(f"{esc(TIER_LABEL.get(k, k))} {v}" for k, v in tiers.most_common())}</td></tr>
<tr><th>By study type</th><td>{", ".join(f"{esc(TYPE_LABEL.get(k, k))} {v}" for k, v in types.most_common())}</td></tr>
<tr><th>By tumor site</th><td>{", ".join(f"{esc(SITE_LABEL.get(k, k))} {v}" for k, v in sites.most_common())}</td></tr>
<tr><th>Years</th><td>{min(r['year'] for r in recs.values())} to {max(r['year'] for r in recs.values())}</td></tr>
</table>
"""
    return page("Home", body, "", stats, "home")


def read_summary(name: str) -> str:
    """A summary file, with its level-one heading removed (the page supplies its own)."""
    text = (SUMMARY / f"{name}.md").read_text()
    lines = text.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    return "\n".join(lines).strip()


def topic_title(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback.replace("-", " ").capitalize()


def build_topics(stats):
    files = sorted(p for p in TOPICS.glob("*.md") if p.name.lower() != "readme.md")
    entries = []
    for f in files:
        text = f.read_text()
        title = topic_title(text, f.stem)
        body_md = "\n".join(l for l in text.splitlines() if not l.startswith("# "))
        first = next((l for l in body_md.splitlines() if l.strip() and not l.startswith("#")), "")
        entries.append((f.stem, title, CITE_RE.sub("", first).strip()))
        body = f"<p class=\"crumbs\"><a href=\"index.html\">Topics</a> › {esc(title)}</p><h1>{esc(title)}</h1>" + md(body_md, "../")
        write(DOCS / "topics" / f"{f.stem}.html", page(title, body, "../", stats, "topics"))
    if entries:
        lis = "".join(f'<li><a href="{esc(stem)}.html"><strong>{esc(title)}</strong></a><div class="muted">{esc(blurb)}</div></li>' for stem, title, blurb in entries)
        body = f"<h1>Topics</h1><p class=\"lead\">One article per subject, synthesized from every relevant source: what the sources report, where they agree, where they disagree, and what remains unknown. Every sentence cited.</p><ul class=\"topics\">{lis}</ul>"
    else:
        body = "<h1>Topics</h1><p class=\"lead\">Topic articles are written by the maintenance runs from the records and appear here as they are completed. Until then, start with the two summaries.</p><p><a href=\"../clinicians.html\">For clinicians and researchers</a> · <a href=\"../families.html\">For parents and patients</a></p>"
    write(DOCS / "topics" / "index.html", page("Topics", body, "../", stats, "topics"))
    return entries


def build_audience(key, title, section_md, stats, lead):
    section_md = section_md.replace("](../topics/", "](topics/")
    body = f"<h1>{esc(title)}</h1><p class=\"lead\">{lead}</p>" + md(section_md, "")
    return page(title, body, "", stats, key)


def build_source_pages(recs, stats):
    for stem, r in recs.items():
        fts = str(r.get("full_text_source") or "")
        abstract_only = r.get("evidence_basis") == "abstract"
        if abstract_only:
            fts_html = f'<strong>Not read.</strong> This record rests on the abstract alone, read at <a href="{esc(r.get("abstract_source") or r["source_url"])}">{esc(r.get("abstract_source") or r["source_url"])}</a>; no open route to the full text was found. Every citation of it on this site carries a dagger (†).'
        elif fts.startswith("http"):
            fts_html = f'<a href="{esc(fts)}">{esc(fts)}</a>'
        elif fts.upper().startswith("PMC"):
            fts_html = f'<a href="https://pmc.ncbi.nlm.nih.gov/articles/{esc(fts)}/">{esc(fts)}</a>'
        else:
            fts_html = esc(fts)
        ids = []
        if r.get("pmid"):
            ids.append(f'PubMed <a href="https://pubmed.ncbi.nlm.nih.gov/{esc(r["pmid"])}/">{esc(r["pmid"])}</a>')
        if r.get("doi"):
            ids.append(f'DOI <a href="https://doi.org/{esc(r["doi"])}">{esc(r["doi"])}</a>')
        if r.get("pmcid"):
            ids.append(f'PMC <a href="https://pmc.ncbi.nlm.nih.gov/articles/{esc(r["pmcid"])}/">{esc(r["pmcid"])}</a>')

        def section(title, items, render):
            if not items:
                return ""
            return f"<h2>{title}</h2><ul>" + "".join(f"<li>{render(i)}</li>" for i in items) + "</ul>"

        def alt(a):
            s = f"<strong>{esc(a['gene'])}</strong>: {esc(a['alteration'])}"
            if a.get("frequency"):
                s += f" <span class=\"muted\">({esc(a['frequency'])})</span>"
            if a.get("notes"):
                s += f"<br><span class=\"muted\">{esc(a['notes'])}</span>"
            return s

        def tx(t):
            s = f"<strong>{esc(t['regimen'])}</strong>"
            bits = []
            if t.get("setting"):
                bits.append(esc(t["setting"]))
            if t.get("n") is not None:
                bits.append(f"n = {esc(t['n'])}")
            if bits:
                s += " <span class=\"muted\">(" + "; ".join(bits) + ")</span>"
            if t.get("outcome"):
                s += f"<br>Outcome: {esc(t['outcome'])}"
            return s

        rel = ""
        for label, key in (("Conflicts with", "conflicts_with"), ("Overlaps with", "overlaps_with")):
            links = [f'<a href="{esc(x)}.html">{esc(recs[x].get("first_author") or x)} {esc(recs[x]["year"])}: {esc(recs[x]["title"])}</a>' if x in recs else esc(x) for x in r.get(key) or []]
            if links:
                rel += f"<h2>{label}</h2><ul>" + "".join(f"<li>{l}</li>" for l in links) + "</ul>"
        if r.get("superseded_by"):
            rel += f'<p>Superseded by <a href="{esc(r["superseded_by"])}.html">{esc(r["superseded_by"])}</a>.</p>'

        body = f"""
<p class="crumbs"><a href="index.html">All sources</a> › {esc(stem)}</p>
<h1>{esc(r['title'])}</h1>
<p class="lead">{esc(r.get('first_author') or '')}{' · ' if r.get('first_author') and r.get('journal') else ''}{esc(r.get('journal') or '')} · {esc(r['year'])}{' · ' + esc(r['language']) if r.get('language') and r['language'] != 'en' else ''}</p>
<table class="kv">
<tr><th>Source type</th><td>{esc(TIER_LABEL.get(r['source_tier'], r['source_tier']))}</td></tr>
<tr><th>Study type</th><td>{esc(TYPE_LABEL.get(r['study_type'], r['study_type']))}</td></tr>
<tr><th>Tumor site</th><td>{esc(SITE_LABEL.get(r.get('tumor_site'), r.get('tumor_site')))}</td></tr>
<tr><th>JGCT patients</th><td>{esc(r['n_jgct_patients']) if r.get('n_jgct_patients') is not None else 'Not stated'}</td></tr>
<tr><th>Ages</th><td>{esc(r.get('age_range') or 'Not stated')}</td></tr>
<tr><th>Identifiers</th><td>{' · '.join(ids) or esc(r['source_url'])}</td></tr>
<tr><th>{'Evidence' if abstract_only else 'Full text read from'}</th><td>{fts_html}</td></tr>
<tr><th>Record</th><td><code>{esc(stem)}</code> · {esc(r['review_status'])}{' · reviewed by ' + esc(r['reviewed_by']) if r.get('reviewed_by') else ''} · retrieved {esc(r['retrieved_on'])}{' · <strong>retracted</strong>' if r.get('retracted') else ''}</td></tr>
</table>
<h2>Why it matters for JGCT</h2><p>{esc(r['relevance_to_jgct'])}</p>
<h2>Key findings</h2><ul>{''.join(f'<li>{esc(k)}</li>' for k in r['key_findings'])}</ul>
{section('Presentation', r.get('presentation') or [], esc)}
{section('Genetic and molecular findings', r.get('alterations') or [], alt)}
{section('Treatments reported', r.get('treatments') or [], tx)}
{rel}
{('<h2>Notes</h2><p class="muted">' + esc(r['notes']) + '</p>') if r.get('notes') else ''}
<p class="muted">{'Every statement above was taken from the abstract of this source; its full text has not been read.' if abstract_only else 'Every statement above was taken from the full text of this source.'} It is a draft until a human reviewer checks it against the source. <a href="{REPO_URL}/blob/main/knowledge/records/{esc(stem)}.yaml">View the record</a> · <a href="{REPO_URL}/issues/new?title=Correction%20to%20{esc(stem)}">Report a problem</a>.</p>
"""
        write(DOCS / "sources" / f"{stem}.html", page(r["title"], body, "../", stats, "sources", r["relevance_to_jgct"]))


def build_sources_index(recs, stats):
    by_year = defaultdict(list)
    for stem, r in recs.items():
        by_year[r["year"]].append((stem, r))
    parts = [f"<h1>All sources</h1><p class=\"lead\">{len(recs)} sources: {len(recs) - len(ABSTRACT_ONLY)} read in full and {len(ABSTRACT_ONLY)} known from their abstracts only (marked †). Newest first. Use the search box for a title, author, gene, or finding.</p>"]
    for y in sorted(by_year, reverse=True):
        rows = [source_row(s, r, "../") for s, r in sorted(by_year[y], key=lambda x: x[1]["title"])]
        parts.append(f"<h2 id=\"y{y}\">{y}</h2>" + table(rows))
    write(DOCS / "sources" / "index.html", page("All sources", "".join(parts), "../", stats, "sources"))


def build_genes(recs, stats):
    by_gene = defaultdict(list)
    for stem, r in recs.items():
        for a in r.get("alterations") or []:
            g = gene_key(a["gene"])
            if g:
                by_gene[g].append((stem, r, a))
    for g, items in by_gene.items():
        items.sort(key=lambda x: -x[1]["year"])
        rows = "".join(
            f"<tr><td>{source_link(s, r, '../')}<div class=\"muted\">{esc(r['title'])}</div></td><td>{esc(a['alteration'])}</td>"
            f"<td>{esc(a.get('frequency') or '')}</td><td class=\"num\">{esc(r.get('n_jgct_patients')) if r.get('n_jgct_patients') is not None else ''}</td><td class=\"muted\">{esc(a.get('notes') or '')}</td></tr>"
            for s, r, a in items)
        body = (f"<p class=\"crumbs\"><a href=\"index.html\">Genes</a> › {esc(g)}</p><h1>{esc(g)} in JGCT</h1>"
                f"<p class=\"lead\">Every reported finding about {esc(g)}, as each source states it. Frequencies are copied from the source, never computed across sources.</p>"
                f"<table class=\"sources\"><thead><tr><th>Source</th><th>Alteration</th><th>Frequency</th><th class=\"num\">JGCT patients</th><th>Notes</th></tr></thead><tbody>{rows}</tbody></table>")
        write(DOCS / "genes" / f"{g.replace('/', '-')}.html", page(f"{g} in JGCT", body, "../", stats, "genes"))
    items = sorted(by_gene.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    lis = "".join(f'<li><a href="{esc(g.replace("/", "-"))}.html">{esc(g)}</a> <span class="muted">{len(v)} finding{"s" if len(v) != 1 else ""} in {len({s for s, _, _ in v})} source{"s" if len({s for s, _, _ in v}) != 1 else ""}</span></li>' for g, v in items)
    body = ("<h1>Genes and molecular findings</h1><p class=\"lead\">Every gene or molecular feature any source reports in JGCT, with the number of findings recorded. Open a gene to see each source's statement side by side.</p>"
            f"<ul class=\"cols\">{lis}</ul>")
    write(DOCS / "genes" / "index.html", page("Genes", body, "../", stats, "genes"))


def build_treatments(recs, stats):
    items = [(s, r, t) for s, r in recs.items() for t in r.get("treatments") or []]
    items.sort(key=lambda x: (-x[1]["year"], x[1]["title"]))
    groups = defaultdict(list)
    for s, r, t in items:
        reg = t["regimen"].lower()
        if any(k in reg for k in ("chemo", "cisplatin", "carboplatin", "bep", "peb", "pei", "etoposide", "bleomycin", "paclitaxel", "ifosfamide", "cyclophosphamide")):
            groups["Chemotherapy"].append((s, r, t))
        elif any(k in reg for k in ("surg", "ectomy", "resection", "excision", "laparo", "enucleation", "staging", "debulk", "cystectomy", "orchi")):
            groups["Surgery"].append((s, r, t))
        elif any(k in reg for k in ("watch", "surveillance", "observation", "follow")):
            groups["Surveillance"].append((s, r, t))
        elif any(k in reg for k in ("radio", "hipec", "hormon", "inhibitor", "buserelin", "letrozole", "tamoxifen", "gnrh", "anti")):
            groups["Other therapies"].append((s, r, t))
        else:
            groups["Other or combined"].append((s, r, t))
    parts = [f"<h1>Treatments reported</h1><p class=\"lead\">Every treatment any source describes, with the setting and outcome exactly as that source reports it. {len(items)} entries from {len({s for s, _, _ in items})} sources. This is a list of what the literature reports, not a recommendation.</p>"]
    for name in ("Surgery", "Chemotherapy", "Surveillance", "Other therapies", "Other or combined"):
        rows = groups.get(name)
        if not rows:
            continue
        parts.append(f"<h2>{name}</h2><table class=\"sources\"><thead><tr><th>Source</th><th>Regimen</th><th>Setting</th><th class=\"num\">n</th><th>Outcome</th></tr></thead><tbody>" + "".join(
            f"<tr><td>{source_link(s, r, '')}</td><td>{esc(t['regimen'])}</td><td class=\"muted\">{esc(t.get('setting') or '')}</td><td class=\"num\">{esc(t['n']) if t.get('n') is not None else ''}</td><td>{esc(t.get('outcome') or '')}</td></tr>"
            for s, r, t in rows) + "</tbody></table>")
    write(DOCS / "treatments.html", page("Treatments reported", "".join(parts), "", stats, "treatments"))


def build_cohorts(recs, stats):
    big = sorted(((s, r) for s, r in recs.items() if (r.get("n_jgct_patients") or 0) >= 5 or r["study_type"] in ("registry", "guideline", "meta_analysis")),
                 key=lambda x: (-(x[1].get("n_jgct_patients") or 0), -x[1]["year"]))
    rows = []
    for s, r in big:
        rows.append(f"<tr><td class=\"num\"><strong>{esc(r.get('n_jgct_patients')) if r.get('n_jgct_patients') is not None else '–'}</strong></td><td>{source_link(s, r, '')}<div class=\"muted\">{esc(r['title'])}</div></td>"
                    f"<td>{esc(TYPE_LABEL.get(r['study_type'], r['study_type']))}</td><td>{esc(SITE_LABEL.get(r.get('tumor_site'), r.get('tumor_site')))}</td><td>{esc(r['key_findings'][0])}</td></tr>")
    body = ("<h1>Cohorts, registries, guidelines</h1><p class=\"lead\">The sources that carry the most weight: series of five or more patients, registry reports, guidelines and meta-analyses, largest first. Patient counts are as each source states them; overlapping cohorts are linked on each source's page and must not be added together.</p>"
            f"<table class=\"sources\"><thead><tr><th class=\"num\">JGCT</th><th>Source</th><th>Type</th><th>Site</th><th>First key finding</th></tr></thead><tbody>{''.join(rows)}</tbody></table>")
    write(DOCS / "cohorts.html", page("Cohorts, registries, guidelines", body, "", stats, "cohorts"))


def build_conflicts(recs, stats):
    seen, pairs = set(), []
    for s, r in recs.items():
        for other in r.get("conflicts_with") or []:
            key = tuple(sorted((s, other)))
            if key in seen or other not in recs:
                continue
            seen.add(key)
            pairs.append(key)
    parts = ["<h1>Where sources disagree</h1><p class=\"lead\">Pairs of sources whose findings conflict. The base records both and settles nothing; each source's page shows what it reports. Read the notes on each record for the specifics.</p>"]
    if not pairs:
        parts.append("<p>No conflicts recorded yet.</p>")
    for a, b in pairs:
        ra, rb = recs[a], recs[b]
        parts.append(f"""<div class="pair">
<div><h3>{source_link(a, ra, '')}</h3><p class="muted">{esc(ra['title'])}</p><p>{esc(ra['key_findings'][0])}</p>{('<p class="muted">' + esc(ra['notes']) + '</p>') if ra.get('notes') else ''}</div>
<div><h3>{source_link(b, rb, '')}</h3><p class="muted">{esc(rb['title'])}</p><p>{esc(rb['key_findings'][0])}</p>{('<p class="muted">' + esc(rb['notes']) + '</p>') if rb.get('notes') else ''}</div>
</div>""")
    write(DOCS / "conflicts.html", page("Where sources disagree", "".join(parts), "", stats, "conflicts"))


def build_pending(pending, stats):
    abs_items = [p for p in pending if p.get("status") == "abstract_only"]
    nft = [p for p in pending if p.get("status") != "abstract_only"]
    parts = [f"<h1>Not yet read in full</h1><p class=\"lead\">{len(pending)} relevant sources whose full text could not be obtained by any open route. {len(abs_items)} of them have a record written from the abstract alone (marked † wherever they are cited); {len(nft)} have no record yet. Every one is retried on every run. If you have library access to any of these, they are the fastest way to make this knowledge base more complete.</p>"]

    def listing(items, with_record):
        by_year = defaultdict(list)
        for p in items:
            by_year[p["year"] or "undated"].append(p)
        out = []
        for y in sorted(by_year, reverse=True):
            lis = []
            for p in by_year[y]:
                pid = str(p.get("id") or "")
                link = f'https://pubmed.ncbi.nlm.nih.gov/{pid[5:]}/' if pid.startswith("pmid:") else (f'https://doi.org/{pid[4:]}' if pid.startswith("doi:") else "")
                t = esc(p.get("title") or pid)
                rec = f' · <a href="sources/{esc(p["record"])}.html">record</a>' if with_record and p.get("record") else ""
                lis.append(f"<li>{f'<a href=\"{esc(link)}\">{t}</a>' if link else t}<span class=\"muted\"> {esc(pid)}{rec}</span></li>")
            out.append(f"<h3>{esc(y)}</h3><ul>{''.join(lis)}</ul>")
        return "".join(out)

    parts.append("<h2>Known from the abstract only</h2>" + (listing(abs_items, True) or "<p>None.</p>"))
    parts.append("<h2>No record yet</h2><p class=\"muted\">Relevant by title or abstract, but neither full text nor an abstract usable for a record.</p>" + (listing(nft, False) or "<p>None.</p>"))
    write(DOCS / "pending.html", page("Not yet read in full", "".join(parts), "", stats, "pending"))


def build_about(stats):
    body = f"""
<h1>About this knowledge base</h1>
<p class="lead">A centralized, cited, continuously maintained account of everything known about juvenile granulosa cell tumor.</p>
<h2>Why it exists</h2>
<p>JGCT is rare. What is known about it is scattered across a few hundred papers, conference abstracts, registry reports, guidelines and databases, in several languages, much of it behind paywalls. A family that hears the diagnosis, or a clinician who sees one case in a career, has no single place to go. This is that place. It was started by a parent whose seven-year-old daughter is being treated for JGCT.</p>
<h2>How it is built</h2>
<ul>
<li><strong>Full text first; abstracts only when there is no other way, and always marked.</strong> A source is read start to finish whenever an open route to its text exists. Where none does, the record rests on the abstract alone, says so, and every citation of it carries a dagger (†). Nothing is taken from a citation or from memory. Sources not yet read in full are listed under <a href="pending.html">Not yet read in full</a>.</li>
<li><strong>Numbers are copied, never computed.</strong> A source that says "4 of 31" is recorded as 4 of 31. Patient counts from overlapping cohorts are linked, not summed.</li>
<li><strong>Disagreements are recorded, not resolved.</strong> See <a href="conflicts.html">Where sources disagree</a>.</li>
<li><strong>Every claim traces to its source.</strong> Each bracketed citation opens a page showing exactly what was taken from that source and where its full text was read.</li>
<li><strong>It is maintained by an AI agent and judged by a human.</strong> Once a month an agent reads the whole base, searches for everything new about JGCT, reads it in full, and opens a pull request. The maintainer reviews every change before it is published. The agent never rates its own work; every record is a draft until a person has checked it against its source.</li>
</ul>
<h2>What it is not</h2>
<p>It is not medical advice, and it does not recommend treatment for anyone. It reports what published sources say. Decisions about a person's care belong with that person's care team, who can use this site to find the sources quickly.</p>
<h2>Help it grow</h2>
<p>The biggest gap is full text behind paywalls. Many of the field's foundational papers are on the <a href="pending.html">Not yet read in full</a> list, known here only from their abstracts. If you have library access or are an author of one of them, the <a href="{REPO_URL}">repository</a> explains how to help. Corrections to any record are welcome there too.</p>
<h2>Licenses and source</h2>
<p>Content is CC BY 4.0. The code that builds this site is MIT. Everything lives at <a href="{REPO_URL}">{REPO_URL}</a>. This site was last rebuilt on {stats['updated']} from {stats['n_records']} sources, {stats['n_full']} read in full and {stats['n_abstract']} from abstracts.</p>
"""
    write(DOCS / "about.html", page("About", body, "", stats, "about"))


def build_search(recs, stats):
    index = [{"id": s, "title": r["title"], "year": r["year"], "type": TYPE_LABEL.get(r["study_type"], r["study_type"]),
              "site": SITE_LABEL.get(r.get("tumor_site"), r.get("tumor_site")), "author": r.get("first_author") or "",
              "text": " ".join(r["key_findings"]) + " " + " ".join(a["gene"] for a in r.get("alterations") or []) + " " + r["relevance_to_jgct"]}
             for s, r in recs.items()]
    write(DOCS / "search.json", json.dumps(index, ensure_ascii=False))
    body = """<h1>Search</h1><p class="lead">Searches titles, authors, genes and key findings of every source. Results update as you type.</p>
<input id="q" type="search" placeholder="e.g. AKT1, precocious puberty, chemotherapy stage IC2" autofocus>
<div id="results"></div>"""
    write(DOCS / "search.html", page("Search", body, "", stats, ""))


def main() -> None:
    recs = load_records()
    pending = load_pending()
    ABSTRACT_ONLY.update(s for s, r in recs.items() if r.get("evidence_basis") == "abstract")
    stats = {"n_records": len(recs), "n_full": len(recs) - len(ABSTRACT_ONLY), "n_abstract": len(ABSTRACT_ONLY),
             "n_pending": len(pending), "updated": last_run_date()}
    if DOCS.exists():
        for p in DOCS.iterdir():
            if p.name != "CNAME":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    DOCS.mkdir(exist_ok=True)
    (DOCS / ".nojekyll").write_text("")
    shutil.copytree(ASSETS_SRC, DOCS / "assets")
    topics = build_topics(stats)
    write(DOCS / "index.html", build_home(recs, stats, "", topics))
    n_topics = len(topics)
    write(DOCS / "clinicians.html", build_audience("clinicians", "For clinicians and researchers", read_summary("clinicians"), stats,
          "A technical synthesis of the knowledge base. Every factual sentence cites the sources it rests on; click a citation to see what that source reports and where its full text was read."))
    write(DOCS / "families.html", build_audience("families", "For parents and patients", read_summary("families"), stats,
          "The same knowledge in plain language. Terms are explained the first time they appear. This is a synthesis of published sources, not medical advice; you can show any paragraph, with its sources, to your care team."))
    build_source_pages(recs, stats)
    build_sources_index(recs, stats)
    build_genes(recs, stats)
    build_treatments(recs, stats)
    build_cohorts(recs, stats)
    build_conflicts(recs, stats)
    build_pending(pending, stats)
    build_about(stats)
    build_search(recs, stats)
    n_pages = sum(1 for _ in DOCS.rglob("*.html"))
    print(f"built _site/: {n_pages} pages from {len(recs)} records, {n_topics} topics, {len(pending)} pending")


if __name__ == "__main__":
    main()
