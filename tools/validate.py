#!/usr/bin/env python3
"""Validate every record in knowledge/records against the schema and the repository rules. Exit 1 on any error."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "knowledge" / "records"
SCHEMA = json.loads((ROOT / "knowledge" / "schema" / "record.schema.json").read_text())

try:
    import jsonschema
except ImportError:
    jsonschema = None


def check_schema(rec: dict) -> list[str]:
    if jsonschema:
        v = jsonschema.Draft202012Validator(SCHEMA)
        return [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}" for e in v.iter_errors(rec)]
    errs = []
    for k in SCHEMA["required"]:
        if k not in rec:
            errs.append(f"missing required field {k}")
    for k in rec:
        if k not in SCHEMA["properties"]:
            errs.append(f"unknown field {k}")
    for k, spec in SCHEMA["properties"].items():
        if k in rec and "enum" in spec and rec[k] not in spec["enum"]:
            errs.append(f"{k}: {rec[k]!r} not in {spec['enum']}")
    return errs


def reviewed_in_main() -> set[str]:
    """Records whose committed version on main is already reviewed. Used to stop a sweep editing them."""
    try:
        out = subprocess.run(["git", "ls-tree", "-r", "--name-only", "origin/main", "knowledge/records"],
                             capture_output=True, text=True, cwd=ROOT, check=True).stdout.split()
    except Exception:
        return set()
    done = set()
    for path in out:
        try:
            blob = subprocess.run(["git", "show", f"origin/main:{path}"], capture_output=True, text=True, cwd=ROOT, check=True).stdout
            if yaml.safe_load(blob).get("review_status") == "reviewed":
                done.add(Path(path).stem)
        except Exception:
            pass
    return done


def main() -> None:
    errors = 0
    stems = set()
    frozen = reviewed_in_main()
    for p in sorted(RECORDS.glob("*.yaml")):
        try:
            rec = yaml.safe_load(p.read_text())
        except yaml.YAMLError as e:
            print(f"{p.name}: YAML error {e}")
            errors += 1
            continue
        stems.add(p.stem)
        errs = check_schema(rec)
        if not re.fullmatch(r"(pmid|doi|abstract|url)-.+", p.stem):
            errs.append("file name must be <source_type>-<source_id>.yaml")
        elif not p.stem.startswith(rec.get("source_type", "") + "-"):
            errs.append("file name prefix does not match source_type")
        if p.stem in frozen:
            cur = subprocess.run(["git", "show", f"origin/main:knowledge/records/{p.name}"], capture_output=True, text=True, cwd=ROOT).stdout
            old = yaml.safe_load(cur) if cur else {}
            changed = {k for k in set(old) | set(rec) if old.get(k) != rec.get(k)} - {"conflicts_with", "superseded_by"}
            if changed:
                errs.append(f"reviewed record changed outside conflicts_with/superseded_by: {sorted(changed)}")
        if rec.get("review_status") == "reviewed" and p.stem not in frozen and not rec.get("reviewed_by"):
            errs.append("review_status reviewed requires reviewed_by")
        for e in errs:
            print(f"{p.name}: {e}")
        errors += len(errs)
    for p in RECORDS.glob("*.yaml"):
        rec = yaml.safe_load(p.read_text()) or {}
        for ref in rec.get("conflicts_with") or []:
            if ref not in stems:
                print(f"{p.name}: conflicts_with references unknown record {ref}")
                errors += 1
    print(f"{len(stems)} records, {errors} errors")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
