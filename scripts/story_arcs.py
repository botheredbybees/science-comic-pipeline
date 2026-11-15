#!/usr/bin/env python3
"""EXPERIMENT. Propose two or three story arcs from a topic page, each beat tied to the statements it rests on.

    python scripts/story_arcs.py pages/gallery-programs.md -o arcs/gallery-programs.arcs.md [--report dropped.json]

A topic page (scripts/topic_from_cards.py) is a list of statements, each with its papers and pages. An arc is an order to tell them in:
a handful of beats that go from a question to what is still open, or from one side of a disagreement to the other. The model chooses the order
and the wording; it may not add a fact. Every beat must name the statements it rests on (S1, S2 ...). The reply is then checked, and a beat is
dropped and reported if it:
  * cites no statement, or one that does not exist;
  * states a number that appears in none of the statements it cites;
  * is told as a disagreement ("tension") but cites no statement from the page's "Where the papers differ" section;
  * is told as an open question ("open") but cites no statement from the page's "Open questions" section.
An arc left with fewer than three beats is dropped. The arcs are as reliable as the topic page, which is as reliable as its cards (model-drafted,
not yet read by a person), and they are a suggestion of order, not a script: nothing here writes the comic. Models: see scripts/llm.py.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from suggest_graphics import numbers_in  # noqa: E402

SECTIONS = {"Synthesis": "finding", "Where the papers differ": "tension", "Open questions": "open"}
ROLES = ("setup", "finding", "tension", "open")
MIN_BEATS = 3

PROMPT = """Below are the numbered statements of a review of "{topic}". Propose {n} different story arcs: orders in which the statements could be told to a reader
who knows nothing about the subject. An arc has 4 to 6 beats. Each beat is one or two plain sentences that restate what its statements say, nothing more.

Return JSON: {{"arcs": [{{"name": "<3 to 6 words>", "shape": "<question and answer | two sides | from problem to practice | what we do not know>", "logline": "<one sentence>",
"beats": [{{"role": "<setup | finding | tension | open>", "text": "<1 or 2 sentences>", "cites": ["S1", "S4"]}}]}}]}}

Rules:
- Use ONLY the statements. A beat may restate, combine or reorder them; it may not add a fact, a cause or a number. Keep their hedges ("suggests", "appeared to").
- Every beat cites the statement numbers it rests on, written exactly as S1, S2.
- A beat with role "tension" must cite a statement marked [differ]. A beat with role "open" must cite a statement marked [open]. A "setup" or "finding" beat may cite any.
- Name a paper only by a label from the list below, exactly as written, and only when a cited statement names it.
- The {n} arcs must differ in their shape or in which statements they lean on, not just in their wording.
- Do not rank the studies or say one is better. If the page has an [open] statement, end at least one arc on it.

Paper labels: {labels}

Statements:
{statements}
"""


def parse_topic(md):
    """Read a topic page: its title, the paper labels, and the statements as [{id, section, text, cite}] in page order."""
    title = (re.search(r"^title:\s*(.+)$", md, re.M) or [None, "the topic"])[1].strip()
    labels = re.findall(r"^- (.+?)(?: \(none of its cards were cited above\))?$", md.split("\n## Papers", 1)[-1], re.M) if "\n## Papers" in md else []
    out, section = [], None
    for line in md.split("\n"):
        h = re.match(r"^## (.+)$", line)
        if h:
            section = SECTIONS.get(h.group(1).strip())
            continue
        if section and line.strip() and not line.startswith("_") and not line.startswith("#"):
            body = line[2:] if line.startswith("- ") else line
            m = re.match(r"^(.*?)\s*(\((?:[^()]|\([^()]*\))*,\s*p\.[\d,]+(?:;[^()]*)?\))\s*$", body.strip())
            text, cite = (m.group(1), m.group(2)) if m else (body.strip(), "")
            out.append({"id": f"S{len(out) + 1}", "section": section, "text": text.strip(), "cite": cite})
    return title, [x for x in labels if x and not x.startswith("Not used")], out


def parse(text):
    try:
        return json.loads(text)
    except ValueError:
        return {}


def check(reply, statements, labels=()):
    """Return (arcs, rejected): arcs whose beats passed (an arc with fewer than MIN_BEATS is dropped); a rejection carries its reason."""
    index = {s["id"]: s for s in statements}
    named = set().union(*(numbers_in(x) for x in labels)) if labels else set()
    arcs, rejected = [], []
    for arc in reply.get("arcs") or []:
        beats = []
        for b in arc.get("beats") or []:
            cites = [c for c in dict.fromkeys(b.get("cites") or [])]
            text, role = b.get("text", ""), b.get("role", "finding")
            why = None
            if not cites:
                why = "it cites no statement"
            elif any(c not in index for c in cites):
                why = "it cites a statement that does not exist: " + ", ".join(c for c in cites if c not in index)
            else:
                have = set().union(*(numbers_in(index[c]["text"]) for c in cites))
                missing = sorted(numbers_in(text) - have - named)
                if missing:
                    why = "it states a number the cited statements do not contain: " + ", ".join(missing)
                elif role == "tension" and not any(index[c]["section"] == "tension" for c in cites):
                    why = "a tension beat must cite a statement from 'Where the papers differ'"
                elif role == "open" and not any(index[c]["section"] == "open" for c in cites):
                    why = "an open beat must cite a statement from 'Open questions'"
                elif role not in ROLES:
                    why = f"unknown role {role!r}"
            if why:
                rejected.append({"arc": arc.get("name", ""), "text": text, "why": why})
            else:
                beats.append({"role": role, "text": text.strip(), "cites": cites})
        if len(beats) >= MIN_BEATS:
            arcs.append({"name": arc.get("name", "").strip(), "shape": arc.get("shape", ""), "logline": arc.get("logline", "").strip(), "beats": beats})
        else:
            rejected.append({"arc": arc.get("name", ""), "text": "", "why": f"only {len(beats)} beat(s) survived the checks (needs {MIN_BEATS})"})
    return arcs, rejected


def render(title, arcs, rejected, statements, source, model=""):
    index = {s["id"]: s for s in statements}
    fm = {"type": "story-arcs", "generated_by": "topic page", "experiment": True, "reviewed": False, "topic": title, "source": source, "model": model,
          "arcs": len(arcs), "beats_dropped": sum(1 for r in rejected if r["text"])}
    out = ["---", yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000).strip(), "---", "", f"## Story arcs: {title}", "",
           "_An experiment. Each arc is an order to tell the topic page's statements in; every beat names the statements it rests on and the papers and pages behind them. "
           "No person has read the arcs or the cards under them._", ""]
    if not arcs:
        out += ["No arc survived the checks.", ""]
    for n, a in enumerate(arcs, 1):
        out += [f"### Arc {n}: {a['name']}", "", f"_{a['shape']}_. {a['logline']}", ""]
        for i, b in enumerate(a["beats"], 1):
            cites = "; ".join(dict.fromkeys(index[c]["cite"].strip("()") for c in b["cites"] if index[c]["cite"]))
            out.append(f"{i}. **{b['role']}**: {b['text']} ({', '.join(b['cites'])}{'; ' + cites if cites else ''})")
        out.append("")
    used = {c for a in arcs for b in a["beats"] for c in b["cites"]}
    left = [s["id"] for s in statements if s["id"] not in used]
    out += ["## Statements", ""] + [f"- {s['id']} [{s['section']}] {s['text']} {s['cite']}".rstrip() for s in statements] + [""]
    if left:
        out += [f"_Not used in any arc: {', '.join(left)}._", ""]
    return "\n".join(out)


def main(argv=None):
    from llm import LLMError, add_arguments, chat, settings
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("topic_page", help="a page written by topic_from_cards.py")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("-n", "--arcs", type=int, default=3, help="how many arcs to ask for (default 3)")
    ap.add_argument("--report", help="write the dropped beats and their reasons here (JSON)")
    add_arguments(ap, model_help="the model that proposes the arcs")
    args = ap.parse_args(argv)
    try:
        cfg = settings(args.backend, args.base_url, args.model)
    except LLMError as e:
        sys.exit(str(e))
    md = Path(args.topic_page).read_text()
    title, labels, statements = parse_topic(md)
    if len(statements) < 4:
        sys.exit(f"{args.topic_page}: only {len(statements)} statements; not enough for an arc")
    tag = {"finding": "", "tension": " [differ]", "open": " [open]"}
    lines = "\n".join(f"{s['id']}{tag[s['section']]} {s['text']} {s['cite']}".rstrip() for s in statements)
    reply = parse(chat(PROMPT.format(topic=title, n=args.arcs, labels="; ".join(labels), statements=lines), cfg, temperature=0.4, max_tokens=8000, num_ctx=32768))
    arcs, rejected = check(reply, statements, labels)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(render(title, arcs, rejected, statements, Path(args.topic_page).name, cfg["model"]))
    if args.report:
        Path(args.report).write_text(json.dumps(rejected, indent=2))
    print(f"{len(arcs)} arcs, {sum(len(a['beats']) for a in arcs)} beats kept, {sum(1 for r in rejected if r['text'])} beats dropped -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
