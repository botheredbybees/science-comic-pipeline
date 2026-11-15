#!/usr/bin/env python3
"""Suggest graphic elements for a paper from its cards, and rank the assets the renderer is missing across papers.

    python scripts/suggest_graphics.py cards/<slug>/cards.yaml -o graphics/<slug>/graphics.yaml       # one paper, any model
    python scripts/suggest_graphics.py --rollup graphics/*/graphics.yaml -o graphics/SUMMARY.md       # across papers

For each paper a model proposes five to eight pictures a comic could draw (a chart, an apparatus, a setting, a diagram), each tied to
the cards it rests on and to an element the renderer already has (`element.kind`: a prop such as `bars`, `venn`, `armchair`) or to
`new`, a drawing that does not exist yet, with a short name for it. Then every suggestion is checked, and dropped (and listed under
`rejected`, with the reason) if it breaks a rule:
  * its element kind is not one of the renderer's props, nor `new`;
  * it cites no card, or a card that does not exist;
  * a number in its chart values appears in none of the cards it cites (a chart must not invent data).

The rollup counts how often each existing element is suggested and groups the `new` ones that several papers want, so the assets worth
drawing next are the ones a real corpus asks for. Models: see scripts/llm.py and docs/SETUP.md.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

DATA_CHARTS = {"bars", "pie", "stack", "scatter", "boxplot"}  # these draw values, so each needs a number a cited card states

# One line on what each common element is good for, so a model chooses by purpose. Anything in the schema but not here is offered by name.
PURPOSE = {
    "bars": "compare a few amounts (needs numbers from the paper)", "pie": "parts of a whole (needs shares from the paper)",
    "plot": "a trend of one thing against another (only the shape the paper reports)", "axis": "a timeline or a scale with marked points",
    "stack": "a column of segments", "flow": "stages of a process, left to right", "steps": "a ladder of levels or stages",
    "venn": "two groups and what they share", "board": "a row of cards, some hidden: what is missing or unreported",
    "box": "a labelled text callout: a quote, a definition, a list", "label": "a word placed in the picture", "arrow": "a pointer between things",
    "paper": "a form, a questionnaire or a document", "desk": "an office or a study", "laptop": "analysis done on a computer",
    "armchair": "a care home, a waiting room or a listener", "wheelchair": "mobility and access", "piano": "music making", "guitar": "music making",
    "easel": "painting, or a gallery picture", "picture": "a framed picture containing its own scene", "camera": "photography",
    "brain": "the brain or memory", "headphones": "listening, or noise", "notes": "music or song", "clay": "making with clay",
    "mosaic": "making with tiles or fabric", "teapot": "a shared cup of tea, hospitality", "cups": "levels or quantities in cups",
    "microscope": "close examination", "thermometer": "a measured level", "scatter": "a relationship between two measures",
    "boxplot": "a comparison of groups", "map": "where (polar maps only)", "tree": "a family tree or a hierarchy",
    "gallery": "a gallery room or museum wall with framed pictures (options: frames, bench, ramp, easels); a good wide-shot setting",
    "staff": "a bar of music: five lines, a time signature and notes (pitches, meter); for rhythm, melody or a piece of music", "cycle": "a loop of stages that feed back (give 3 to 6 items)", "book": "a book, guide or toolkit (title; heart)", "headprofile": "a head in profile: memory, ageing, a missing scan (question)",
    "cloud": "a fog, a weight or a fading thought (faded)", "scales": "weighing two things against each other (tilt, items)", "door": "a barrier or an entrance (locked, open)",
    "heart": "care or connection, placed between things", "trolley": "an outreach or tea trolley of objects", "van": "mobile outreach: a van with a pop-up table",
    "skyline": "a town or city setting (markers for places)", "network": "connections between many things", "database": "a collection or a reference library", "molecule": "a chemical",
}
NOT_FOR_THIS = {"cpr", "bongo", "trawl", "rmt", "ctd", "echosounder", "radar", "satellite", "icecore", "helicopter", "drone", "emsled", "stake",
                "fieldcamp", "iceberg", "iceshelf", "seaice", "mixedlayer", "currents", "ship", "net", "sequencer", "massspec", "filter", "tubes",
                "freezer", "aquarium", "radarscreen", "modelgrid", "clusters", "sequence"}  # polar and marine apparatus; offered only to papers that need them

PROMPT = """You help a cartoonist plan the pictures for a comic about one paper. Below are the paper's claims ("cards"), each with an id.
Suggest {lo} to {hi} graphic elements the comic could draw. A good suggestion SHOWS the subject (a chart of a reported number, the place, the
object, the process) instead of two people talking.

Return JSON: {{"graphics": [{{"title": "<short name>", "shows": "<one sentence: what the picture depicts>", "claim_ids": ["C1", "C2"],
"element": {{"kind": "<one of the available kinds, or new>", "labels": ["<words printed in the picture>"], "values": [{{"label": "<name>", "value": <a number reported in a cited card>}}]}},
"new_asset": "<only when kind is new: a short noun phrase for the missing drawing, e.g. gallery wall with framed paintings>", "why": "<one sentence>"}}]}}

Rules: cite the card ids each picture rests on. Choose each kind for the purpose listed beside it, not for a loose resemblance. The data
charts (bars, pie, stack, scatter, boxplot) need at least two `values` taken from numbers a cited card states; with no number, draw a diagram
or a picture instead.
Include at least one picture that NO available kind can draw well: give it kind `new` and name the missing drawing, so we learn what to draw next.
Prefer variety across the rest: a chart, a place, an object, a process.
Do not depict an individual person with dementia or any illness as a figure of fun; draw the setting, the activity or the number.

Available kinds:
{kinds}

Cards:
{cards}
"""


def vocabulary():
    """{kind: purpose} for the renderer's props, read from the schema, minus polar and marine apparatus."""
    schema = json.loads((ROOT / "schema" / "storyboard.schema.json").read_text())
    kinds = schema["$defs"]["staging"]["properties"]["props"]["items"]["properties"]["kind"]["enum"]
    return {k: PURPOSE.get(k, "") for k in kinds if k not in NOT_FOR_THIS}


# "one" and "zero" are left out: "one study", "no one", "one of" are not quantities, and checking them would reject honest sentences.
WORDS = {w: str(i) for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
                                          "seventeen eighteen nineteen twenty".split()) if i >= 2}
TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90}


def numbers_in(text):
    """The numbers in a text as strings: digits, and number words (eight, twenty-four) as digits, so a card that writes 'eight' supports 8."""
    t = str(text).lower()
    out = {n.replace(",", "") for n in re.findall(r"\d[\d,]*\.?\d*", t) if n.strip(",.")}
    for m in re.finditer(r"\b(" + "|".join(TENS) + r")(?:[- ](one|two|three|four|five|six|seven|eight|nine))?\b", t):
        out.add(str(TENS[m.group(1)] + (int({"one": 1}.get(m.group(2)) or WORDS.get(m.group(2), 0)) if m.group(2) else 0)))
    out |= {WORDS[w] for w in re.findall(r"\b[a-z]+\b", t) if w in WORDS}
    return out


def parse(text):
    try:
        return json.loads(text)["graphics"]
    except (ValueError, KeyError, TypeError):
        cut = text.rfind("},")
        try:
            return json.loads(text[:cut + 1] + "]}")["graphics"] if cut > 0 else []
        except (ValueError, KeyError, TypeError):
            return []


def validate(graphics, cards, vocab):
    """Split model suggestions into (kept, rejected); a rejection says why."""
    by_id = {c["id"]: c for c in cards}
    kept, rejected = [], []
    for g in graphics:
        why = None
        el = g.get("element") or {}
        kind = el.get("kind")
        ids = g.get("claim_ids") or []
        if kind != "new" and kind not in vocab:
            why = f"element kind {kind!r} is not one of the renderer's props or 'new'"
        elif not ids:
            why = "it cites no card"
        elif any(i not in by_id for i in ids):
            why = "it cites a card that does not exist: " + ", ".join(i for i in ids if i not in by_id)
        elif kind == "new" and not str(g.get("new_asset", "")).strip():
            why = "kind is new but the missing drawing is not named"
        elif kind in DATA_CHARTS and not [v for v in (el.get("values") or []) if numbers_in(v.get("value", ""))]:
            why = f"a {kind} chart draws values, but no number from a cited card is given for it"
        else:
            cited = " ".join(by_id[i]["text"] + " " + by_id[i]["source"]["quote"] for i in ids)
            have = numbers_in(cited)
            for v in el.get("values") or []:
                if numbers_in(v.get("value", "")) and not (numbers_in(v.get("value", "")) <= have):
                    why = f"the chart value {v.get('value')!r} for {v.get('label')!r} appears in none of the cited cards"
                    break
        (rejected if why else kept).append({**g, "rejected_because": why} if why else g)
    return kept, rejected


def suggest(cards, ask_fn, vocab=None, lo=5, hi=8):
    vocab = vocab or vocabulary()
    usable = [c for c in cards if (c.get("model_check") or {}).get("verdict") not in ("overstated", "different", "unclear")]
    kinds = "\n".join(f"- {k}: {v}" if v else f"- {k}" for k, v in vocab.items())
    text = "\n".join(f"{c['id']} [{c['kind']}, p{c['source']['page']}] {c['text']}" for c in usable)
    graphics = parse(ask_fn(PROMPT.format(lo=lo, hi=hi, kinds=kinds, cards=text)))
    kept, rejected = validate(graphics, usable, vocab)
    return kept, rejected


GAP_STOP = set("a an the of with and in on for to by at from or as into two one icon icons symbolic abstract stylized small large diverse framed "
               "showing indicating connecting between representing small large simple".split())


def gap_themes(names):
    """Group requests for missing assets by the content word they share (gallery, hand, diagram ...): [(word, [names])], biggest first.

    Models describe the same missing drawing in different words ("gallery wall with framed paintings", "accessible gallery interior"),
    so exact names hide the pattern. Each request goes to its most common word, and only words shared by two or more requests count."""
    from collections import Counter
    words = {n: {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in re.findall(r"[a-z]{3,}", n)} - GAP_STOP for n in names}
    freq = Counter(w for ws in words.values() for w in ws)
    groups = {}
    for n, ws in words.items():
        if ws:
            best = max(ws, key=lambda w: (freq[w], len(w)))
            if freq[best] >= 2:
                groups.setdefault(best, []).append(n)
    return sorted(groups.items(), key=lambda kv: -len(kv[1]))


def rollup(files):
    """Markdown summary across graphics.yaml files: element use, and the new assets several papers want."""
    from collections import Counter, defaultdict
    use, gaps, papers = Counter(), defaultdict(list), 0
    for f in files:
        d = yaml.safe_load(Path(f).read_text())
        papers += 1
        for g in d.get("graphics", []):
            el = g["element"]["kind"]
            if el == "new":
                name = re.sub(r"\s+", " ", str(g.get("new_asset", "")).lower()).strip()
                gaps[name].append(d.get("paper", Path(f).parent.name))
            else:
                use[el] += 1
    groups = []  # fuzzy-merge near-identical names
    for name, ps in sorted(gaps.items(), key=lambda kv: -len(kv[1])):
        for gr in groups:
            if difflib.SequenceMatcher(None, name, gr["name"]).ratio() > 0.8:
                gr["papers"] += ps
                gr["variants"].append(name)
                break
        else:
            groups.append({"name": name, "papers": list(ps), "variants": [name]})
    groups.sort(key=lambda g: -len(set(g["papers"])))
    out = [f"# Graphic elements suggested across {papers} papers", "", "## Existing elements, by how often they were suggested", ""]
    out += [f"- `{k}`: {v}" for k, v in use.most_common()]
    names = [str(g.get("new_asset", "")).lower() for f in files for g in yaml.safe_load(Path(f).read_text()).get("graphics", []) if g["element"]["kind"] == "new"]
    themes = gap_themes(names)
    if themes:
        out += ["", "## Missing assets, grouped by what they depict", ""]
        out += [f"- **{w}**: {len(ns)} requests, e.g. " + "; ".join(ns[:3]) for w, ns in themes]
    out += ["", "## Assets that do not exist yet, by how many papers want them", ""]
    out += [f"- **{g['name']}**: {len(set(g['papers']))} papers" + (f" (also: {', '.join(v for v in g['variants'][1:4])})" if len(g['variants']) > 1 else "") for g in groups[:40]]
    return "\n".join(out) + "\n"


def main(argv=None):
    from llm import LLMError, add_arguments, chat, settings
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards", nargs="?", help="a paper's cards.yaml")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--rollup", nargs="+", metavar="graphics.yaml", help="summarise these graphics.yaml files instead of asking a model")
    ap.add_argument("--paper", default="", help="the paper's name for the output (default: the cards folder's name)")
    add_arguments(ap, model_help="the model that proposes the graphics")
    args = ap.parse_args(argv)
    if args.rollup:
        Path(args.out).write_text(rollup(args.rollup))
        print(f"rollup of {len(args.rollup)} files -> {args.out}")
        return 0
    if not args.cards:
        sys.exit("give a cards.yaml, or --rollup")
    try:
        cfg = settings(args.backend, args.base_url, args.model)
    except LLMError as e:
        sys.exit(str(e))
    doc = yaml.safe_load(Path(args.cards).read_text())
    cards = doc["claims"] if isinstance(doc, dict) else doc
    kept, rejected = suggest(cards, lambda p: chat(p, cfg, temperature=0.3, max_tokens=8000))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(yaml.safe_dump({"paper": args.paper or Path(args.cards).parent.name, "model": cfg["model"], "graphics": kept, "rejected": rejected},
                                             sort_keys=False, allow_unicode=True, width=100))
    print(f"{len(kept)} suggestions kept, {len(rejected)} rejected -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
