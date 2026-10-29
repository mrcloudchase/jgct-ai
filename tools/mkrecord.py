"""Helper for writing a record YAML from Python: from mkrecord import rec; rec(pmid, doi, title, journal, year, first_author, study_type, n, key_findings, relevance, ...).
alts = (gene, alteration, frequency[, notes]); tx = (regimen, setting, n, outcome). Sets retrieved_on to D (edit per run) and review_status draft."""
import yaml, sys, os
import datetime
D=datetime.date.today().isoformat()
OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "knowledge", "records") + "/"
def rec(pmid, doi, title, journal, year, fa, study_type, n, key, rel, tier="peer_reviewed", full=False, conf=3, age=None, alts=(), tx=(), pres=(), conflicts=(), notes=None, method="verbatim_abstract"):
    r = dict(source_id=pmid, source_type="pmid", source_tier=tier, source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
             retrieved_on=D, full_text_read=full, language="en", pmid=pmid, doi=doi or None, title=title, journal=journal,
             year=year, first_author=fa, study_type=study_type, n_jgct_patients=n, age_range=age,
             alterations=[dict(gene=a[0], alteration=a[1], frequency=a[2], notes=a[3] if len(a)>3 else None) for a in alts],
             treatments=[dict(regimen=t[0], setting=t[1], n=t[2], outcome=t[3]) for t in tx],
             presentation=list(pres), key_findings=list(key), relevance_to_jgct=rel, conflicts_with=list(conflicts),
             superseded_by=None, retracted=False, notes=notes, confidence=conf, review_status="draft",
             reviewed_by=None, reviewed_on=None, extraction_method=method)
    yaml.safe_dump(r, open(OUT+f"pmid-{pmid}.yaml","w"), sort_keys=False, allow_unicode=True, width=1000)
    print("wrote", pmid)


def rec_url(url, title, year, study_type, key, rel, tier, conf, n=None, notes=None, method="verbatim_abstract", tx=(), first_author=None, journal=None, extra=None):
    """Record for a non-PMID source keyed by 12-char sha1 of the URL (source_type url)."""
    import hashlib
    sid = hashlib.sha1(url.encode()).hexdigest()[:12]
    r = dict(source_id=sid, source_type="url", source_tier=tier, source_url=url, retrieved_on=D, full_text_read=True, language="en",
             pmid=None, doi=None, title=title, journal=journal, year=year, first_author=first_author, study_type=study_type,
             n_jgct_patients=n, age_range=None, alterations=[], treatments=[dict(regimen=t[0], setting=t[1], n=t[2], outcome=t[3]) for t in tx],
             presentation=[], key_findings=list(key), relevance_to_jgct=rel, conflicts_with=[], superseded_by=None, retracted=False,
             notes=notes, confidence=conf, review_status="draft", reviewed_by=None, reviewed_on=None, extraction_method=method)
    r.update(extra or {})
    yaml.safe_dump(r, open(OUT + f"url-{sid}.yaml", "w"), sort_keys=False, allow_unicode=True, width=1000)
    print("wrote", f"url-{sid}", url)
    return sid
