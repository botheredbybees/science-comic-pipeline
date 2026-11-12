#!/usr/bin/env python3
"""Validate a storyboard YAML file against the schema and the accuracy-ledger rules.

Errors stop a storyboard from being rendered. Warnings are things a reviewer must
look at before publishing. Exit code: 0 clean, 1 errors (or warnings with --strict).

    python scripts/validate_storyboard.py examples/akam-2026-cartooning/storyboard.yaml
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "storyboard.schema.json"
HAS_NUMBER = re.compile(r"\d")


def load_schema():
    return json.loads(SCHEMA_PATH.read_text())


def _dupes(ids):
    seen, dupes = set(), []
    for i in ids:
        if i in seen:
            dupes.append(i)
        seen.add(i)
    return dupes


def validate(doc):
    """Return (errors, warnings) for a parsed storyboard."""
    errors, warnings = [], []

    validator = Draft202012Validator(load_schema())
    for e in sorted(validator.iter_errors(doc), key=lambda e: list(e.absolute_path)):
        where = "/".join(str(p) for p in e.absolute_path) or "(root)"
        errors.append(f"schema: {where}: {e.message}")
    if errors:  # later checks assume the shape is right
        return errors, warnings

    cast_ids = {c["id"] for c in doc["cast"]}
    claims = {c["id"]: c for c in doc["claims"]}
    panels = [p for page in doc["pages"] for p in page["panels"]]

    for kind, ids in (
        ("cast", [c["id"] for c in doc["cast"]]),
        ("claim", [c["id"] for c in doc["claims"]]),
        ("page", [p["id"] for p in doc["pages"]]),
        ("panel", [p["id"] for p in panels]),
    ):
        for d in _dupes(ids):
            errors.append(f"duplicate {kind} id: {d}")

    used = set()
    for p in panels:
        for line in p.get("speech", []):
            if line["speaker"] != "narrator" and line["speaker"] not in cast_ids:
                errors.append(f"{p['id']}: speaker '{line['speaker']}' is not in the cast")
        cited = p.get("claim_ids", [])
        for cid in cited:
            if cid not in claims:
                errors.append(f"{p['id']}: cites unknown claim {cid}")
            else:
                used.add(cid)
        text = " ".join(line["text"] for line in p.get("speech", []))
        if HAS_NUMBER.search(text) and not cited:
            errors.append(f"{p['id']}: dialogue contains a number but the panel cites no claim")
        if "humour" in p and cited and not p["humour"].get("keeps_claims_intact"):
            warnings.append(f"{p['id']}: joke on a panel that cites {', '.join(cited)}; a reviewer must confirm it keeps the claims intact")

    for cid in sorted(used):
        c = claims[cid]
        if c["status"] != "verified":
            msg = f"{cid} is {c['status']} but is drawn in a panel"
            if c.get("note"):
                msg += f" ({c['note']})"
            warnings.append(msg)
    for cid in sorted(set(claims) - used):
        warnings.append(f"{cid} is in the ledger but no panel uses it")

    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("storyboard")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    args = ap.parse_args(argv)

    doc = yaml.safe_load(Path(args.storyboard).read_text())
    errors, warnings = validate(doc)
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
