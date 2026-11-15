#!/usr/bin/env python3
"""Write a wiki topic page from the cards of several papers, with every sentence tied to the cards it rests on.

    python scripts/topic_from_cards.py --topic "Gallery programs" -o pages/gallery-programs.md \\
        --from kenning-2016=cards/kenning/cards.yaml --label kenning-2016="Kenning 2016" \\
        --from camic-2014=cards/camic/cards.yaml --label camic-2014="Camic 2014"

A topic page written by a model from other models' summaries compounds their errors. This one is written from the cards themselves
(each a paraphrase, a page and an exact quote), and every statement it makes must name the cards it rests on, as `ref:C12`. The model's
reply is then checked, and any statement is dropped and reported if it:
  * cites no card, or a card that does not exist;
  * states a number that appears in none of the cards it cites;
  * is offered as a tension between sources but cites cards from fewer than two papers;
  * is offered as an open question but cites no card where the authors call for further research or state a limitation.
The page lists any paper none of whose cards were cited, so a gap shows. The cards are model-drafted: the page is as reliable as they
are, and says so. Models: see scripts/llm.py and docs/SETUP.md.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from suggest_graphics import numbers_in  # noqa: E402

FLAGGED = ("overstated", "different", "unclear")
OPEN_KINDS = ("future_research", "caveat")

PROMPT = """Write a synthesis of what these papers say about the topic "{topic}", using ONLY the numbered cards below. Each card is
`<card id> [kind, page] paraphrase`, where the card id looks like `paper:C12`.

Return JSON: {{"synthesis": [{{"text": "<2 to 4 sentences>", "cites": ["<card id>", "<card id>"]}}], "tensions": [{{"text": "<where two papers differ>", "cites": ["<card id>", "<card id>"]}}],
"open_questions": [{{"text": "<a question the papers leave open>", "cites": ["<card id>"]}}]}}

Papers (the label to use for each in your text, if you name a paper at all):
{papers}

Rules:
- Name a paper only by its label above, exactly as written. Do not add authors, "et al.", or years that are not in the label.
- Give 4 to 8 synthesis paragraphs. Every item must cite the cards it rests on, by their full id exactly as it is written before each card, with no extra prefix.
- Say what a paper found as that paper's finding; never credit one paper with another's result. Keep hedges ("suggests", "appeared to").
- A number may appear only if a cited card states it. Do not rank the studies or call one better.
- A tension must cite cards from at least two different papers. If the papers do not differ, return no tensions.
- Give 1 to 3 open questions. Each must cite a card where the authors call for further research or state a limitation.

Cards:
{cards}
"""


def load(spec):
    ref, _, path = spec.partition("=")
    doc = yaml.safe_load(Path(path).read_text())
    cards = doc["claims"] if isinstance(doc, dict) else doc
    return ref, [c for c in cards if (c.get("model_check") or {}).get("verdict") not in FLAGGED]


def parse(text):
    try:
        return json.loads(text)
    except ValueError:
        return {}


def normalise_cite(cite, index):
    """Models often write the prompt's literal `ref:` in front of a card id (`ref:camic-2014:C5`); drop it when the rest is a real card."""
    return cite[4:] if cite.startswith("ref:") and cite not in index and cite[4:] in index else cite


def check(reply, index, labels=None):
    """Return (kept, rejected): each item of synthesis, tensions and open_questions that passes the rules; a rejection carries its reason."""
    kept = {"synthesis": [], "tensions": [], "open_questions": []}
    rejected = []
    named = set().union(*(numbers_in(v) for v in (labels or {}).values()))  # a year in a paper's own label is a citation, not a finding
    for section in kept:
        for item in reply.get(section) or []:
            cites = [normalise_cite(c, index) for c in item.get("cites") or []]
            item["cites"] = cites
            text = item.get("text", "")
            why = None
            if not cites:
                why = "it cites no card"
            elif any(c not in index for c in cites):
                why = "it cites a card that does not exist: " + ", ".join(c for c in cites if c not in index)
            else:
                have = set().union(*(numbers_in(index[c]["text"] + " " + index[c]["source"]["quote"]) for c in cites))
                missing = sorted(numbers_in(text) - have - named)
                if missing:
                    why = f"it states a number the cited cards do not contain: {', '.join(missing)}"
                elif section == "tensions" and len({c.split(":")[0] for c in cites}) < 2:
                    why = "a tension must cite cards from at least two papers"
                elif section == "open_questions" and not any(index[c]["kind"] in OPEN_KINDS for c in cites):
                    why = "an open question must cite a card of kind future_research or caveat"
            (rejected.append({"section": section, "text": text, "why": why}) if why else kept[section].append(item))
    return kept, rejected


def cite_text(cites, index, labels):
    """'(Kenning 2016, p.13; Camic 2014, p.7)' from card ids, merging pages of the same paper."""
    by = {}
    for c in cites:
        ref = c.split(":")[0]
        by.setdefault(ref, []).append(str(index[c]["source"]["page"]))
    return "(" + "; ".join(f"{labels.get(r, r)}, p." + ",".join(sorted(set(p), key=int)) for r, p in by.items()) + ")"


def render(topic, kept, rejected, index, labels, refs, model="", slug=""):
    cited = {c.split(":")[0] for sec in kept.values() for it in sec for c in it["cites"]}
    fm = {"type": "topic", "generated_by": "cards", "reviewed": False, "title": topic, "slug": slug or re.sub(r"[^a-z0-9]+", "-", topic.lower()).strip("-"),
          "sources": [labels.get(r, r) for r in refs], "model": model, "statements_kept": sum(len(v) for v in kept.values()), "statements_dropped": len(rejected)}
    out = ["---", yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000).strip(), "---", "", f"## {topic}", "",
           "_Every statement names the papers and pages it rests on. The cards behind them were drafted by a model and checked against the page text; "
           "no person has read them yet._", ""]
    for heading, key in (("Synthesis", "synthesis"), ("Where the papers differ", "tensions")):
        if kept[key]:
            out += [f"## {heading}", ""]
            out += [f"{it['text'].strip()} {cite_text(it['cites'], index, labels)}\n" for it in kept[key]]
    if kept["open_questions"]:
        out += ["## Open questions", ""]
        out += [f"- {it['text'].strip()} {cite_text(it['cites'], index, labels)}" for it in kept["open_questions"]]
        out.append("")
    unused = [labels.get(r, r) for r in refs if r not in cited]
    out += ["## Papers", ""] + [f"- {labels.get(r, r)}" + ("" if r in cited else " (none of its cards were cited above)") for r in refs] + [""]
    if unused:
        out += [f"_Not used in the statements above: {', '.join(unused)}._", ""]
    return "\n".join(out)


def main(argv=None):
    from llm import LLMError, add_arguments, chat, settings
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--topic", required=True)
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--from", dest="sources", action="append", required=True, metavar="REF=cards.yaml", help="a paper's id and its cards.yaml (repeat)")
    ap.add_argument("--label", action="append", default=[], metavar="REF=Author Year", help="how to cite a paper in the text (repeat)")
    ap.add_argument("--report", help="write the dropped statements and their reasons here (JSON)")
    add_arguments(ap, model_help="the model that writes the synthesis")
    args = ap.parse_args(argv)
    try:
        cfg = settings(args.backend, args.base_url, args.model)
    except LLMError as e:
        sys.exit(str(e))
    labels = dict(x.partition("=")[::2] for x in args.label)
    index, refs, lines = {}, [], []
    for spec in args.sources:
        ref, cards = load(spec)
        refs.append(ref)
        for c in cards:
            index[f"{ref}:{c['id']}"] = c
            lines.append(f"{ref}:{c['id']} [{c['kind']}, p{c['source']['page']}] {c['text']}")
    papers = "\n".join(f"- {labels.get(r, r)}" for r in refs)
    reply = parse(chat(PROMPT.format(topic=args.topic, papers=papers, cards="\n".join(lines)), cfg, temperature=0.2, max_tokens=12000, num_ctx=65536))
    kept, rejected = check(reply, index, labels)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(render(args.topic, kept, rejected, index, labels, refs, cfg["model"]))
    if args.report:
        Path(args.report).write_text(json.dumps(rejected, indent=2))
    print(f"{sum(len(v) for v in kept.values())} statements kept, {len(rejected)} dropped -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
