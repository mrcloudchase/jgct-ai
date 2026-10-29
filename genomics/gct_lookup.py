#!/usr/bin/env python3
"""Find every granulosa cell tumor sample in public cBioPortal studies and annotate JGCT genes against CIViC.

No API key needed. Writes genomics/REPORT.md.

Method:
  1. List all public cBioPortal studies.
  2. Filter samples whose CANCER_TYPE_DETAILED is Granulosa Cell Tumor or Sex Cord Stromal Tumor.
  3. Pull mutations in a panel of JGCT-relevant genes for those samples.
  4. Flag FOXL2 p.C134W carriers as adult-type; everything else is "possible juvenile-type", which is
     only a hint, since many panels and studies do not record histologic subtype.
  5. Pull patient age where the study records it.
  6. Query CIViC for evidence filed under granulosa cell tumor and for each panel gene.

This generates hypotheses for a conversation with an oncologist. It is not a treatment recommendation.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
CBIO = "https://www.cbioportal.org/api"
CIVIC = "https://civicdb.org/api/graphql"
HEADERS = {"User-Agent": "jgct-ai genomics (https://github.com/mrcloudchase/jgct-ai)", "Content-Type": "application/json"}

# Entrez IDs for genes reported in JGCT or used to separate adult-type tumors.
PANEL = {
    "FOXL2": 668, "AKT1": 207, "DICER1": 23405, "KMT2C": 58508, "KMT2D": 8085, "GNAS": 2778,
    "TERT": 7015, "IDH1": 3417, "TGFBR1": 7046, "ARID1A": 8289, "SMARCA4": 6597, "FGFR1": 2260,
    "TP53": 7157, "CTNNB1": 1499, "PIK3CA": 5290,
}
CANCER_TYPES = ["Granulosa Cell Tumor", "Sex Cord Stromal Tumor"]
NORMAL_SAMPLE = re.compile(r"-N\d+-")
AGE_ATTRS = ["AGE", "AGE_AT_DX", "AGE_AT_DIAGNOSIS", "AGE_AT_SEQ_REPORT", "AGE_AT_SEQ_REPORTED_YEARS"]


def get(path: str, **params):
    r = requests.get(f"{CBIO}{path}", params=params, headers=HEADERS, timeout=120)
    r.raise_for_status()
    return r.json()


def post(path: str, body, **params):
    r = requests.post(f"{CBIO}{path}", params=params, data=json.dumps(body), headers=HEADERS, timeout=300)
    r.raise_for_status()
    return r.json()


def civic(query: str) -> dict:
    r = requests.post(CIVIC, data=json.dumps({"query": query}), headers=HEADERS, timeout=120)
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def find_samples() -> list[dict]:
    studies = [s["studyId"] for s in get("/studies", projection="SUMMARY", pageSize=10000)]
    print(f"{len(studies)} public studies", file=sys.stderr)
    body = {"studyIds": studies,
            "clinicalDataFilters": [{"attributeId": "CANCER_TYPE_DETAILED", "values": [{"value": v} for v in CANCER_TYPES]}]}
    samples = post("/filtered-samples/fetch", body)
    samples.sort(key=lambda x: x["studyId"], reverse=True)
    # Recover the exact subtype label for each sample.
    ids = [{"entityId": s["sampleId"], "studyId": s["studyId"]} for s in samples]
    labels = {}
    if ids:
        for row in post("/clinical-data/fetch", {"attributeIds": ["CANCER_TYPE_DETAILED"], "identifiers": ids},
                        clinicalDataType="SAMPLE", projection="SUMMARY"):
            labels[(row["studyId"], row["sampleId"])] = row["value"]
    out, seen = [], set()
    for s in samples:
        # Skip matched-normal samples (e.g. MSK clonal hematopoiesis blood samples, IDs like P-0000118-N01-IM3).
        if NORMAL_SAMPLE.search(s["sampleId"]):
            continue
        # The same MSK sample appears in several overlapping releases; keep one copy.
        if s["sampleId"] in seen:
            continue
        seen.add(s["sampleId"])
        s["subtype"] = labels.get((s["studyId"], s["sampleId"]), "")
        out.append(s)
    return out


def patient_ages(samples: list[dict]) -> dict[tuple[str, str], str]:
    ids = [{"entityId": s["patientId"], "studyId": s["studyId"]} for s in samples]
    ages = {}
    if not ids:
        return ages
    for row in post("/clinical-data/fetch", {"attributeIds": AGE_ATTRS, "identifiers": ids},
                    clinicalDataType="PATIENT", projection="SUMMARY"):
        ages.setdefault((row["studyId"], row["patientId"]), row["value"])
    return ages


def mutations(samples: list[dict]) -> dict[tuple[str, str], list[dict]]:
    by_study = defaultdict(list)
    for s in samples:
        by_study[s["studyId"]].append(s["sampleId"])
    found = defaultdict(list)
    for study, sample_ids in by_study.items():
        profiles = get(f"/studies/{study}/molecular-profiles")
        mut = next((p["molecularProfileId"] for p in profiles if p["molecularAlterationType"] == "MUTATION_EXTENDED"), None)
        if not mut:
            continue
        rows = post(f"/molecular-profiles/{mut}/mutations/fetch",
                    {"sampleIds": sample_ids, "entrezGeneIds": list(PANEL.values())}, projection="DETAILED")
        for m in rows:
            found[(study, m["sampleId"])].append({
                "gene": m["gene"]["hugoGeneSymbol"], "change": m.get("proteinChange") or m.get("mutationType", ""),
                "type": m.get("mutationType", ""),
            })
    return found


def civic_evidence() -> tuple[list[dict], dict[str, dict]]:
    q = """{ evidenceItems(diseaseName: "Granulosa Cell Tumor", first: 50) { totalCount nodes {
              id evidenceType evidenceLevel significance evidenceDirection
              molecularProfile { name } disease { name } therapies { name } source { citation } } } }"""
    disease = civic(q)["evidenceItems"]["nodes"]
    genes = {}
    for sym in PANEL:
        g = civic(f'{{ gene(entrezSymbol: "{sym}") {{ id name link }} }}')["gene"]
        if not g:
            continue
        mps = None
        for n_var, n_ev in ((60, 10), (25, 5)):
            try:
                variants = civic(f'{{ gene(entrezSymbol: "{sym}") {{ variants(first: {n_var}) {{ nodes {{ name link singleVariantMolecularProfile {{ name evidenceItems(first: {n_ev}) {{ nodes {{ evidenceType evidenceLevel significance disease {{ name }} therapies {{ name }} }} }} }} }} }} }} }}')["gene"]["variants"]["nodes"]
                mps = [v["singleVariantMolecularProfile"] for v in variants if v.get("singleVariantMolecularProfile")]
                break
            except (requests.HTTPError, RuntimeError) as e:
                print(f"warning: CIViC query for {sym} failed at {n_var}/{n_ev}: {e}", file=sys.stderr)
        if mps is None:
            continue
        predictive = []
        for mp in mps:
            for ev in mp["evidenceItems"]["nodes"]:
                if ev["evidenceType"] == "PREDICTIVE" and ev["therapies"]:
                    predictive.append({"profile": mp["name"], "level": ev["evidenceLevel"], "significance": ev["significance"],
                                       "disease": ev["disease"]["name"] if ev["disease"] else "", "therapies": [t["name"] for t in ev["therapies"]]})
        genes[sym] = {"link": g["link"], "n_profiles": len(mps), "predictive": predictive}
    return disease, genes


def main() -> None:
    samples = find_samples()
    print(f"{len(samples)} granulosa / sex cord-stromal samples", file=sys.stderr)
    ages = patient_ages(samples)
    muts = mutations(samples)
    disease_ev, gene_ev = civic_evidence()

    rows = []
    for s in samples:
        key = (s["studyId"], s["sampleId"])
        ms = muts.get(key, [])
        foxl2 = any(m["gene"] == "FOXL2" and "C134W" in (m["change"] or "") for m in ms)
        rows.append({**s, "age": ages.get((s["studyId"], s["patientId"]), ""), "mutations": ms,
                     "group": "adult-type (FOXL2 C134W)" if foxl2 else "possible juvenile-type or untested"})

    by_study = Counter(r["studyId"] for r in rows)
    by_group = Counter(r["group"] for r in rows)
    gene_counts = Counter(m["gene"] for r in rows if r["group"].startswith("possible") for m in r["mutations"])

    out = [f"# Granulosa cell tumor samples in public cBioPortal data, {date.today().isoformat()}", "",
           "> Hypothesis generation only. Subtype is inferred from the FOXL2 C134W marker when the study does not record it; "
           "FOXL2-negative does not prove juvenile type, and most panels do not detect TERT rearrangements.", "",
           f"Samples found: {len(rows)} across {len(by_study)} studies.", "",
           "| Group | Samples |", "|---|---|"] + [f"| {g} | {n} |" for g, n in by_group.most_common()] + [
           "", "## Studies", "", "| Study | Samples |", "|---|---|"] + [
           f"| [{s}](https://www.cbioportal.org/study/summary?id={s}) | {n} |" for s, n in by_study.most_common()] + [
           "", "## Panel genes mutated in FOXL2-negative samples", "", "| Gene | Samples |", "|---|---|"] + [
           f"| {g} | {n} |" for g, n in gene_counts.most_common()] + [
           "", "## Sample-level detail (FOXL2-negative only)", "",
           "| Study | Sample | Age | Subtype label | Panel mutations |", "|---|---|---|---|---|"]
    for r in rows:
        if r["group"].startswith("possible"):
            ms = "; ".join(f"{m['gene']} {m['change']}" for m in r["mutations"]) or "none in panel"
            out.append(f"| {r['studyId']} | {r['sampleId']} | {r['age']} | {r['subtype']} | {ms} |")

    out += ["", "## CIViC evidence filed under granulosa cell tumor", ""]
    if disease_ev:
        out += ["| Profile | Type | Level | Significance | Therapies | Source |", "|---|---|---|---|---|---|"]
        for e in disease_ev:
            out.append(f"| {e['molecularProfile']['name']} | {e['evidenceType']} | {e['evidenceLevel']} | {e['significance']} | "
                       f"{', '.join(t['name'] for t in e['therapies']) or ''} | {e['source']['citation'] if e['source'] else ''} |")
    else:
        out.append("None.")

    out += ["", "## CIViC predictive evidence for panel genes (any cancer type)", "",
            "Therapies with evidence against these genes somewhere in oncology. Evidence in another tumor type does not transfer "
            "to JGCT without clinical judgment.", ""]
    for sym, g in gene_ev.items():
        if not g["predictive"]:
            continue
        out.append(f"### [{sym}](https://civicdb.org{g['link']})")
        out.append("| Profile | Level | Significance | Disease | Therapies |")
        out.append("|---|---|---|---|---|")
        seen = set()
        for p in sorted(g["predictive"], key=lambda p: p["level"]):
            k = (p["profile"], p["disease"], tuple(p["therapies"]))
            if k in seen:
                continue
            seen.add(k)
            out.append(f"| {p['profile']} | {p['level']} | {p['significance']} | {p['disease']} | {', '.join(p['therapies'])} |")
        out.append("")

    (HERE / "REPORT.md").write_text("\n".join(out) + "\n")
    (HERE / "samples.json").write_text(json.dumps(rows, indent=1) + "\n")
    print(f"wrote {HERE / 'REPORT.md'} and samples.json", file=sys.stderr)


if __name__ == "__main__":
    main()
