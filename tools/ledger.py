#!/usr/bin/env python3
"""Read and update state/ledger.json and state/backlog.json.

  python3 tools/ledger.py status
  python3 tools/ledger.py add <source_type> <source_id> <url> [--tier T] [--priority N] [--needs-index-approval] [--note TEXT]
  python3 tools/ledger.py next [--limit N]          # highest-priority pending items, newest first within a priority
  python3 tools/ledger.py triage                    # batch-fetch PubMed titles and publication types; set priorities
  python3 tools/ledger.py start <source_id>
  python3 tools/ledger.py done <source_id> --record knowledge/records/<file>.yaml
  python3 tools/ledger.py unreachable <source_id> --reason TEXT
  python3 tools/ledger.py skip <source_id> --reason TEXT   # not about JGCT, duplicate, etc.

Ledger statuses: pending, in_progress, done, unreachable, skipped. Backlog holds only pending and in_progress items.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "state" / "ledger.json"
BACKLOG = ROOT / "state" / "backlog.json"
PRIORITY_DEFAULT = {"peer_reviewed": 2, "guideline": 1, "registry": 2, "database": 3, "preprint": 3,
                    "conference_abstract": 3, "organization": 5, "other": 5}


def load(p: Path) -> dict:
    return json.loads(p.read_text()) if p.exists() else {"items": {}}


def save(p: Path, d: dict) -> None:
    p.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")


PRIORITY_1_TITLE = re.compile(r"genom|sequenc|mutation|methylat|molecular|cohort|series|registry|outcome|survival|"
                              r"prognos|classification|guideline|consensus|management|multicent|retrospective|"
                              r"\b\d{2,3} (cases|patients|tumou?rs)\b", re.I)


def triage(items: dict) -> int:
    """Fetch title, year and publication types for every PubMed item lacking a title, then set priority."""
    import requests
    pmids = [k for k, v in items.items() if v["source_type"] == "pmid" and not v.get("title")]
    for i in range(0, len(pmids), 200):
        chunk = pmids[i:i + 200]
        r = requests.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", timeout=120,
                         params={"db": "pubmed", "id": ",".join(chunk), "retmode": "json"})
        r.raise_for_status()
        res = r.json().get("result", {})
        for pmid in chunk:
            d = res.get(pmid)
            if not d or "title" not in d:
                continue
            it = items[pmid]
            it["title"] = d.get("title", "")
            it["year"] = (d.get("pubdate") or "")[:4]
            it["pubtypes"] = d.get("pubtype", [])
            pt = " ".join(it["pubtypes"]).lower()
            if "case reports" in pt and not PRIORITY_1_TITLE.search(it["title"]):
                it["priority"] = 4
            elif "review" in pt or "guideline" in pt or "practice guideline" in pt or PRIORITY_1_TITLE.search(it["title"]):
                it["priority"] = 1
            else:
                it["priority"] = 2
    return len(pmids)


def sync_backlog(ledger: dict) -> None:
    bl = {k: v for k, v in ledger["items"].items() if v["status"] in ("pending", "in_progress")}
    save(BACKLOG, {"items": bl, "count": len(bl)})


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("triage")
    a = sub.add_parser("add")
    a.add_argument("source_type", choices=["pmid", "doi", "abstract", "url"])
    a.add_argument("source_id")
    a.add_argument("url")
    a.add_argument("--tier", default="other")
    a.add_argument("--priority", type=int)
    a.add_argument("--needs-index-approval", action="store_true")
    a.add_argument("--note", default="")
    n = sub.add_parser("next")
    n.add_argument("--limit", type=int, default=20)
    for cmd in ("start", "done", "unreachable", "skip"):
        s = sub.add_parser(cmd)
        s.add_argument("source_id")
        s.add_argument("--record")
        s.add_argument("--reason", default="")
    args = ap.parse_args()

    ledger = load(LEDGER)
    items = ledger["items"]
    today = date.today().isoformat()

    if args.cmd == "status":
        counts = {}
        for v in items.values():
            counts[v["status"]] = counts.get(v["status"], 0) + 1
        approvals = sum(1 for v in items.values() if v.get("needs_index_approval") and v["status"] == "pending")
        print(json.dumps({"total": len(items), **counts, "needs_index_approval": approvals}, indent=1))
        return
    if args.cmd == "add":
        if args.source_id in items:
            print(f"already in ledger with status {items[args.source_id]['status']}")
            return
        items[args.source_id] = {
            "source_type": args.source_type, "url": args.url, "tier": args.tier,
            "priority": args.priority if args.priority is not None else PRIORITY_DEFAULT.get(args.tier, 5),
            "status": "pending", "added_on": today, "needs_index_approval": args.needs_index_approval, "note": args.note,
        }
    elif args.cmd == "triage":
        n = triage(items)
        save(LEDGER, ledger)
        sync_backlog(ledger)
        prio = {}
        for v in items.values():
            if v["status"] == "pending":
                prio[v["priority"]] = prio.get(v["priority"], 0) + 1
        print(f"triaged {n} items; pending by priority: {json.dumps(prio, sort_keys=True)}")
        return
    elif args.cmd == "next":
        pend = [(k, v) for k, v in items.items() if v["status"] == "pending" and not v.get("needs_index_approval")]
        pend.sort(key=lambda kv: (kv[1]["priority"], -int(kv[1].get("year") or 0), kv[1]["added_on"]))
        print("priority\ttype\tid\tyear\ttier\ttitle\turl")
        for k, v in pend[: args.limit]:
            print(f"{v['priority']}\t{v['source_type']}\t{k}\t{v.get('year', '')}\t{v['tier']}\t{(v.get('title') or '')[:100]}\t{v['url']}")
        return
    else:
        it = items.get(args.source_id)
        if it is None:
            raise SystemExit(f"{args.source_id} not in ledger; add it first")
        it["status"] = {"start": "in_progress", "done": "done", "unreachable": "unreachable", "skip": "skipped"}[args.cmd]
        it["updated_on"] = today
        if args.record:
            it["record"] = args.record
        if args.reason:
            it["reason"] = args.reason
    save(LEDGER, ledger)
    sync_backlog(ledger)
    print(f"{args.cmd} {getattr(args, 'source_id', '')}: ok")


if __name__ == "__main__":
    main()
