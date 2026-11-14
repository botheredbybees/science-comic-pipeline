#!/usr/bin/env python3
"""Draw a catalogue of every body and prop the xkcd renderer has, as a PDF, so you can see what is available.

    python scripts/asset_gallery.py -o output/asset-gallery.pdf

Each panel is a row of labelled items. The animals and apparatus are generic cartoon shapes, not accurate or to
scale; the labels are the names to use in a storyboard (`body: seal`, `kind: massspec`).
"""
import argparse
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_pdf import export  # noqa: E402

# (name, label, scale or props fields). Bodies are `extra` characters; the first has no body (a plain stick figure).
BODIES = [
    [("stick", 1.0), ("diatom", 1.0), ("krill", 1.4), ("penguin", 1.0), ("whale", 0.42)],
    [("salp", 0.72), ("copepod", 0.95), ("fish", 0.9), ("worm", 0.75), ("jellyfish", 0.9)],
    [("urchin", 1.0), ("seastar", 1.0), ("seal", 0.78), ("seabird", 0.95), ("moss", 1.0)],
    [("bacterium", 1.2), ("dinoflagellate", 1.0), ("squid", 0.7), ("amphipod", 0.85)],
]
HELD = [("marker", "marker (pen)"), ("mug", "mug"), ("teacup", "teacup"), ("clipboard", "clipboard"), ("flask", "flask"), ("magnifier", "magnifier")]
# Cast looks: every hair style, each hair tone, glasses and the lab coat, as cast members with appearance options.
LOOKS = [
    [("hair_none", "no hair", {"hair": "none"}), ("hair_bob", "bob", {"hair": "bob"}), ("hair_long", "long", {"hair": "long"}),
     ("hair_ponytail", "ponytail", {"hair": "ponytail"}), ("hair_bun", "bun", {"hair": "bun"}), ("hair_spiky", "spiky", {"hair": "spiky"}),
     ("hair_beanie", "beanie", {"hair": "beanie"})],
    [("tone_light_bob", "light bob", {"hair": "bob", "hair_tone": "light"}), ("tone_light_long", "light long", {"hair": "long", "hair_tone": "light"}),
     ("tone_strands_ponytail", "strand ponytail", {"hair": "ponytail", "hair_tone": "strands"}), ("tone_strands_long", "strand long", {"hair": "long", "hair_tone": "strands"}),
     ("glasses", "glasses", {"hair": "bob", "glasses": True}), ("coat", "lab coat", {"hair": "bun", "coat": True}),
     ("coat_glasses", "coat + glasses", {"hair": "ponytail", "glasses": True, "coat": True})],
    [("hardhat", "hard hat", {"hair": "hardhat"}), ("floatcoat", "float coat", {"hair": "bob", "outfit": "floatcoat"}),
     ("parka", "parka", {"hair": "none", "outfit": "parka"}), ("hivis", "hi-vis vest", {"hair": "none", "outfit": "hivis"}),
     ("hivis_hardhat", "hi-vis + hard hat", {"hair": "hardhat", "outfit": "hivis"}), ("parka_glasses", "parka + glasses", {"hair": "bob", "glasses": True, "outfit": "parka"}),
     ("floatcoat_beanie", "float coat + beanie", {"hair": "beanie", "outfit": "floatcoat"})],
]
PROPS = [
    ("Analysis steps", [("sequence", {"label": "marker gene"}), ("tree", {"items": [{"label": "a"}, {"label": "b"}, {"label": "c"}, {"label": "d"}]}),
                        ("clusters", {"items": [{}, {}, {}]}), ("network", {}), ("database", {}),
                        ("venn", {"items": [{"label": "one"}, {"label": "two"}], "label": "both"})]),
    ("Data and models", [("scatter", {"x_label": "x", "y_label": "y"}), ("boxplot", {"items": [{"label": "a"}, {"label": "b"}, {"label": "c"}]}),
                         ("modelgrid", {}), ("tubes", {}), ("filter", {}), ("sequencer", {})]),
    ("Charts and diagrams: data bars, pie and plot", [("bars", {"bars": [{"label": "a", "value": 3}, {"label": "b", "value": 5}, {"label": "c", "value": 2}], "show_values": False, "show_max": False}),
                                                    ("pie", {"items": [{"label": "a", "value": 1}, {"label": "b", "value": 2}, {"label": "c", "value": 1}]}),
                                                    ("plot", {"series": [{"points": [[0, 0.2], [0.4, 0.6], [1, 0.85]], "style": "dashed"}], "x_label": "x", "y_label": "y"}),
                                                    ("stack", {"items": [{"label": "a", "value": 1}, {"label": "b", "value": 2}, {"label": "c", "value": 1}]})]),
    ("Charts and diagrams: axis, flow and steps", [("axis", {"items": [{"label": "a", "at": 0.15}, {"label": "b", "at": 0.5}, {"label": "c", "at": 0.85}]}),
                                                  ("flow", {"items": [{"label": "one"}, {"label": "two"}, {"label": "three"}]}),
                                                  ("steps", {"items": [{"label": "low"}, {"label": "mid"}, {"label": "high"}]})]),
    ("Maps: the south polar cap and the wider southern hemisphere", [("map", {}),
                                                                      ("map", {"view": "wide"})]),
    ("Major currents laid over each map", [("map", {"_over": {"kind": "currents"}}), ("map", {"view": "wide", "_over": {"kind": "currents", "view": "wide"}})]),
    ("Polar field gear and a molecule", [("stake", {}), ("emsled", {}), ("fieldcamp", {}), ("molecule", {})]),
    ("An iceberg and an ice shelf", [("iceberg", {}), ("iceshelf", {})]),
    ("Sea ice conditions, seen from above", [("seaice", {"condition": "pancake", "label": "pancake"}), ("seaice", {"condition": "pack", "label": "pack"}),
                                              ("seaice", {"condition": "drift", "label": "drift"}), ("seaice", {"condition": "fast", "label": "fast ice"})]),
    ("The upper ocean: wind, the mixed layer, the thermocline", [("mixedlayer", {"items": [{"label": "mixed layer"}, {"label": "thermocline"}, {"label": "deep water"}]})]),
    ("Sampling at sea", [("ctd", {}), ("net", {}), ("bottle", {}), ("jar", {}), ("cpr", {})]),
    ("Towed nets", [("bongo", {}), ("trawl", {}), ("rmt", {})]),
    ("The ship, after the RSV Nuyina, and its echosounder", [("ship", {}), ("echosounder", {})]),
    ("Remote sensing and ice", [("satellite", {}), ("radar", {}), ("radarscreen", {}), ("icecore", {}), ("massspec", {}), ("helicopter", {})]),
    ("Lab and field", [("aquarium", {}), ("freezer", {}), ("tag", {}), ("drone", {}), ("microscope", {}), ("laptop", {}), ("thermometer", {})]),
    ("Everyday props", [("desk", {}), ("bowl", {}), ("board", {"cards": [{"label": "A"}, {"label": "B"}, {"label": "C"}]}), ("paper", {"label": "paper"}), ("box", {"label": "text box"})]),
    ("More everyday props", [("box", {"label": "box"}), ("teapot", {}), ("cups", {"items": [{"label": "a", "value": 1}, {"label": "b", "value": 2}]}), ("flash", {"label": "flash"})]),
    ("Pictures, labels and arrows", [("picture", {"staging": {"props": [{"kind": "bottle", "x": 0.3, "y": 0.1, "w": 0.4, "h": 0.8}]}}), ("label", {"label": "label"}), ("arrow", {"x2": 0.95, "y2": 0.3})]),
]


def build():
    beats = []
    n = 0
    for title, groups, kind in (("Bodies", BODIES, "body"), ):
        panels = []
        for row in groups:
            n += 1
            chars, props = [], []
            for i, (name, scale) in enumerate(row):
                x = 0.1 + i * (0.8 / 4)
                c = {"id": "extra", "x": round(x, 3), "y": 0.8, "scale": scale}
                if name != "stick":
                    c["body"] = name
                chars.append(c)
                props.append({"kind": "label", "x": round(x, 3), "y": 0.86, "label": name})
            panels.append({"id": f"B1.{n}", "weight": "full", "height": "short", "frame": "outlined", "transition": "scene-to-scene" if n > 1 else None,
                           "scene": "A row of the renderer's animal and cell bodies, each labelled with the name to use.",
                           "speech": [{"speaker": "narrator", "kind": "caption", "text": "Bodies: set `body` on a cast member or on an extra."}] if n == 1 else [],
                           "staging": {"characters": chars, "props": props}})
        beats.append({"id": "B1", "title": "Bodies", "act": "method", "panels": panels})
    hp = []
    for n, row in enumerate((HELD[:3], HELD[3:]), 1):
        chars, props = [], []
        for i, (name, label) in enumerate(row):
            x = round(0.14 + i * (0.72 / (len(row) - 1)), 3)
            chars.append({"id": "extra", "x": x, "y": 0.8, "pose": "hold", "holding": name})
            props.append({"kind": "label", "x": x, "y": 0.86, "label": label})
        hp.append({"id": f"B3.{n}", "weight": "full", "height": "short", "frame": "outlined", "transition": "scene-to-scene",
                   "scene": "Stick figures each holding one of the objects a character can hold.",
                   "speech": [{"speaker": "narrator", "kind": "caption", "text": "Held objects: set `holding` on a staged character."}] if n == 1 else [],
                   "staging": {"characters": chars, "props": props}})
    beats.append({"id": "B3", "title": "Held objects", "act": "method", "panels": hp})
    cast = [{"id": "guide", "name": "Guide", "role": "Not used", "look": "none"}]
    lp = []
    for n, row in enumerate(LOOKS, 1):
        chars, props = [], []
        for i, (cid, label, app) in enumerate(row):
            cast.append({"id": cid, "name": label, "role": "A look in the gallery", "look": label, "appearance": app})
            x = round(0.09 + i * (0.82 / (len(row) - 1)), 3)
            chars.append({"id": cid, "x": x, "y": 0.8, "face": "smile"})
            props.append({"kind": "label", "x": x, "y": 0.86, "label": label})
        lp.append({"id": f"B4.{n}", "weight": "full", "height": "short", "frame": "outlined", "transition": "scene-to-scene",
                   "scene": "A row of cast looks: hair styles and hats, hair tones, glasses, a lab coat and work clothing.",
                   "speech": [{"speaker": "narrator", "kind": "caption", "text": "Looks: set `appearance` on a cast member in head.yaml."}] if n == 1 else [],
                   "staging": {"characters": chars, "props": props}})
    beats.append({"id": "B4", "title": "Looks", "act": "method", "panels": lp})
    def comp_panel(n, weight, caption, chars, props=None):
        return {"id": f"B5.{n}", "weight": weight, "height": "tall", "frame": "outlined", "transition": "scene-to-scene",
                "scene": caption, "speech": [{"speaker": "narrator", "kind": "caption", "text": caption}],
                "staging": {"characters": chars, "props": props or []}}

    beats.append({"id": "B5", "title": "Composition: scale, cropping and layering", "act": "method", "panels": [
        comp_panel(1, "wide", "A large animal shown larger, its tail cropped by the edge.",
                   [{"id": "extra", "body": "whale", "x": 0.2, "y": 0.9, "scale": 1.6}, {"id": "extra", "body": "krill", "x": 0.85, "y": 0.55, "scale": 0.9, "facing": "left"}]),
        comp_panel(2, "wide", "The other way: a krill much larger than the diatoms.",
                   [{"id": "extra", "body": "krill", "x": 0.35, "y": 0.92, "scale": 2.6}, {"id": "extra", "body": "diatom", "x": 0.8, "y": 0.9, "scale": 0.45},
                    {"id": "extra", "body": "diatom", "x": 0.92, "y": 0.62, "scale": 0.4}]),
        comp_panel(3, "wide", "A character placed in a prop: krill in the aquarium.",
                   [{"id": "extra", "body": "krill", "x": 0.4, "y": 0.62, "scale": 1.5}, {"id": "extra", "body": "krill", "x": 0.64, "y": 0.74, "scale": 1.2, "facing": "left"}],
                   [{"kind": "aquarium", "x": 0.12, "y": 0.1, "w": 0.76, "h": 0.8}]),
        comp_panel(4, "wide", "A close-up: the krill cropped by the panel's edge.",
                   [{"id": "extra", "body": "krill", "x": 0.2, "y": 1.55, "scale": 6.0}])]})
    panels = []
    for n, (title, row) in enumerate(PROPS, 1):
        props = []
        for i, (kind, extra) in enumerate(row):
            w = 0.82 / len(row)
            extra = dict(extra)  # build() may run more than once: never change the shared table
            over = extra.pop("_over", None)
            p = {"kind": kind, "x": round(0.06 + i * (0.88 / len(row)), 3), "y": 0.06, "w": round(w, 3), "h": 0.7}
            p.update(extra)
            props.append(p)
            if over:  # a second prop laid over the first in the same box (currents on a map)
                q = dict(p)
                q.update(over)
                q.pop("places", None)
                props.append(q)
            props.append({"kind": "label", "x": round(0.06 + i * (0.88 / len(row)) + w / 2, 3), "y": 0.86, "label": kind})
        panels.append({"id": f"B2.{n}", "weight": "full", "height": "short", "frame": "outlined", "transition": "scene-to-scene" if n > 1 else "scene-to-scene",
                       "scene": f"{title}: a row of labelled props.", "speech": [{"speaker": "narrator", "kind": "caption", "text": f"{title}."}],
                       "staging": {"props": props}})
    beats.append({"id": "B2", "title": "Props", "act": "method", "panels": panels})
    for b in beats:
        for p in b["panels"]:
            if p.get("transition") is None:
                p.pop("transition", None)
    return {"version": 2,
            "meta": {"title": "Asset gallery", "gallery": True,
                     "source": {"title": "science-comic-pipeline asset gallery", "authors": ["science-comic-pipeline"], "year": 2026,
                                "url": "https://github.com/botheredbybees/science-comic-pipeline", "licence": "MIT"},
                     "spine": {"and": "The renderer draws bodies and props.", "but": "Which exist?", "therefore": "This gallery lists them."}},
            "cast": cast,
            "claims": [], "beats": beats}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("-o", "--out", default="output/asset-gallery.pdf")
    args = ap.parse_args(argv)
    doc = build()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        sb = Path(tmp) / "gallery.yaml"
        sb.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=200))
        export(str(sb), args.out)
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
