#!/usr/bin/env python3
"""Ask a second language model whether each card's paraphrase is fairly supported by its quote, and record the verdict.

    LLM_MODEL=<model name> python scripts/verify_cards.py cards/<slug>/cards.yaml        # a different, preferably larger, model than the extractor

scripts/extract_cards.py guarantees the quote is real; it cannot say whether the paraphrase over-reaches it. This asks another model,
with only the claim and the quote in front of it, for one verdict per card: supported, overstated (says more or stronger than the
quote), different (about something else) or unclear. The verdict is written to the card as `model_check`. In a test with 12 planted
errors among 48 cards, a 122B model caught all 12 and flagged 2 of the 36 untouched cards. Treat the flags as a reading list for a
person: a card that passes is still unreviewed, and only a person marks a claim `verified`.
"""
import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from llm import add_arguments, chat, settings, LLMError  # noqa: E402

BATCH = 40
PROMPT = """For each numbered item, judge whether the CLAIM is fairly and fully supported by the QUOTE alone (the quote is the only evidence). Verdicts: "supported" (the claim says no more than the quote does), "overstated" (the claim says more, or stronger, than the quote), "different" (the claim is about something else), "unclear".
Return JSON: {{"verdicts": [{{"id": "C1", "verdict": "...", "why": "<six words or fewer>"}}]}}. Judge every item.

{items}"""


def verify(cards, ask_fn):
    """Add `model_check` ({verdict, why}) to every card; return the verdict counts."""
    counts = {}
    for i in range(0, len(cards), BATCH):
        batch = cards[i:i + BATCH]
        items = "\n".join(f'{c["id"]}. CLAIM: {c["text"]}\n   QUOTE: {c["source"]["quote"]}' for c in batch)
        try:
            verdicts = {v["id"]: v for v in json.loads(ask_fn(PROMPT.format(items=items)))["verdicts"]}
        except (ValueError, KeyError):
            verdicts = {}
        for c in batch:
            v = verdicts.get(c["id"], {"verdict": "unclear", "why": "no verdict returned"})
            c["model_check"] = {"verdict": v.get("verdict", "unclear"), "why": v.get("why", "")}
            counts[c["model_check"]["verdict"]] = counts.get(c["model_check"]["verdict"], 0) + 1
    return counts


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cards")
    add_arguments(ap, model_env="LLM_VERIFY_MODEL", model_help="the checking model: use a different, preferably larger, model than the one that extracted the cards")
    args = ap.parse_args(argv)
    try:
        cfg = settings(args.backend, args.base_url, args.model, model_env="LLM_VERIFY_MODEL")
    except LLMError as e:
        sys.exit(str(e))
    if not cfg["model"]:
        sys.exit("give --model or set LLM_VERIFY_MODEL (use a different, preferably larger, model than the one that extracted the cards)")
    path = Path(args.cards)
    doc = yaml.safe_load(path.read_text())
    counts = verify(doc["claims"], lambda p: chat(p, cfg, temperature=0.0, max_tokens=8000))
    path.write_text(yaml.dump(doc, sort_keys=False, width=100, allow_unicode=True))
    print(f"{len(doc['claims'])} cards checked by {cfg['model']}: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
