#!/usr/bin/env python3
"""Render knowledge/papers/*.yaml into INDEX.md and ALTERATIONS.md."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
PAPERS = HERE / "papers"
SCHEMA = json.loads((HERE / "schema" / "paper.schema.json").read_text())


def load_records() -> list[dict]:
    records = []
    for path in sorted(PAPERS.glob("*.yaml")):
        rec = yaml.safe_load(path.read_text())
        missing = [k for k in SCHEMA["required"] if k not in rec]
        if missing:
            sys.exit(f"{path.name}: missing required fields {missing}")
        if rec["study_type"] not in SCHEMA["properties"]["study_type"]["enum"]:
            sys.exit(f"{path.name}: invalid study_type {rec['study_type']!r}")
        records.append(rec)
    return records


def write_index(records: list[dict]) -> None:
    rows = ["# JGCT literature index", "",
            f"{len(records)} records. Status counts: "
            + ", ".join(f"{s} {sum(1 for r in records if r['review_status'] == s)}"
                        for s in ("reviewed", "draft")) + ".", "",
            "| Year | Title | Type | n | Status |", "|---|---|---|---|---|"]
    for r in sorted(records, key=lambda r: (-r["year"], r["title"])):
        link = f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"
        rows.append(f"| {r['year']} | [{r['title']}]({link}) | {r['study_type']} | "
                    f"{r.get('n_jgct_patients') or ''} | {r['review_status']} |")
    (HERE / "INDEX.md").write_text("\n".join(rows) + "\n")


def write_alterations(records: list[dict]) -> None:
    by_gene: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for r in records:
        for a in r.get("alterations") or []:
            by_gene[a["gene"].upper()].append((a, r))
    rows = ["# Reported alterations in JGCT", "",
            "Aggregated from the knowledge base. Draft records are included and marked.", "",
            "| Gene | Alteration | Frequency | Source | Status |", "|---|---|---|---|---|"]
    for gene in sorted(by_gene):
        for a, r in by_gene[gene]:
            src = f"[{r['first_author'] or 'PMID ' + r['pmid']} {r['year']}](https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/)"
            rows.append(f"| {gene} | {a['alteration']} | {a.get('frequency') or ''} | {src} | {r['review_status']} |")
    (HERE / "ALTERATIONS.md").write_text("\n".join(rows) + "\n")


if __name__ == "__main__":
    recs = load_records()
    write_index(recs)
    write_alterations(recs)
    print(f"wrote INDEX.md and ALTERATIONS.md from {len(recs)} records")
