#!/usr/bin/env python3
"""Choose the key cards for a paper, and mark the cards that should not be on a summary page at all.

    python scripts/select_key_cards.py cards/<slug>/cards.yaml -o cards/<slug>/key.yaml

A paper can yield 150 cards. A source page needs the ones that matter: what the paper is for, how it was done, what it found, what it
cautions, what it asks for next. A model is asked to pick those by id. In a separate question it is asked which cards are about one
specific person (a participant's diagnosis, behaviour or family), and those are left off the page; a card of kind method, caveat or
future_research is never left off. The model writes no text: it only chooses among cards that already exist, so selecting cannot
add a claim. Ids that do not exist are discarded; if the model picks too few, the gap is filled by card kind. Models: see scripts/llm.py and docs/SETUP.md.
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

PRIORITY = ("result", "method", "future_research", "caveat", "argument", "interpretation", "practice", "background")
NEVER_OMITTED = ("future_research", "caveat", "method")  # a card of these kinds is about the study, not a person, so it is never left off

PROMPT_KEY = """Below are the claims ("cards") drawn from one paper. Choose the {n} that a reader most needs to understand the paper.

Return JSON: {{"key": ["C3", "C9"]}}

Choose so that, where the paper has them, the cards cover: what the paper is for, who or what was studied and how, the main findings
(with their numbers and hedges), the main limitations the authors state, and what they say is needed next. Spread them across the paper.

Cards:
{cards}
"""

PROMPT_INDIVIDUALS = """Below are claims ("cards") drawn from one paper. List the ids of the cards whose subject is ONE specific person: someone
named (a pseudonym counts) or individually described, such as a participant's diagnosis, behaviour or family.

Do NOT list a card about participants in general, a group, a programme, a method, a finding, a limitation or a reference list. Most papers
have no such cards; then return an empty list.

Return JSON: {{"individuals": ["C41", "C42"]}}

Cards:
{cards}
"""


def parse(text):
    try:
        return json.loads(text)
    except ValueError:
        return {}


def select(cards, ask_fn, n=None):
    """Return {"key": [ids], "omit": [ids]} for the cards. The model only chooses among existing cards, and every id is checked.

    Two separate questions: which cards matter (key), and which are about one specific person (omit). They were once one reply, and
    the model then treated "omit" as "everything that is not key", dropping results and calls for research."""
    usable = [c for c in cards if (c.get("model_check") or {}).get("verdict") not in ("overstated", "different", "unclear")]
    by_id = {c["id"]: c for c in usable}
    n = n or min(25, max(10, len(usable) // 4))
    listing = "\n".join(f"{c['id']} [{c['kind']}, p{c['source']['page']}] {c['text']}" for c in usable)
    omit_reply = parse(ask_fn(PROMPT_INDIVIDUALS.format(cards=listing)))
    omit = [i for i in dict.fromkeys(omit_reply.get("individuals") or []) if i in by_id and by_id[i]["kind"] not in NEVER_OMITTED]
    key_reply = parse(ask_fn(PROMPT_KEY.format(n=n, cards=listing)))
    key = [i for i in dict.fromkeys(key_reply.get("key") or []) if i in by_id and i not in omit][:n]
    if len(key) < min(6, len(usable)):  # the model chose too few: fill by kind, then by order
        have = set(key)
        for kind in PRIORITY:
            for c in usable:
                if len(key) >= min(n, 12):
                    break
                if c["kind"] == kind and c["id"] not in have and c["id"] not in omit:
                    key.append(c["id"])
                    have.add(c["id"])
    return {"key": key, "omit": omit}


def main(argv=None):
    from llm import LLMError, add_arguments, chat, settings
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("-n", type=int, default=None, help="how many key cards (default: a sixth of the cards, between 8 and 25)")
    add_arguments(ap, model_help="the model that chooses")
    args = ap.parse_args(argv)
    try:
        cfg = settings(args.backend, args.base_url, args.model)
    except LLMError as e:
        sys.exit(str(e))
    doc = yaml.safe_load(Path(args.cards).read_text())
    cards = doc["claims"] if isinstance(doc, dict) else doc
    res = select(cards, lambda p: chat(p, cfg, temperature=0.1, max_tokens=4000), args.n)
    res["model"] = cfg["model"]
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(yaml.safe_dump(res, sort_keys=False))
    print(f"{len(res['key'])} key cards, {len(res['omit'])} omitted of {len(cards)} -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
