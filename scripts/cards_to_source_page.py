#!/usr/bin/env python3
"""Build a wiki source page from a paper's cards, with no model: every line is a card, and every card has a page and exact words.

    python scripts/cards_to_source_page.py cards/<slug>/cards.yaml -o pages/<slug>.md \\
        --title "Paper title" --apa7 "Author (2020). Title." --doi 10.xxxx/yyyy --slug <slug>
    python scripts/cards_to_source_page.py cards/<slug>/cards.yaml -o pages/<slug>.md --meta-page old-wiki/sources/<slug>.md \\
        --graphics graphics/<slug>/graphics.yaml

A summary written by a model from a sample of the paper can state things the paper does not say, and it carries no page numbers.
This page cannot: its body is only the cards that `extract_cards.py` drafted, each with the paraphrase, its page, and the quote it
rests on (the quote is verified to be on that page). Cards a second model flagged as overstated, different or unclear are listed
apart under "Needs review", not mixed in. Nothing here is marked verified: the cards are drafts until a person reads them.

`--meta-page` copies the title, citation, DOI, tags and appearances from an existing wiki source page, so the wiki's graph does not
change; `--graphics` adds the suggested graphic elements from `suggest_graphics.py`; `--key` takes the `key.yaml` from
`select_key_cards.py`: the page then leads with the key cards, lists the rest under "More detail", and leaves off the cards the
selection omitted (about named individuals, reference entries, logistics).
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

SECTIONS = [
    ("Background", ("background",)),
    ("Methods", ("method",)),
    ("Results", ("result",)),
    ("Interpretation and arguments", ("interpretation", "argument")),
    ("Practice", ("practice",)),
    ("Caveats and limitations", ("caveat",)),
    ("Calls for further research", ("future_research",)),
]
FLAGGED = ("overstated", "different", "unclear")


def load_cards(path):
    doc = yaml.safe_load(Path(path).read_text())
    return doc["claims"] if isinstance(doc, dict) else doc


def verdict(card):
    return (card.get("model_check") or {}).get("verdict", "unchecked")


def meta_from_page(path):
    """title, apa7, doi, slug, appearances and tags from an existing wiki source page's frontmatter."""
    text = Path(path).read_text(encoding="utf-8-sig")
    m = re.match(r"\A---[ \t]*\r?\n(.*?)^---[ \t]*\r?$", text, re.DOTALL | re.MULTILINE)
    if not m:
        return {}
    fm = yaml.safe_load(m.group(1)) or {}
    return {k: fm[k] for k in ("title", "apa7", "doi", "slug", "appearances", "tags") if fm.get(k) not in (None, "")}


def pages_covered(cards, n_pages):
    pages = {int(c["source"]["page"]) for c in cards if str(c["source"].get("page", "")).isdigit()}
    return len(pages), n_pages or 0


def section_lines(cards, level="##"):
    out = []
    for heading, kinds in SECTIONS:
        sel = sorted((c for c in cards if c["kind"] in kinds), key=lambda c: (int(c["source"]["page"]), c["id"]))
        if sel:
            out += [f"{level} {heading}", ""] + [f"- {c['text']} (p.{c['source']['page']}) `{c['id']}`" for c in sel] + [""]
    return out


def render(cards, meta, graphics=None, n_pages=0, key=None):
    omit = set((key or {}).get("omit", []))
    shown = [c for c in cards if c["id"] not in omit]
    ok = [c for c in shown if verdict(c) not in FLAGGED]
    flagged = [c for c in shown if verdict(c) in FLAGGED]
    covered, total = pages_covered(cards, n_pages)
    fm = {"type": "source", "generated_by": "cards", "reviewed": False}
    fm.update({k: v for k, v in meta.items() if v not in (None, "")})
    fm["cards"] = len(cards)
    fm["cards_flagged"] = len([c for c in cards if verdict(c) in FLAGGED])
    if omit:
        fm["cards_left_off"] = len(omit & {c["id"] for c in cards})
    if total:
        fm["pages_with_cards"] = f"{covered} of {total}"
    out = ["---", yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, width=1000).strip(), "---", ""]
    title = meta.get("title") or "Source"
    out += [f"## {title}", "",
            "_Every line below is a card: a paraphrase, the page it is on, and the exact words it rests on (listed under Evidence). "
            "The cards were drafted by a model and the quotes were checked against the page text; no person has read them yet._", ""]
    if key:
        key_ids = set(key["key"])
        out += ["## Key points", "", "_Chosen from the paper's cards by a model; it wrote none of the words._", ""]
        out += section_lines([c for c in ok if c["id"] in key_ids], "###")
        rest = [c for c in ok if c["id"] not in key_ids]
        if rest:
            out += ["## More detail", ""] + section_lines(rest, "###")
    else:
        out += section_lines(ok)
    if flagged:
        out += ["## Needs review", "", "_A second model judged these overstated, about something else, or unclear against their quotes._", ""]
        out += [f"- {c['text']} (p.{c['source']['page']}) `{c['id']}`: **{verdict(c)}**" + (f" ({c['model_check']['why']})" if c.get("model_check", {}).get("why") else "")
                for c in sorted(flagged, key=lambda c: (int(c["source"]["page"]), c["id"]))]
        out.append("")
    if graphics:
        out += ["## Suggested graphic elements", ""]
        for g in graphics:
            el = g.get("element", {})
            kind = el.get("kind", "?")
            new = f" (a new asset: {g['new_asset']})" if kind == "new" and g.get("new_asset") else ""
            out.append(f"- **{g.get('title', '')}**: {g.get('shows', '')} Use `{kind}`{new}. Cards: {', '.join(g.get('claim_ids', []))}")
        out.append("")
    out += ["## Evidence", "", "_The exact words each card rests on._", ""]
    out += [f"- `{c['id']}` p.{c['source']['page']}: \"{c['source']['quote']}\"" for c in sorted(shown, key=lambda c: (int(c["source"]["page"]), c["id"]))]
    out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cards", help="the paper's cards.yaml")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--meta-page", help="copy title, citation, DOI, tags and appearances from this wiki source page")
    ap.add_argument("--title")
    ap.add_argument("--apa7")
    ap.add_argument("--doi")
    ap.add_argument("--slug")
    ap.add_argument("--graphics", help="a graphics.yaml from suggest_graphics.py to add as a section")
    ap.add_argument("--key", help="a key.yaml from select_key_cards.py: lead with the key cards and leave off the omitted ones")
    ap.add_argument("--n-pages", type=int, default=0, help="the paper's page count (default: counted from the cards folder's pages/)")
    args = ap.parse_args(argv)
    cards = load_cards(args.cards)
    meta = meta_from_page(args.meta_page) if args.meta_page else {}
    for k in ("title", "apa7", "doi", "slug"):
        if getattr(args, k):
            meta[k] = getattr(args, k)
    n_pages = args.n_pages or len(list((Path(args.cards).parent / "pages").glob("p*.txt")))
    graphics = yaml.safe_load(Path(args.graphics).read_text()).get("graphics") if args.graphics and Path(args.graphics).exists() else None
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    key = yaml.safe_load(Path(args.key).read_text()) if args.key and Path(args.key).exists() else None
    Path(args.out).write_text(render(cards, meta, graphics, n_pages, key))
    print(f"{len(cards)} cards -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
