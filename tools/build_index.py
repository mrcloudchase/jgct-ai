#!/usr/bin/env python3
"""Render knowledge/records/*.yaml into INDEX.md, ALTERATIONS.md and TREATMENTS.md. Run tools/validate.py first."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "knowledge"
RECORDS = KB / "records"


def load() -> list[tuple[str, dict]]:
    out = []
    for p in sorted(RECORDS.glob("*.yaml")):
        out.append((p.stem, yaml.safe_load(p.read_text())))
    return out


def src(stem: str, r: dict) -> str:
    who = r.get("first_author") or stem
    return f"[{who} {r['year']}]({r['source_url']})"


def write_index(recs):
    tiers = defaultdict(int)
    for _, r in recs:
        tiers[r["source_tier"]] += 1
    lines = ["# JGCT knowledge base index", "",
             f"{len(recs)} records. Reviewed {sum(1 for _, r in recs if r['review_status'] == 'reviewed')}, "
             f"draft {sum(1 for _, r in recs if r['review_status'] == 'draft')}.", "",
             "By tier: " + ", ".join(f"{t} {n}" for t, n in sorted(tiers.items())) + ".", "",
             "| Record | Year | Title | Type | Tier | n | Conf | Status |", "|---|---|---|---|---|---|---|---|"]
    for stem, r in sorted(recs, key=lambda x: (-x[1]["year"], x[1]["title"])):
        lines.append(f"| `{stem}` | {r['year']} | [{r['title']}]({r['source_url']}) | {r['study_type']} | {r['source_tier']} | "
                     f"{r.get('n_jgct_patients') if r.get('n_jgct_patients') is not None else ''} | {r['confidence']} | {r['review_status']} |")
    (KB / "INDEX.md").write_text("\n".join(lines) + "\n")


def write_alterations(recs):
    by_gene = defaultdict(list)
    for stem, r in recs:
        for a in r.get("alterations") or []:
            by_gene[a["gene"].upper()].append((a, stem, r))
    lines = ["# Reported alterations in JGCT", "",
             "Aggregated from every record. Draft records are included and marked. Frequencies are as stated by each source.", "",
             "| Gene | Alteration | Frequency | Source | Tier | Conf | Status |", "|---|---|---|---|---|---|---|"]
    for gene in sorted(by_gene):
        for a, stem, r in by_gene[gene]:
            lines.append(f"| {gene} | {a['alteration']} | {a.get('frequency') or ''} | {src(stem, r)} | {r['source_tier']} | {r['confidence']} | {r['review_status']} |")
    (KB / "ALTERATIONS.md").write_text("\n".join(lines) + "\n")


def write_treatments(recs):
    rows = []
    for stem, r in recs:
        for t in r.get("treatments") or []:
            rows.append((t, stem, r))
    lines = ["# Reported treatments and outcomes in JGCT", "",
             "Every treatment any record describes, with the reported setting, patient count and outcome. "
             "This is a list of what the literature reports, not a recommendation.", "",
             "| Regimen | Setting | n | Outcome | Source | Tier | Conf | Status |", "|---|---|---|---|---|---|---|---|"]
    for t, stem, r in sorted(rows, key=lambda x: (x[0]["regimen"].lower(), -x[2]["year"])):
        lines.append(f"| {t['regimen']} | {t.get('setting') or ''} | {t.get('n') if t.get('n') is not None else ''} | "
                     f"{t.get('outcome') or ''} | {src(stem, r)} | {r['source_tier']} | {r['confidence']} | {r['review_status']} |")
    (KB / "TREATMENTS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    recs = load()
    write_index(recs)
    write_alterations(recs)
    write_treatments(recs)
    print(f"built INDEX.md, ALTERATIONS.md, TREATMENTS.md from {len(recs)} records")
