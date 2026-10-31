#!/usr/bin/env python3
"""Patient-level rows on records, and their export for analyses/.

  python3 tools/patients.py merge batch.json      # set `patients` on records from {"<stem>": [ {...}, ... ]}
  python3 tools/patients.py export                # write analyses/data/published-cases.csv from every record with patients
  python3 tools/patients.py stats                 # counts by site, stage, outcome

A batch replaces the whole `patients` list of each record named in it. Each row follows the `patients`
item schema in knowledge/schema/record.schema.json; the merge validates the record and writes nothing
for a record that fails. The export adds the record stem, year, first author, evidence_basis and
overlaps_with to each row so an analysis can drop duplicated patients.
"""
import csv, glob, json, os, sys
import yaml, jsonschema

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
REC = os.path.join(ROOT, "knowledge", "records")
OUT = os.path.join(ROOT, "analyses", "data", "published-cases.csv")
SCHEMA = json.load(open(os.path.join(ROOT, "knowledge", "schema", "record.schema.json")))
FIELDS = list(SCHEMA["properties"]["patients"]["items"]["properties"])
ORDER = list(SCHEMA["properties"])


def load(stem):
    return yaml.safe_load(open(os.path.join(REC, stem + ".yaml")))


def save(stem, r):
    r = {k: r[k] for k in ORDER if k in r} | {k: v for k, v in r.items() if k not in ORDER}
    yaml.safe_dump(r, open(os.path.join(REC, stem + ".yaml"), "w"), sort_keys=False, allow_unicode=True, width=1000)


def merge(path):
    batch = json.load(open(path))
    n = 0
    for stem, rows in batch.items():
        r = load(stem)
        full = [{k: row.get(k) for k in FIELDS if k in row or k in ("id", "site", "outcome")} for row in rows]
        for row, src in zip(full, rows):
            row.setdefault("presentation", src.get("presentation", []))
        r["patients"] = full
        try:
            jsonschema.validate(r, SCHEMA)
        except jsonschema.ValidationError as e:
            print("INVALID", stem, "/".join(map(str, e.path)), e.message[:120]); continue
        save(stem, r); n += len(full)
    print(f"merged {n} patients into {len(batch)} records")


def rows():
    for f in sorted(glob.glob(os.path.join(REC, "*.yaml"))):
        r = yaml.safe_load(open(f))
        for p in r.get("patients") or []:
            yield os.path.basename(f)[:-5], r, p


def export():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["record", "year", "first_author", "evidence_basis", "overlaps_with"] + FIELDS)
        n = 0
        for stem, r, p in rows():
            w.writerow([stem, r["year"], r.get("first_author") or "", r.get("evidence_basis"), ";".join(r.get("overlaps_with") or [])]
                       + [";".join(p[k]) if isinstance(p.get(k), list) else ("" if p.get(k) is None else p[k]) for k in FIELDS])
            n += 1
    print(f"exported {n} patients to {os.path.relpath(OUT, ROOT)}")


def stats():
    from collections import Counter
    c = Counter(); s = Counter(); o = Counter(); n = 0
    for _, _, p in rows():
        n += 1; c[p["site"]] += 1; s[p.get("stage") or "unstated"] += 1; o[p["outcome"]] += 1
    print(n, dict(c)); print(dict(s)); print(dict(o))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "stats"
    {"merge": lambda: merge(sys.argv[2]), "export": export, "stats": stats}[cmd]()
