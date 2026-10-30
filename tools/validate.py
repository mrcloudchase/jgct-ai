#!/usr/bin/env python3
"""Validate every record in knowledge/records/ against knowledge/schema/record.schema.json,
plus project rules the schema cannot express.

  python3 tools/validate.py            # exit 1 on any error

Extra checks: file stem == <source_type>-<source_id>; reviewed records name a reviewer;
conflicts_with targets exist and link back; overlaps_with targets exist and link back;
tumor_site key present; full_text_source equals pmcid when it is a PMC ID; ledger item for
the record is 'processed' (pmid:<n> / doi:<doi> items only).
"""
import glob, json, os, sqlite3, sys
import yaml, jsonschema

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def load_all():
    recs = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "knowledge/records/*.yaml"))):
        recs[os.path.basename(f)[:-5]] = yaml.safe_load(open(f))
    return recs


def main():
    schema = json.load(open(os.path.join(ROOT, "knowledge/schema/record.schema.json")))
    v = jsonschema.Draft202012Validator(schema)
    recs = load_all(); errs = []
    dbp = os.path.join(ROOT, "state/ledger.sqlite")
    led = sqlite3.connect(dbp) if os.path.exists(dbp) else None
    for stem, r in recs.items():
        for e in v.iter_errors(r):
            errs.append(f"{stem}: {'/'.join(map(str, e.path))}: {e.message}")
        if not isinstance(r, dict):
            continue
        exp = f"{r.get('source_type')}-{str(r.get('source_id')).replace('/', '_')}"
        if exp != stem:
            errs.append(f"{stem}: file stem should be {exp}")
        if "tumor_site" not in r:
            errs.append(f"{stem}: tumor_site missing (CLAUDE.md: set it on every record; null if not stated)")
        if r.get("review_status") == "reviewed" and not r.get("reviewed_by"):
            errs.append(f"{stem}: reviewed without reviewed_by")
        fts = r.get("full_text_source") or ""
        if fts.startswith("PMC") and r.get("pmcid") not in (None, fts):
            errs.append(f"{stem}: full_text_source {fts} differs from pmcid {r.get('pmcid')}")
        lid = {"pmid": "pmid:", "doi": "doi:"}.get(r.get("source_type"))
        if lid and led is not None:
            row = led.execute("SELECT status FROM items WHERE id=?", (lid + str(r.get("source_id")).lower() if lid == "doi:" else lid + str(r.get("source_id")),)).fetchone()
            if row and row[0] != "processed":
                errs.append(f"{stem}: ledger status is {row[0]}, expected processed")
        for key in ("conflicts_with", "overlaps_with"):
            for o in r.get(key) or []:
                if o not in recs:
                    errs.append(f"{stem}: {key} target {o} missing")
                elif stem not in (recs[o].get(key) or []):
                    errs.append(f"{stem}: {key} {o} not reciprocated")
    for e in errs:
        print("ERROR", e)
    print(f"{len(recs)} records, {len(errs)} errors")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
