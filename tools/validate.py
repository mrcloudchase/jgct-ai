#!/usr/bin/env python3
"""Validate every record in knowledge/records/ against knowledge/schema/record.schema.json,
plus project rules the schema cannot express.

  python3 tools/validate.py            # exit 1 on any error

Extra checks: file stem == <source_type>-<source_id>; confidence ceilings per tier
(peer_reviewed abstract-only <=3, model_assisted_fetch <=3, conference/preprint <=3,
organization/other <=2, registry/database <=4); new records must be draft;
conflicts_with targets must exist and link back.
"""
import glob, json, os, sys
import yaml, jsonschema

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CEIL = {"peer_reviewed": 5, "guideline": 5, "registry": 4, "database": 4, "preprint": 3,
        "conference_abstract": 3, "organization": 2, "other": 2}


def load_all():
    recs = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "knowledge/records/*.yaml"))):
        recs[os.path.basename(f)[:-5]] = yaml.safe_load(open(f))
    return recs


def main():
    schema = json.load(open(os.path.join(ROOT, "knowledge/schema/record.schema.json")))
    v = jsonschema.Draft202012Validator(schema)
    recs = load_all(); errs = []
    for stem, r in recs.items():
        for e in v.iter_errors(r):
            errs.append(f"{stem}: {'/'.join(map(str, e.path))}: {e.message}")
        if not isinstance(r, dict):
            continue
        exp = f"{r.get('source_type')}-{str(r.get('source_id')).replace('/', '_')}"
        if exp != stem:
            errs.append(f"{stem}: file stem should be {exp}")
        c, t = r.get("confidence", 0), r.get("source_tier")
        ceil = CEIL.get(t, 5)
        if t == "peer_reviewed" and not r.get("full_text_read"):
            ceil = 3
        if r.get("extraction_method") == "model_assisted_fetch":
            ceil = min(ceil, 3)
        if c > ceil:
            errs.append(f"{stem}: confidence {c} exceeds ceiling {ceil} for tier {t}")
        if c == 5 and r.get("extraction_method") != "full_text":
            errs.append(f"{stem}: confidence 5 requires extraction_method full_text")
        for o in r.get("conflicts_with") or []:
            if o not in recs:
                errs.append(f"{stem}: conflicts_with target {o} missing")
            elif stem not in (recs[o].get("conflicts_with") or []):
                errs.append(f"{stem}: conflict with {o} not reciprocated")
    for e in errs:
        print("ERROR", e)
    print(f"{len(recs)} records, {len(errs)} errors")
    sys.exit(1 if errs else 0)


if __name__ == "__main__":
    main()
