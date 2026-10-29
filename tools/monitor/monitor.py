#!/usr/bin/env python3
"""Watch PubMed and ClinicalTrials.gov for new JGCT papers and trials.

Usage:
  python monitor/monitor.py                 # update state, write monitor/latest.md
  python monitor/monitor.py --dry-run       # do not write state
  python monitor/monitor.py --backfill 10   # on a fresh state, report the 10 newest instead of seeding silently

Summaries use Claude when ANTHROPIC_API_KEY is set; otherwise the raw abstract is used.
Exit code 0 always; prints NEW_ITEMS=<n> on the last line so a workflow can decide whether to open an issue.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
STATE = HERE / "state.json"
REPORT = HERE / "latest.md"

PUBMED_TERM = (
    '"juvenile granulosa cell tumor"[tiab] OR "juvenile granulosa cell tumour"[tiab] '
    'OR "juvenile granulosa cell tumors"[tiab] OR "juvenile granulosa cell tumours"[tiab]'
)
CTGOV_CONDITIONS = ["granulosa cell tumor", "sex cord-stromal tumor"]
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
CTGOV = "https://clinicaltrials.gov/api/v2/studies"
HEADERS = {"User-Agent": "jgct-ai monitor (https://github.com/mrcloudchase/jgct-ai)"}


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"pubmed": [], "ctgov": []}


def pubmed_ids() -> list[str]:
    r = requests.get(f"{EUTILS}/esearch.fcgi", headers=HEADERS, timeout=60,
                     params={"db": "pubmed", "term": PUBMED_TERM, "retmax": 1000, "retmode": "json"})
    r.raise_for_status()
    return r.json()["esearchresult"]["idlist"]


def pubmed_details(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    r = requests.get(f"{EUTILS}/efetch.fcgi", headers=HEADERS, timeout=120,
                     params={"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"})
    r.raise_for_status()
    out = []
    for art in ET.fromstring(r.text).findall(".//PubmedArticle"):
        pmid = art.findtext(".//PMID")
        a = art.find(".//Article")
        abstract = " ".join((t.text or "") for t in a.findall(".//AbstractText"))
        out.append({
            "id": pmid,
            "title": "".join(a.find("ArticleTitle").itertext()) if a.find("ArticleTitle") is not None else "",
            "journal": a.findtext(".//Journal/Title") or "",
            "year": a.findtext(".//PubDate/Year") or a.findtext(".//PubDate/MedlineDate") or "",
            "abstract": abstract,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return out


def ctgov_studies() -> list[dict]:
    seen, out = set(), []
    for cond in CTGOV_CONDITIONS:
        token = None
        while True:
            params = {"query.cond": cond, "pageSize": 100,
                      "fields": "NCTId,BriefTitle,OverallStatus,StartDate,BriefSummary,Condition,InterventionName"}
            if token:
                params["pageToken"] = token
            r = requests.get(CTGOV, headers=HEADERS, params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            for s in data.get("studies", []):
                p = s["protocolSection"]
                nct = p["identificationModule"]["nctId"]
                if nct in seen:
                    continue
                seen.add(nct)
                out.append({
                    "id": nct,
                    "title": p["identificationModule"].get("briefTitle", ""),
                    "status": p.get("statusModule", {}).get("overallStatus", ""),
                    "start": p.get("statusModule", {}).get("startDateStruct", {}).get("date", ""),
                    "conditions": p.get("conditionsModule", {}).get("conditions", []),
                    "interventions": [i.get("name", "") for i in p.get("armsInterventionsModule", {}).get("interventions", [])],
                    "summary": p.get("descriptionModule", {}).get("briefSummary", ""),
                    "url": f"https://clinicaltrials.gov/study/{nct}",
                })
            token = data.get("nextPageToken")
            if not token:
                break
    return out


def summarize(items: list[dict], kind: str) -> dict[str, str]:
    """Return {id: summary}. Uses Claude if a key is available, else a trimmed abstract."""
    fallback = {i["id"]: (i.get("abstract") or i.get("summary") or "")[:600] for i in items}
    if not items or not os.environ.get("ANTHROPIC_API_KEY"):
        return fallback
    try:
        import anthropic
    except ImportError:
        return fallback
    client = anthropic.Anthropic()
    out = {}
    for it in items:
        text = it.get("abstract") or it.get("summary") or ""
        if not text:
            out[it["id"]] = ""
            continue
        prompt = (
            "You are summarizing for a parent and clinicians tracking juvenile granulosa cell tumor (JGCT) research. "
            f"Below is a {'PubMed abstract' if kind == 'pubmed' else 'clinical trial summary'}. "
            "In three sentences at most, say what was studied, what was found, and whether it bears on JGCT "
            "diagnosis, biology, or treatment. Do not give medical advice. If it is not actually about JGCT or "
            "sex cord-stromal tumors, say so in one sentence.\n\n"
            f"Title: {it['title']}\n\n{text}"
        )
        try:
            resp = client.beta.messages.create(
                model="claude-opus-5-5",
                max_tokens=1024,
                output_config={"effort": "low"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                messages=[{"role": "user", "content": prompt}],
            )
            if resp.stop_reason == "refusal":
                out[it["id"]] = fallback[it["id"]]
                continue
            out[it["id"]] = "".join(b.text for b in resp.content if b.type == "text").strip()
        except anthropic.RateLimitError:
            out[it["id"]] = fallback[it["id"]]
        except anthropic.APIStatusError as e:
            print(f"warning: Claude API error {e.status_code} on {it['id']}", file=sys.stderr)
            out[it["id"]] = fallback[it["id"]]
        except anthropic.APIConnectionError:
            out[it["id"]] = fallback[it["id"]]
    return out


def render(new_pubs: list[dict], new_trials: list[dict], pub_sum: dict, trial_sum: dict) -> str:
    lines = [f"# JGCT monitor report, {date.today().isoformat()}", ""]
    lines.append(f"New papers: {len(new_pubs)}. New or changed trials: {len(new_trials)}.")
    if new_pubs:
        lines += ["", "## New papers", ""]
        for p in new_pubs:
            lines.append(f"### [{p['title']}]({p['url']})")
            lines.append(f"*{p['journal']}, {p['year']}. PMID {p['id']}.*")
            lines.append("")
            lines.append(pub_sum.get(p["id"]) or "_No abstract available._")
            lines.append("")
    if new_trials:
        lines += ["", "## New trials", ""]
        for t in new_trials:
            lines.append(f"### [{t['title']}]({t['url']})")
            lines.append(f"*{t['id']}, status {t['status']}, start {t['start'] or 'n/a'}. "
                         f"Conditions: {', '.join(t['conditions'][:5])}. "
                         f"Interventions: {', '.join(t['interventions'][:5]) or 'n/a'}.*")
            lines.append("")
            lines.append(trial_sum.get(t["id"]) or "")
            lines.append("")
    lines += ["", "---", "_Generated by monitor/monitor.py. Summaries are automated and may be wrong; read the source._"]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--backfill", type=int, default=0,
                    help="on first run, report this many newest items instead of silently seeding")
    args = ap.parse_args()

    state = load_state()
    first_run = not state["pubmed"] and not state["ctgov"]

    all_pmids = pubmed_ids()
    all_trials = ctgov_studies()
    seen_p, seen_t = set(state["pubmed"]), set(state["ctgov"])

    new_pmids = [p for p in all_pmids if p not in seen_p]
    new_trials = [t for t in all_trials if t["id"] not in seen_t]
    if first_run:
        new_pmids = new_pmids[: args.backfill]
        new_trials = new_trials[: args.backfill]

    new_pubs = pubmed_details(new_pmids)
    pub_sum = summarize(new_pubs, "pubmed")
    trial_sum = summarize(new_trials, "ctgov")
    report = render(new_pubs, new_trials, pub_sum, trial_sum)
    REPORT.write_text(report)
    print(report)

    if not args.dry_run:
        state["pubmed"] = sorted(set(all_pmids), key=int, reverse=True)
        state["ctgov"] = sorted({t["id"] for t in all_trials})
        state["last_run"] = date.today().isoformat()
        STATE.write_text(json.dumps(state, indent=1) + "\n")
    print(f"NEW_ITEMS={len(new_pubs) + len(new_trials)}")


if __name__ == "__main__":
    main()
