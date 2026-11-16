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
        ("A5", "bridge", [("joined, labelled", big("bridge", items=TWO)), ("broken", big("bridge", broken=True, items=TWO))],
         ["The joined bridge reads as a bridge (deck, arch).", "The broken one reads as a missing link, not as two unrelated blocks.", "Labels fit inside the blocks."]),
        ("A6", "eye", [("plain", big("eye")), ("lens", big("eye", lens=True)), ("thought bubble", big("eye", thought="what is that?"))],
         ["The eye reads as an eye (iris, pupil, glint, lashes).", "The lens reads as a lens, with the eye still visible through it.", "The thought bubble text is readable and sits clear of the eye."]),
        ("A7", "bookshelf", [("plain", big("bookshelf")), ("books missing", big("bookshelf", gap=True))],
         ["The shelf reads as a bookcase.", "The gap is noticed at once and has a question mark."]),
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

# Round 2 (2026-11-16): only what changed after the first review, with checks taken from the notes.
HALF_A2 = {"characters": [{"id": "extra", "x": 0.5, "y": 0.88, "face": "smile"}]}
HALF_B2 = {"characters": [{"id": "extra", "x": 0.5, "y": 0.88, "face": "worry"}], "props": [{"kind": "cloud", "x": 0.2, "y": 0.0, "w": 0.6, "h": 0.4, "faded": True}]}
ROUND2 = [
    ("Changed after your notes", [
        ("A2", "blackbox", [("labelled", big("blackbox", items=[{"label": "input"}, {"label": "output"}])), ("dashed output", big("blackbox", dashed=True, items=[{"label": "drama"}, {"label": "?"}]))],
         ["The question mark is big enough now."]),
        ("A3", "circle", [("fire, 7 chairs", big("circle", centre="fire", chairs=7)), ("easel, 5 chairs", big("circle", centre="easel", chairs=5)),
                          ("person, 8 chairs", big("circle", centre="person", chairs=8)), ("a figure standing in the middle", with_chars(big("circle"), fig(0.5, 0.66, 0.42)))],
         ["No figure sits without a chair under it (the sitting figure is gone; a figure stands in the middle instead).", "The chairs still read as a circle."]),
        ("A5", "bridge", [("joined, labelled", big("bridge", items=TWO)), ("broken", big("bridge", broken=True, items=TWO))],
         ["The joined bridge (a plain deck, no arch or rail) reads as a bridge between the blocks.", "The broken one still reads as a missing link."]),
        ("A6", "eye", [("plain", big("eye")), ("lens held away", big("eye", lens=True)), ("thought bubble", big("eye", thought="what is that?"))],
         ["The lens reads as a lens, held away from the eye with the view running through it.", "The thought-bubble text is large enough and fits."]),
        ("A7", "bookshelf", [("plain", big("bookshelf")), ("books missing", big("bookshelf", gap=True))],
         ["The wider gap is noticed at once (the rays are gone).", "The break in the row of books triggers the pattern, as you said it would."]),
        ("A9", "brain: side view", [("plain", big("brain")), ("lobes named", big("brain", labels=True)), ("temporal lobe shaded", big("brain", highlight="temporal", labels=True)),
                                    ("fibre tracts", big("brain", tracts=True)), ("a signal route", big("brain", signal=True))],
         ["It reads as a brain at a glance (lobes, the two fissures, folds, cerebellum, stem).", "Each lobe is where an anatomist would expect it.", "The folds give enough detail for the discussions we will illustrate.",
          "The labels are readable and sit clear of the folds.", "What detail is still missing? Say in the notes."]),
        ("A9b", "brain: from above", [("two hemispheres", big("brain", view="top")), ("left shaded, named", big("brain", highlight="left", labels=True)), ("right shaded", big("brain", highlight="right"))],
         ["It reads as a brain from above, with a fissure between two hemispheres.", "Left and right are the right way round for a comparison of the two."]),
        ("A11", "split screen", [("side", {"split": [HALF_A2, HALF_B2], "split_labels": ["before", "after"], "split_direction": "side"}),
                                 ("stack", {"split": [HALF_A2, HALF_B2], "split_labels": ["before", "after"], "split_direction": "stack"}),
                                 ("slope", {"split": [HALF_A2, HALF_B2], "split_labels": ["before", "after"], "split_direction": "slope"})],
         ["In the slope, the first figure now sits inside its wedge (higher and further left).", "Nothing crosses the divider."]),
        ("B2", "livingroom", [("plain", big("livingroom")), ("lamp, armchair, figure", with_chars({"props": [{"kind": "livingroom", "x": 0.04, "y": 0.04, "w": 0.92, "h": 0.9, "lamp": True}, {"kind": "armchair", "x": 0.4, "y": 0.4, "w": 0.2, "h": 0.5}]}, fig(0.75, 0.9, 0.7)))],
         ["The room reads as a room without the rug."]),
        ("B3", "gears", [("labelled", big("gears", items=[{"label": "speech"}, {"label": "song"}]))], ["The labels are larger and still fit inside the hubs."]),
    ]),
]
# Round 3 (2026-11-16): the three assets that were marked fix in round 2, and the one marked keep with a note.
ROUND3 = [
    ("Changed after round 2", [
        ("A2", "blackbox", [("labelled", big("blackbox", items=[{"label": "input"}, {"label": "output"}])), ("dashed output", big("blackbox", dashed=True, items=[{"label": "drama"}, {"label": "?"}]))],
         ["The question mark now fills most of the box and reads across a page."]),
        ("A7", "bookshelf", [("plain", big("bookshelf")), ("books missing", big("bookshelf", gap=True))],
         ["The question mark in the gap is large enough to read at once."]),
        ("A9", "brain: side view", [("plain", big("brain")), ("lobes named", big("brain", labels=True)), ("temporal lobe shaded", big("brain", highlight="temporal", labels=True)),
                                    ("fibre tracts", big("brain", tracts=True)), ("a signal route", big("brain", signal=True))],
         ["The fold squiggles are gone: the only solid lines are the outline, the lateral fissure, the central sulcus and the cerebellum.", "The fibre tracts are dotted with a ring at each end, so they cannot be mistaken for a fissure.",
          "It still reads as a brain at a glance, and the lobe labels are clear.", "What would you add or change? Say in the notes."]),
    ]),
]
ROUNDS = {1: ITEMS, 2: ROUND2, 3: ROUND3}


def variants(items=None):
    for _, group in (items or ITEMS):
        for iid, asset, vs, checks in group:
            for k, (label, st) in enumerate(vs):
                yield f"{iid}{chr(97 + k)}", asset, label, st


def build_doc(items=None):
    import asset_gallery as G
    doc = G.build()
    panels = []
    for n, (pid, asset, label, st) in enumerate(variants(items), 1):
        cap = f"[{pid}] {asset}: {label}"
        panels.append({"id": f"B1.{n}", "weight": "standard", "height": "tall", "frame": "outlined", "scene": cap,
                       "speech": [{"speaker": "narrator", "kind": "caption", "text": cap}], "staging": st})
    doc["beats"] = [{"id": "B1", "title": "New assets, to review", "act": "method", "panels": panels}]
    doc["meta"]["title"] = "New assets review sheet"
    return doc


def form_html(items=None, rnd=1):
    """The review as one self-contained web form (see review_form.py), with each variant drawn as an inline SVG in a 640 by 420 frame."""
    import render as R
    from review_form import build_html, framed_svg
    cast = {c["id"]: c for c in build_doc()["cast"]}
    groups = []
    for title, group in (items or ITEMS):
        out = []
        for iid, asset, vs, checks in group:
            vars_ = []
            for k, (label, st) in enumerate(vs):
                pid = f"{iid}{chr(97 + k)}"
                pen = R.Pen(pid)
                frame = pen.rect(3, 3, 634, 414, 2.8)
                svg, _ = R.stage(pen, 14, 14, 612, 392, st, cast, 22)
                vars_.append({"id": pid, "label": label, "svg": framed_svg(frame + svg, f"{asset}: {label}")})
            out.append({"id": iid, "name": asset, "variants": vars_, "checks": checks})
        groups.append((title, out))
    if rnd == 3:
        return build_html("New assets: review, round 3", "Three assets changed after round 2: the blackbox and bookshelf question marks, and the side-view brain without its fold squiggles. Choose keep, fix or drop for each, then press Submit.", groups, collection="round3")
    if rnd == 2:
        return build_html("New assets: review, round 2", "These are the assets changed after your first review. Each has the drawing as it is now, what to check against your notes, and a verdict: keep, fix or drop. Press Submit when you are done.", groups, collection="round2")
    return build_html("New assets: review", "Look at each asset, tick what holds, and choose keep, fix or drop. Add a note where something needs changing. Answers save as you go.", groups)


def checklist(items=None):
    out = ["# New assets: review checklist", "",
           "Generated by `scripts/review_sheet.py`; the panel ids (A1b) are the ids in `output/new-assets-review.pdf`. Regenerate both with:", "",
           "```", "python scripts/review_sheet.py --pdf output/new-assets-review.pdf --md docs/new-assets-checklist.md", "```", "",
           "For each asset: look at its panels in the PDF, tick what holds, then choose a verdict. **Keep** means usable as it is, **fix** means usable after the change you note, **drop** means not worth the room.", ""]
    for title, group in (items or ITEMS):
        out += [f"## {title}", ""]
        for iid, asset, vs, checks in group:
            ids = ", ".join(f"{iid}{chr(97 + k)} ({label})" for k, (label, _) in enumerate(vs))
            out += [f"### {iid} `{asset}`", "", f"Panels: {ids}", ""] + [f"- [ ] {c}" for c in checks]
            out += ["", "Verdict: [ ] keep  [ ] fix  [ ] drop", "", "Notes: ", ""]
    return "\n".join(out)


def main(argv=None):
    from export_pdf import export
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pdf", default="output/new-assets-review.pdf")
    ap.add_argument("--md", default="docs/new-assets-checklist.md")
    ap.add_argument("--round", type=int, default=1, choices=sorted(ROUNDS), help="which round of the review: 1 is the first set of assets, 2 and 3 only those changed after the round before")
    ap.add_argument("--html", help="also write the review as a web form (publish it as an Artifact with the db capability)")
    args = ap.parse_args(argv)
    items = ROUNDS[args.round]
    doc = build_doc(items)
    Path(args.pdf).parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        sb = Path(tmp) / "review.yaml"
        sb.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=200))
        export(str(sb), args.pdf)
    Path(args.md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.md).write_text(checklist(items))
    if args.html:
        Path(args.html).parent.mkdir(parents=True, exist_ok=True)
        Path(args.html).write_text(form_html(items, args.round))
    print(f"wrote {args.pdf} and {args.md}" + (f" and {args.html}" if args.html else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
