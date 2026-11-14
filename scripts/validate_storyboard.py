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


THOUSANDS = re.compile(r"(?<=\d),\s?(?=\d{3}(?!\d))")


def _norm(text):
    """Join thousands separators ("55,465" and the PDF's "55, 465") so a chart value 55465 matches either."""
    return THOUSANDS.sub("", text)


def _supported_numbers(text):
    """Numbers a cited claim supports: its digits, its number words, and rounded forms of its decimals."""
    text = _norm(text)
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


# The footer of every comic already says the pictures are simple cartoons, stand-ins and not to scale, so a label that says
# it again on a panel is noise, and a panel whose only words are that label is a filler.
BOILERPLATE = re.compile(r"\b(?:schematics?|stand-?ins?|not to scale)\b", re.I)


def _boilerplate_only(text):
    """True if nothing is left of a label once the boilerplate words, brackets and joining words are removed."""
    rest = BOILERPLATE.sub("", text)
    return not re.sub(r"\b(?:are|is|a|an|the|of)\b|[\s,;:().\-]", "", rest, flags=re.I)


def _real_words(panel):
    """The words a reader gets from a panel: its caption and speech lines, and any label that says more than 'schematic'."""
    texts = [l["text"] for l in panel.get("speech", [])]
    texts += [t for t in _staging_texts(panel.get("staging")) if t.strip() and not _boilerplate_only(t)]
    return [t for t in texts if re.search(r"[A-Za-z]", t)]


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
SCENE_OBJECTS = {"ship": "ship", "bowl": "bowl", "bottle": "bottle", "jar": "jar", "desk": "desk", "pie": "pie", "board": "board", "teapot": "teapot", "laptop": "laptop",
                 "microscope": "microscope", "thermometer": "thermometer", "sequencer": "sequencer",
                 "database": "database", "echosounder": "echosounder", "helicopter": "helicopter", "drone": "drone",
                 "aquarium": "aquarium", "freezer": "freezer", "satellite": "satellite", "rosette": "ctd", "bongo": "bongo",
                 "iceberg": "iceberg", "map": "map"}
# Objects a character holds rather than a prop; the scene may name one only if someone in the staging holds it.
SCENE_HELD = ("mug", "teacup", "clipboard", "flask", "magnifier")


def _prop_kinds(staging):
    kinds = set()
    for prop in (staging or {}).get("props", []):
        kinds.add(prop["kind"])
        kinds |= _prop_kinds(prop.get("staging"))
    return kinds


def _held(staging):
    return {c["holding"] for c in (staging or {}).get("characters", []) if c.get("holding")}


FIGURE_ONLY_LIMIT = 0.25  # more than this share of panels with no picture of the subject is a defect
MIN_PANELS_FOR_SHARE = 8


def _figure_only(panel, cast_bodies):
    """True if the panel draws nothing but stick figures: no prop and no animal or diatom (or nothing staged at all)."""
    staging = panel.get("staging") or {}
    if staging.get("props"):
        return False
    for c in staging.get("characters", []):
        if (c.get("body") or cast_bodies.get(c["id"], "stick")) != "stick":
            return False
    return True


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

    meta = doc.get("meta", {})
    if meta.get("sources"):  # a topic comic: every claim says which paper it comes from
        ids = [x["id"] for x in meta["sources"]]
        for d in _dupes(ids):
            errors.append(f"duplicate source id: {d}")
        if meta.get("source"):
            errors.append("meta has both `source` and `sources`; use `sources` for a comic drawn from several papers")
        for c in doc["claims"]:
            ref = c["source"].get("ref")
            if not ref:
                errors.append(f"{c['id']}: this comic has several sources, so the claim's source needs a `ref` naming one of {ids}")
            elif ref not in ids:
                errors.append(f"{c['id']}: source ref '{ref}' is not in meta.sources {ids}")
    else:
        for c in doc["claims"]:
            if c["source"].get("ref"):
                errors.append(f"{c['id']}: `ref` is only for comics with meta.sources")
    panels = [p for beat in doc["beats"] for p in beat["panels"]]

    for c in doc["cast"]:  # a combination that reads badly
        app = c.get("appearance") or {}
        if app.get("outfit") and app.get("coat"):
            warnings.append(f"cast {c['id']}: both `coat` (the lab coat) and `outfit` are set; only the outfit is drawn")
        if app.get("hair") == "bun" and app.get("hair_tone") == "strands":
            warnings.append(f"cast {c['id']}: strand hair on a bun reads as a mess; use the default or light tone for a bun")

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
                extra = " (a speaking walk-on needs a cast entry; the staged `extra` cannot speak)" if line["speaker"] == "extra" else ""
                errors.append(f"{p['id']}: speaker '{line['speaker']}' is not in the cast{extra}")
        cited = p.get("claim_ids", [])
        for cid in cited:
            if cid not in claims:
                errors.append(f"{p['id']}: cites unknown claim {cid}")
            else:
                used.add(cid)
        text = _norm(" ".join([line["text"] for line in p.get("speech", [])] + _staging_texts(p.get("staging"))))
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
        for t in _staging_texts(p.get("staging")):
            if BOILERPLATE.search(t):
                warnings.append(f"{p['id']}: the label '{t}' repeats what the footer already says (the pictures are cartoon stand-ins, not "
                                "to scale): name the thing, or drop the label")
        if not _real_words(p) and "humour" not in p:  # a silent beat that is a joke is the one wordless panel a person approves
            warnings.append(f"{p['id']}: the panel has no caption, speech or label of its own; a panel that says nothing is a filler, "
                            "so give it a line the claims support or cut it (a deliberate silent joke carries a `humour` note instead)")
        for prop in (p.get("staging") or {}).get("props", []):
            if prop.get("kind") == "net" and re.search(r"\bCPR\b|plankton recorder", prop.get("label", ""), re.I):
                warnings.append(f"{p['id']}: a plankton net is labelled '{prop['label']}'; a continuous plankton recorder is not a net, use the `cpr` prop")
        drawn = _prop_kinds(p.get("staging"))
        scene = p.get("scene", "")
        for word, kind in SCENE_OBJECTS.items():
            # "jar water" names a sample, "microscope work" a topic: neither is an object to draw
            if re.search(rf"\b{word}s?\b(?!\s+(?:water|work))", scene, re.I) and kind not in drawn:
                warnings.append(f"{p['id']}: the scene (the alt text) mentions a {word} but no {kind} prop is staged")
        held = _held(p.get("staging"))
        for word in SCENE_HELD:
            if re.search(rf"\b{word}s?\b(?!\s+(?:water|work))", scene, re.I) and word not in held and word not in drawn:
                warnings.append(f"{p['id']}: the scene (the alt text) mentions a {word} but nobody in the staging holds one")
        for prop in (p.get("staging") or {}).get("props", []):
            if prop["kind"] == "board":
                cards = prop.get("cards", [])
                longest = max((len(c["label"]) for c in cards), default=0)
                if longest > 20 or (len(cards) > 3 and longest > 10):
                    warnings.append(f"{p['id']}: a board with long labels (or more than three medium ones) shrinks its text "
                                    "until it overlaps or is unreadable; use `box` props for sentences")

    cast_bodies = {c["id"]: (c.get("appearance") or {}).get("body", "stick") for c in doc["cast"]}
    bare = [p["id"] for p in panels if _figure_only(p, cast_bodies)]
    if len(panels) >= MIN_PANELS_FOR_SHARE and len(bare) > FIGURE_ONLY_LIMIT * len(panels):
        warnings.append(f"{len(bare)} of {len(panels)} panels ({100 * len(bare) // len(panels)}%) show only stick figures, no prop, chart, "
                        f"apparatus or animal ({', '.join(bare[:8])}{' ...' if len(bare) > 8 else ''}); characters are the voice, "
                        "not the picture: draw what each claim is about, or fold the claim into a neighbouring panel that has a picture")

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


def variety(doc):
    """McCloud-style variety of a comic: return (stats, warnings). Transitions and word-picture labels are notes about the
    reading, but they are how a comic's rhythm is planned, so a comic that is nearly all scene-to-scene with no moments, no
    silent pictures and no plain-English glosses is a defect of variety. Applies from 20 panels."""
    panels = [p for b in doc["beats"] for p in b["panels"]]
    n = len(panels)
    trans = {}
    for p in panels:
        if p.get("transition"):
            trans[p["transition"]] = trans.get(p["transition"], 0) + 1
    labelled = sum(trans.values())
    # only a panel that says something counts: a wordless picture is a filler, not a moment
    moments = sum(1 for p in panels if p.get("transition") in ("moment-to-moment", "aspect-to-aspect") and _real_words(p))
    no_wp = sum(1 for p in panels if not p.get("word_picture"))
    picture = sum(1 for p in panels if p.get("word_picture") == "picture-specific")
    devices = {}
    for p in panels:
        if p.get("device"):
            devices[p["device"]] = devices.get(p["device"], 0) + 1
    stats = {"panels": n, "scene_pct": round(100 * trans.get("scene-to-scene", 0) / max(labelled, 1)), "moment_pct": round(100 * moments / max(n, 1)),
             "no_word_picture_pct": round(100 * no_wp / max(n, 1)), "picture_specific": picture, "devices": devices}
    warnings = []
    if n >= 20:
        if labelled and stats["scene_pct"] > 50:
            warnings.append(f"variety: {stats['scene_pct']}% of the transitions are scene-to-scene; most panels continue the same scene, so label "
                            "them by what actually changes (same subject a moment later, a bigger action, a new subject in the same place)")
        if moments < 0.05 * n:
            warnings.append(f"variety: only {moments} of {n} panels are moment-to-moment or aspect-to-aspect; if the paper describes an instant or an action, "
                            "show it (the flash, the net closing) with a caption or a line; do not add empty frames to meet a number")
        if no_wp > 0.25 * n:
            warnings.append(f"variety: {no_wp} of {n} panels have no word_picture label; say how words and picture relate in each one")
        if n >= 30 and picture < 3:
            warnings.append(f"variety: {picture} picture-specific panel(s); let the picture carry a few panels with little or no caption")
        if not devices.get("gloss"):
            warnings.append("variety: no panel is marked device: gloss; have a character restate a technical term in plain English "
                            "(on a definition claim) at least once")
        if n >= 30 and not devices.get("moment"):
            warnings.append("variety: no panel is marked device: moment; show the instant itself at least once (the flash, the net closing)")
    for p in panels:
        if p.get("device") == "gloss":
            if not p.get("claim_ids"):
                warnings.append(f"{p['id']}: a gloss restates a term the paper defines, so it must cite the definition claim")
            if not any(l.get("kind", "say") != "caption" and l["speaker"] != "narrator" for l in p.get("speech", [])):
                warnings.append(f"{p['id']}: a gloss is a character's line, but this panel has none")
    return stats, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("storyboard")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--variety", action="store_true", help="also check the comic's McCloud variety (transitions, moments, glosses); see skills/storyboard")
    args = ap.parse_args(argv)

    doc = yaml.safe_load(Path(args.storyboard).read_text())
    errors, warnings = validate(doc)
    if args.variety and not errors:
        stats, vwarn = variety(doc)
        warnings += vwarn
        print(f"variety: {stats['scene_pct']}% scene-to-scene, {stats['moment_pct']}% moments, {stats['no_word_picture_pct']}% unlabelled word-picture, "
              f"{stats['picture_specific']} picture-specific, devices {stats['devices'] or 'none'}")
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
