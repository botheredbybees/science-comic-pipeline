#!/usr/bin/env python3
"""Make a review sheet for the newest drawing assets: a PDF with each one drawn large, and a checklist to tick while you look.

    python scripts/review_sheet.py --pdf output/new-assets-review.pdf --md docs/new-assets-checklist.md

Both come from one table (ITEMS below), so a panel's id in the PDF (A1b) is the id in the checklist. Each item is drawn in a few variants
(its options on and off), large enough to judge, and each has the things to look for. Add a new asset by adding a row. The older
`scripts/asset_gallery.py` shows every asset small, side by side; this one is for deciding whether a new asset is good enough to use.
"""
import argparse
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "renderers" / "xkcd"))


def big(kind, **opts):
    """A staging with one prop filling the scene."""
    return {"props": [{"kind": kind, "x": 0.04, "y": 0.04, "w": 0.92, "h": 0.9, **opts}]}


def with_chars(st, *chars):
    return {**st, "characters": list(chars)}


def fig(x=0.5, y=0.9, scale=0.8, **kw):
    return {"id": "extra", "x": x, "y": y, "scale": scale, **kw}


def puppet(x, y=0.66, **kw):
    return {"id": "extra", "body": "puppet", "x": x, "y": y, "scale": 0.7, **kw}


TWO = [{"label": "art"}, {"label": "health"}]
HALF_A = {"characters": [{"id": "extra", "x": 0.3, "face": "smile"}]}
HALF_B = {"characters": [{"id": "extra", "x": 0.75, "face": "worry"}], "props": [{"kind": "cloud", "x": 0.55, "y": 0.0, "w": 0.4, "h": 0.4, "faded": True}]}

# (group title, [ (id, asset, [(variant label, staging)], [what to look for]) ])
ITEMS = [
    ("Built 2026-11-16 (this session)", [
        ("A1", "stage", [("plain", big("stage")), ("spotlight, audience, two puppets", with_chars(big("stage", spotlight=True, audience=True), puppet(0.5), puppet(0.66, facing="left", face="smile"))),
                         ("screen and a figure", with_chars(big("stage", screen=True), fig(0.5, 0.8, pose="point")))],
         ["The curtains read as curtains, not as grey wedges.", "With the spotlight, the cone of light is clear against the dark back.", "The audience heads read as heads and do not hide the boards.",
          "A figure or puppet stands on the boards, not in the air or below them."]),
        ("A2", "blackbox", [("labelled", big("blackbox", items=[{"label": "input"}, {"label": "output"}])), ("dashed output", big("blackbox", dashed=True, items=[{"label": "drama"}, {"label": "?"}]))],
         ["The question mark is legible white on black.", "Labels sit clear of the arrows.", "The dashed arrow reads as 'effect not shown'."]),
        ("A3", "circle", [("fire, 7 chairs", big("circle", centre="fire", chairs=7)), ("easel, 5 chairs", big("circle", centre="easel", chairs=5)),
                          ("person, 8 chairs", big("circle", centre="person", chairs=8)), ("no centre", with_chars(big("circle"), fig(0.5, 0.62, 0.45, pose="sit")))],
         ["The chairs read as chairs.", "The far chairs sit behind the near ones.", "Each centre is recognisable.", "A figure can sit or stand in the middle without clashing."]),
        ("A4", "hospitalroom", [("plain", big("hospitalroom")), ("drip and a worried figure", with_chars(big("hospitalroom", drip=True), fig(0.4, 0.9, 0.8, face="worry")))],
         ["The bed reads as a hospital bed, the table as a bedside table.", "The drip stand reads as a drip.", "A standing figure is a sensible size next to the bed."]),
        ("A5", "bridge", [("joined, labelled", big("bridge", items=TWO)), ("broken", big("bridge", broken=True, items=TWO))],
         ["The joined bridge reads as a bridge (deck, arch).", "The broken one reads as a missing link, not as two unrelated blocks.", "Labels fit inside the blocks."]),
        ("A6", "eye", [("plain", big("eye")), ("lens", big("eye", lens=True)), ("thought bubble", big("eye", thought="what is that?"))],
         ["The eye reads as an eye (iris, pupil, glint, lashes).", "The lens reads as a lens, with the eye still visible through it.", "The thought bubble text is readable and sits clear of the eye."]),
        ("A7", "bookshelf", [("plain", big("bookshelf")), ("one book missing", big("bookshelf", gap=True)), ("missing and lit", big("bookshelf", gap=True, lit=True))],
         ["The shelf reads as a bookcase.", "The gap is noticed at once and has a question mark.", "The rays help rather than clutter."]),
        ("A8", "spinalcord", [("plain", big("spinalcord")), ("laminae", big("spinalcord", laminae=True)), ("hemisection", big("spinalcord", hemisection=True))],
         ["The grey butterfly is recognisable as a cord section.", "The dashed laminae are visible (they were faint in the small gallery).", "The hemisection reads as one damaged side.",
          "It is a schematic: a caption must carry any anatomical claim."]),
        ("A9", "'missing' options", [("gallery, one frame empty", big("gallery", frames=3, empty=1)), ("book, blank cover", big("book", blank=True)), ("brain, a signal route", big("brain", signal=True))],
         ["Dashed outline plus a question mark means 'missing' in all three (same idiom as bookshelf gap).", "The brain's arrow reads as a route, with a direction."]),
        ("A10", "puppet (a body)", [("five faces", {"characters": [{"id": "extra", "body": "puppet", "x": 0.12 + 0.19 * i, "face": f, "scale": 0.9} for i, f in enumerate(["neutral", "smile", "worry", "deadpan", "surprised"])]}),
                                    ("facing left, with a speech line", {"characters": [{"id": "extra", "body": "puppet", "x": 0.6, "facing": "left", "face": "smile", "scale": 1.1}]})],
         ["It reads as a puppet, not a robot.", "No hand is drawn; the stick and grip read as held up from below.", "The faces differ enough to use.", "Facing left mirrors correctly."]),
        ("A11", "split screen", [("side", {"split": [HALF_A, HALF_B], "split_labels": ["before", "after"], "split_direction": "side"}),
                                 ("stack", {"split": [HALF_A, HALF_B], "split_labels": ["before", "after"], "split_direction": "stack"}),
                                 ("slope", {"split": [HALF_A, HALF_B], "split_labels": ["before", "after"], "split_direction": "slope"})],
         ["Each half reads as its own view.", "Labels sit clear of the figures.", "In the slope, each half's figures stay in their wedge (the divider cuts anything that crosses).",
          "The slope feels like tension; if it only looks tilted, drop it."]),
    ]),
    ("Built earlier this week", [
        ("B1", "staff", [("default", big("staff")), ("3/4, pitches", big("staff", meter="3/4", pitches=[1, 3, 5]))],
         ["It reads as a bar of music, with the time signature.", "The pitches rise as the list does."]),
        ("B2", "livingroom", [("plain", big("livingroom")), ("lamp, armchair, figure", with_chars({"props": [{"kind": "livingroom", "x": 0.04, "y": 0.04, "w": 0.92, "h": 0.9, "lamp": True}, {"kind": "armchair", "x": 0.4, "y": 0.4, "w": 0.2, "h": 0.5}]}, fig(0.75, 0.9, 0.7)))],
         ["It reads as a living room.", "An armchair and a figure sit on the floor line, not floating."]),
        ("B3", "gears", [("labelled", big("gears", items=[{"label": "speech"}, {"label": "song"}]))], ["The gears mesh and the labels fit inside the hubs."]),
        ("B4", "ear", [("default", big("ear"))], ["It reads as an ear, with sound arriving from the left."]),
        ("B5", "funnel", [("labelled", big("funnel", items=[{"label": "all studies"}, {"label": "kept"}]))], ["Many in, few out; the labels do not touch the funnel."]),
        ("B6", "brain options", [("frontal", big("brain", highlight="frontal")), ("temporal", big("brain", highlight="temporal")), ("tracts", big("brain", tracts=True))],
         ["The shaded lobe is where a reader would expect it.", "The tracts read as fibre bundles, not scribbles."]),
    ]),
]


def variants():
    for _, items in ITEMS:
        for iid, asset, vs, checks in items:
            for k, (label, st) in enumerate(vs):
                yield f"{iid}{chr(97 + k)}", asset, label, st


def build_doc():
    import asset_gallery as G
    doc = G.build()
    panels = []
    for n, (pid, asset, label, st) in enumerate(variants(), 1):
        cap = f"[{pid}] {asset}: {label}"
        panels.append({"id": f"B1.{n}", "weight": "standard", "height": "tall", "frame": "outlined", "scene": cap,
                       "speech": [{"speaker": "narrator", "kind": "caption", "text": cap}], "staging": st})
    doc["beats"] = [{"id": "B1", "title": "New assets, to review", "act": "method", "panels": panels}]
    doc["meta"]["title"] = "New assets review sheet"
    return doc


def checklist():
    out = ["# New assets: review checklist", "",
           "Generated by `scripts/review_sheet.py`; the panel ids (A1b) are the ids in `output/new-assets-review.pdf`. Regenerate both with:", "",
           "```", "python scripts/review_sheet.py --pdf output/new-assets-review.pdf --md docs/new-assets-checklist.md", "```", "",
           "For each asset: look at its panels in the PDF, tick what holds, then choose a verdict. **Keep** means usable as it is, **fix** means usable after the change you note, **drop** means not worth the room.", ""]
    for title, items in ITEMS:
        out += [f"## {title}", ""]
        for iid, asset, vs, checks in items:
            ids = ", ".join(f"{iid}{chr(97 + k)} ({label})" for k, (label, _) in enumerate(vs))
            out += [f"### {iid} `{asset}`", "", f"Panels: {ids}", ""] + [f"- [ ] {c}" for c in checks]
            out += ["", "Verdict: [ ] keep  [ ] fix  [ ] drop", "", "Notes: ", ""]
    return "\n".join(out)


def main(argv=None):
    from export_pdf import export
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pdf", default="output/new-assets-review.pdf")
    ap.add_argument("--md", default="docs/new-assets-checklist.md")
    args = ap.parse_args(argv)
    doc = build_doc()
    Path(args.pdf).parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        sb = Path(tmp) / "review.yaml"
        sb.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=200))
        export(str(sb), args.pdf)
    Path(args.md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.md).write_text(checklist())
    print(f"wrote {args.pdf} and {args.md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
