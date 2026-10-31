"""Write one record YAML from Python and validate it against the schema on the spot.

    import sys; sys.path.insert(0, "tools"); from mkrecord import write
    write(source_type="pmid", source_id="23424695", full_text_source="PMC3570947",
          title=..., year=2013, study_type="case_report", key_findings=[...], relevance_to_jgct=...,
          tumor_site="ovary", n_jgct_patients=1, pmid="23424695", doi=..., pmcid="PMC3570947",
          alterations=[dict(gene=..., alteration=..., frequency=..., notes=...)],
          treatments=[dict(regimen=..., setting=..., n=..., outcome=...)], presentation=[...], notes=...)

Defaults: source_url (PubMed URL for pmid, https://doi.org/<doi> for doi), source_tier peer_reviewed,
retrieved_on today, language en, review_status draft, evidence_basis full_text. A record is written from
the full text (full_text_source required) or, when no open route to the full text exists, from the abstract:
pass evidence_basis="abstract", abstract_source=<URL>, full_text_source=None. Raises on schema errors and writes nothing.
File name: knowledge/records/<source_type>-<source_id with / replaced by _>.yaml.
For url sources pass source_url; source_id defaults to sha1(source_url)[:12].
"""
import datetime, hashlib, json, os
import yaml, jsonschema

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "knowledge", "records")
SCHEMA = json.load(open(os.path.join(ROOT, "knowledge", "schema", "record.schema.json")))
ORDER = list(SCHEMA["properties"])


def write(**f):
    st = f.setdefault("source_type", "pmid")
    if st == "url" and not f.get("source_id"):
        f["source_id"] = hashlib.sha1(f["source_url"].encode()).hexdigest()[:12]
    sid = str(f["source_id"])
    if st == "pmid":
        f.setdefault("pmid", sid)
        f.setdefault("source_url", f"https://pubmed.ncbi.nlm.nih.gov/{sid}/")
    elif st == "doi":
        f.setdefault("doi", sid)
        f.setdefault("source_url", f"https://doi.org/{sid}")
    d = dict(source_tier="peer_reviewed", retrieved_on=datetime.date.today().isoformat(), language="en", evidence_basis="full_text",
             abstract_source=None,
             pmid=None, doi=None, pmcid=None, journal=None, first_author=None, tumor_site=None, n_jgct_patients=None,
             age_range=None, alterations=[], treatments=[], presentation=[], conflicts_with=[], overlaps_with=[],
             superseded_by=None, retracted=False, notes=None, review_status="draft", reviewed_by=None, reviewed_on=None)
    d.update(f)
    d = {k: d[k] for k in ORDER if k in d} | {k: v for k, v in d.items() if k not in ORDER}
    jsonschema.validate(d, SCHEMA)
    path = os.path.join(OUT, f"{st}-{sid.replace('/', '_')}.yaml")
    yaml.safe_dump(d, open(path, "w"), sort_keys=False, allow_unicode=True, width=1000)
    print("wrote", os.path.relpath(path, ROOT))
    return path
