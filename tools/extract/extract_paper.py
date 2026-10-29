#!/usr/bin/env python3
"""Draft a knowledge-base record for one PubMed ID using Claude structured outputs.

Usage: python extract/extract_paper.py <pmid> [--force]
Writes knowledge/records/pmid-<pmid>.yaml with review_status: draft. Requires ANTHROPIC_API_KEY.
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Literal, Optional

import anthropic
import requests
import yaml
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
RECORDS = ROOT / "knowledge" / "records"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


class Alteration(BaseModel):
    gene: str
    alteration: str = Field(description="e.g. 'p.C134W', 'truncating', 'rearrangement with CLPTM1L', 'in-frame duplication'")
    frequency: Optional[str] = Field(default=None, description="e.g. '4/31' or '13%', null if not stated")
    notes: Optional[str] = None


class Treatment(BaseModel):
    regimen: str
    setting: Optional[str] = Field(default=None, description="e.g. 'adjuvant stage IC', 'recurrent disease'")
    n: Optional[int] = Field(default=None, description="Number of patients given this regimen, null if not stated")
    outcome: Optional[str] = None


class PaperRecord(BaseModel):
    study_type: Literal["case_report", "case_series", "cohort", "genomic", "review", "trial", "registry", "guideline", "other"]
    n_jgct_patients: Optional[int] = Field(default=None, description="Number of JGCT patients or tumors, null if not stated")
    age_range: Optional[str] = Field(default=None, description="Patient age or age range exactly as stated")
    alterations: list[Alteration] = Field(description="Only alterations the abstract explicitly reports in JGCT. Empty list if none.")
    treatments: list[Treatment] = Field(description="Only treatments the abstract explicitly describes. Empty list if none.")
    presentation: list[str] = Field(description="Clinical presentation features the abstract reports, e.g. precocious puberty, abdominal mass. Empty list if none.")
    key_findings: list[str] = Field(description="Two to five findings, each one sentence, stated only from the abstract")
    relevance_to_jgct: str = Field(description="One sentence on why this paper matters for JGCT specifically")


def fetch(pmid: str) -> dict:
    r = requests.get(f"{EUTILS}/efetch.fcgi", params={"db": "pubmed", "id": pmid, "retmode": "xml"}, timeout=60)
    r.raise_for_status()
    art = ET.fromstring(r.text).find(".//PubmedArticle")
    if art is None:
        sys.exit(f"PMID {pmid} not found")
    a = art.find(".//Article")
    doi = next((i.text for i in art.findall(".//ArticleId") if i.get("IdType") == "doi"), None)
    first = a.find(".//Author")
    return {
        "pmid": pmid,
        "doi": doi,
        "title": "".join(a.find("ArticleTitle").itertext()),
        "journal": a.findtext(".//Journal/Title"),
        "year": int((a.findtext(".//PubDate/Year") or a.findtext(".//PubDate/MedlineDate") or "0")[:4]),
        "first_author": f"{first.findtext('LastName')} {first.findtext('Initials')}" if first is not None else None,
        "abstract": "\n".join(f"{t.get('Label', '')}: {t.text or ''}".strip(": ") for t in a.findall(".//AbstractText")),
    }


def extract(meta: dict) -> PaperRecord:
    client = anthropic.Anthropic()
    prompt = (
        "Extract a structured record for a juvenile granulosa cell tumor (JGCT) knowledge base from this PubMed abstract. "
        "Use only what the abstract states. Do not infer frequencies or treatments that are not written. "
        "If the paper is about adult granulosa cell tumor or another tumor and only mentions JGCT in passing, "
        "say so in relevance_to_jgct and keep alterations and treatments empty unless they are explicitly about JGCT.\n\n"
        f"Title: {meta['title']}\nJournal: {meta['journal']}, {meta['year']}\n\nAbstract:\n{meta['abstract']}"
    )
    resp = client.messages.parse(
        model="claude-opus-5-5",
        max_tokens=8000,
        output_config={"effort": "high"},
        messages=[{"role": "user", "content": prompt}],
        output_format=PaperRecord,
    )
    if resp.stop_reason == "refusal":
        sys.exit("Claude declined this abstract; write the record by hand.")
    return resp.parsed_output


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pmid")
    ap.add_argument("--force", action="store_true", help="overwrite an existing record")
    args = ap.parse_args()
    out = RECORDS / f"pmid-{args.pmid}.yaml"
    if out.exists() and not args.force:
        sys.exit(f"{out} exists; use --force to overwrite")
    meta = fetch(args.pmid)
    if not meta["abstract"]:
        sys.exit("No abstract on PubMed; write this record by hand from the full text.")
    rec = extract(meta)
    from datetime import date
    record = {
        "source_id": meta["pmid"], "source_type": "pmid", "source_tier": "peer_reviewed",
        "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{meta['pmid']}/", "retrieved_on": date.today().isoformat(),
        "full_text_read": False, "language": "en",
        "pmid": meta["pmid"], "doi": meta["doi"], "title": meta["title"], "journal": meta["journal"],
        "year": meta["year"], "first_author": meta["first_author"],
        **rec.model_dump(),
        "conflicts_with": [], "superseded_by": None, "retracted": False,
        "notes": "Drafted from the PubMed abstract by tools/extract/extract_paper.py.",
        "confidence": 3, "review_status": "draft", "reviewed_by": None, "reviewed_on": None,
    }
    out.write_text(yaml.safe_dump(record, sort_keys=False, allow_unicode=True, width=120))
    print(f"wrote {out} (draft). Review it against the paper, then set review_status: reviewed.")


if __name__ == "__main__":
    main()
