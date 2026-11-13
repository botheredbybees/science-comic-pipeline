#!/usr/bin/env python3
"""Validate a storyboard YAML file against the schema and the accuracy-ledger rules.

Errors stop a storyboard from being rendered. Warnings are things a reviewer must
look at before publishing. Exit code: 0 clean, 1 errors (or warnings with --strict).
There is no limit on the number of beats or panels.

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
NUMBER = re.compile(r"\d+(?:\.\d+)?")
PLAIN_NUMBER = re.compile(r"(?<![A-Za-z0-9.])\d+(?:\.\d+)?")  # skips formulas and labels such as O2 and L0
WORDS = {"one": "1", "single": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
         "seven": "7", "eight": "8", "nine": "9", "ten": "10"}


def _supported_numbers(text):
    """Numbers a cited claim supports: its digits, its number words, and rounded forms of its decimals."""
    out = set(NUMBER.findall(text))
    out |= {WORDS[w] for w in re.findall(r"[a-z]+", text.lower()) if w in WORDS}
    for n in list(out):
        if "." in n:
            out |= {str(round(float(n))), f"{float(n):.1f}"}
    return out


def load_schema():
    return json.loads(SCHEMA_PATH.read_text())


def _dupes(ids):
    seen, dupes = set(), []
    for i in ids:
        if i in seen:
            dupes.append(i)
        seen.add(i)
    return dupes


def _staging_texts(staging):
    """Every string and number a renderer would draw as text from a staging block."""
    out = []
    for prop in (staging or {}).get("props", []):
        for key in ("label", "title", "unit", "x_label", "y_label"):
            if key in prop:
                out.append(str(prop[key]))
        out += [c["label"] for c in prop.get("cards", [])]
        for it in prop.get("items", []):
            out += [it.get("label", ""), it.get("caption", "")]
            if prop.get("show_values"):
                out.append(str(it.get("value", "")))
        out += [n["label"] for n in prop.get("notes", [])]
        if prop.get("kind") == "bars" and "max" in prop and prop.get("show_values", True) and prop.get("show_max", True) \
                and not (prop.get("unit") == "%" and prop["max"] == 100):
            out.append(str(prop["max"]))
        if prop.get("kind") == "bars" and prop.get("min", 0) < 0 and prop.get("show_values", True) and prop.get("show_max", True):
            out.append(str(prop["min"]))
        for b in prop.get("bars", []):
            out += [b.get("label", ""), str(b["value"])] if prop.get("show_values", True) else [b.get("label", "")]
        if "staging" in prop:
            out += _staging_texts(prop["staging"])
    return out


# Words in a `scene` that name a prop the renderer can draw. If the scene says it and the staging lacks it, the alt text
# describes something the reader cannot see.
SCENE_OBJECTS = {"ship": "ship", "bowl": "bowl", "bottle": "bottle", "jar": "jar", "desk": "desk", "phone": "phone",
                 "slide": "slide", "pie": "pie", "board": "board"}


def _prop_kinds(staging):
    kinds = set()
    for prop in (staging or {}).get("props", []):
        kinds.add(prop["kind"])
        kinds |= _prop_kinds(prop.get("staging"))
    return kinds


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
    panels = [p for beat in doc["beats"] for p in beat["panels"]]

    for kind, ids in (
        ("cast", [c["id"] for c in doc["cast"]]),
        ("claim", [c["id"] for c in doc["claims"]]),
        ("beat", [b["id"] for b in doc["beats"]]),
        ("panel", [p["id"] for p in panels]),
    ):
        for d in _dupes(ids):
            errors.append(f"duplicate {kind} id: {d}")

    for beat in doc["beats"]:
        for p in beat["panels"]:
            if not p["id"].startswith(beat["id"] + "."):
                errors.append(f"{p['id']}: panel id does not belong to beat {beat['id']}")
    if panels and "transition" in panels[0]:
        errors.append(f"{panels[0]['id']}: the first panel has a transition but nothing before it")

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
        text = " ".join([line["text"] for line in p.get("speech", [])] + _staging_texts(p.get("staging")))
        if HAS_NUMBER.search(text) and not cited:
            errors.append(f"{p['id']}: text or chart values contain a number but the panel cites no claim")
        if cited:  # a number drawn on the panel should come from one of its cited claims, not from the artist
            allowed = set()
            for cid in cited:
                if cid in claims:
                    allowed |= _supported_numbers(claims[cid]["text"] + " " + claims[cid]["source"].get("quote", ""))
            invented = sorted(set(PLAIN_NUMBER.findall(text)) - allowed)
            if invented:
                warnings.append(f"{p['id']}: number(s) {', '.join(invented)} appear on the panel but in none of its cited claims")
        staged = {c["id"] for c in p.get("staging", {}).get("characters", [])}
        for c in staged - cast_ids - {"extra"}:
            errors.append(f"{p['id']}: staged character '{c}' is not in the cast")
        if "staging" in p:
            for line in p.get("speech", []):
                if line.get("kind", "say") != "caption" and line["speaker"] not in staged:
                    warnings.append(f"{p['id']}: {line['speaker']} speaks but is not in the staging, so no speech line can point at them")
        if "humour" in p and not p["humour"].get("keeps_claims_intact"):
            warnings.append(f"{p['id']}: joke on a panel that cites {', '.join(cited) if cited else 'no claim'}; "
                            "a reviewer must confirm it keeps the claims intact")
        drawn = _prop_kinds(p.get("staging"))
        for word, kind in SCENE_OBJECTS.items():
            if re.search(rf"\b{word}s?\b", p.get("scene", ""), re.I) and kind not in drawn:
                warnings.append(f"{p['id']}: the scene (the alt text) mentions a {word} but no {kind} prop is staged")

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
