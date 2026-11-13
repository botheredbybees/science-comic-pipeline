#!/usr/bin/env python3
"""Check that every claim's quote really appears in the source, on the page the claim names.

This is the machine half of "verified": a claim may only be `verified` if it carries a `quote`
and a `page`, and the quote is found on that page of the source text. Matching ignores case,
punctuation, line breaks, hyphenation at line ends and ligatures, so a quote copied from a
PDF extraction matches however the lines broke.

The source is either a directory of per-page text files (p001.txt, p002.txt, ...) or one text
file whose pages are separated by form feeds (what `pdftotext` writes).

    python scripts/check_quotes.py storyboard.yaml --pages-dir sources/<slug>/pages
    python scripts/check_quotes.py storyboard.yaml --text source.txt

A quote may be several fragments joined by " ... " (or an ellipsis): each fragment must appear on the
page, in that order. Use this when a sentence is split by a column break, a page number or a figure.

Errors: a verified claim with no quote or page, or whose quote is not on its page.
Warnings: a quote found only on another page; a claim with no quote; a number in the claim's
text that is not in its quote (a common sign of a misquote); a quote that contains a publisher's
"Downloaded from" footer. Exit code 1 on errors.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

import yaml

NUMBER = re.compile(r"\d+(?:\.\d+)?")
SVEDBERG = re.compile(r"\b\d+S\b")  # 16S, 18S, 28S: ribosomal RNA labels


def tokens(text, join_hyphens=True):
    """Lower-case word and number tokens, with hyphenated line breaks joined and ligatures undone.

    A soft hyphen at a line end always joins the word. A visible hyphen at a line end is ambiguous
    ("ap-/proximately" against "long-/term"), so `join_hyphens` picks one reading; `contains_any`
    tries both."""
    text = unicodedata.normalize("NFKC", text)
    text = re.sub("\u00ad\\s*\\n\\s*", "", text).replace("\u00ad", "")
    if join_hyphens:
        text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = text.lower().replace("\u2212", "-")
    return re.findall(r"[^\W_]+(?:\.\d+)?", text)


def load_pages(pages_dir=None, text_file=None):
    if pages_dir:
        files = sorted(Path(pages_dir).glob("p*.txt"))
        return {int(re.sub(r"\D", "", f.stem)): f.read_text(errors="ignore") for f in files}
    return {i: t for i, t in enumerate(Path(text_file).read_text(errors="ignore").split("\f"), 1)}


def find(page_tokens, quote_tokens, start=0):
    """Index just past the first run of quote_tokens at or after `start`, or -1."""
    n = len(quote_tokens)
    if not n:
        return -1
    for i in range(start, len(page_tokens) - n + 1):
        if page_tokens[i:i + n] == quote_tokens:
            return i + n
    return -1


def fragments(quote):
    """Split a quote into fragments on " ... " or an ellipsis; each must appear, in order."""
    return [f for f in re.split(r"\s*(?:\.\.\.|\u2026)\s*", quote) if f.strip()]


def contains(page_tokens, quote_tokens):
    return find(page_tokens, quote_tokens) >= 0


def contains_quote(page_text, quote):
    """True if every fragment of `quote` is on the page text, in order (either hyphen reading)."""
    for join in (True, False):
        pos, ok = 0, True
        page_tokens = tokens(page_text, join)
        for frag in fragments(quote):
            pos = find(page_tokens, tokens(frag, join), pos)
            if pos < 0:
                ok = False
                break
        if ok:
            return True
    return False


def edge_hint(page_text, quote):
    """If the quote fails only because of its first or last word, say so (line-end hyphens glue words)."""
    for frag in fragments(quote)[:1]:
        t = tokens(frag)
        if len(t) > 3 and contains_quote(page_text, " ".join(t[1:])):
            return "; it is found without its first word (a line-end hyphen can glue the word to the one before), so start the quote one word later"
        if len(t) > 3 and contains_quote(page_text, " ".join(t[:-1])):
            return "; it is found without its last word, so end the quote one word earlier"
    return ""


def dashes(text):
    """One kind of hyphen for locator comparison (page-map.txt may carry U+2010 or an en dash)."""
    return re.sub("[\u2010-\u2015\u2212]", "-", text)


def load_locators(pages_dir):
    """Map page number -> "Section, paragraph N" from page-map.txt (written by fetch_source.py), if present."""
    pm = Path(pages_dir).parent / "page-map.txt"
    out = {}
    if pm.exists():
        for line in pm.read_text().splitlines():
            m = re.match(r"p(\d+) \[(.*?)\] (?:para|abstract) (\d+):", line)
            if m:
                out[int(m.group(1))] = (m.group(2), int(m.group(3)))
    return out


def check(doc, pages, locators=None):
    """Return (errors, warnings)."""
    errors, warnings = [], []
    for c in doc["claims"]:
        src, cid = c["source"], c["id"]
        quote, page = src.get("quote"), src.get("page")
        if not quote:
            (errors if c["status"] == "verified" else warnings).append(f"{cid}: no quote to check")
            continue
        if not page:
            (errors if c["status"] == "verified" else warnings).append(f"{cid}: has a quote but no page")
            continue
        if "downloaded from" in quote.lower():
            warnings.append(f"{cid}: the quote contains a publisher footer (\"Downloaded from ...\"); quote the article, not the page furniture")
        if page not in pages:
            errors.append(f"{cid}: page {page} is not in the source")
        elif not contains_quote(pages[page], quote):
            elsewhere = [n for n, t in pages.items() if contains_quote(t, quote)]
            hint = f"; the quote is on page(s) {elsewhere}" if elsewhere else "; the quote is not on any page" + edge_hint(pages[page], quote)
            (errors if c["status"] == "verified" else warnings).append(f"{cid}: quote not found on page {page}{hint}")
            continue
        m = re.match(r"^(.*?),? paragraph (\d+)$", src.get("locator", "") or "")
        if m and locators and page in locators:
            sec, n = locators[page]
            # every part of the locator must appear in the section's path; headings with commas or numbers
            # ("3.2. Feeding, selectivity") are fine, since each comma-separated piece is looked for on its own
            path = re.sub(r"\s+", " ", dashes(sec.lower()))
            want = [dashes(x.strip().lower()) for x in re.split(r", | / ", m.group(1)) if x.strip()]
            if not all(w in path for w in want) or int(m.group(2)) != n:
                warnings.append(f"{cid}: locator \"{src['locator']}\" but page {page} is {sec}, paragraph {n}")
        # a label such as the 18S in "18S rRNA" is a name, not a quantity the quote has to contain
        missing = sorted(set(NUMBER.findall(SVEDBERG.sub("", c["text"]))) - set(NUMBER.findall(quote)))
        if missing:
            warnings.append(f"{cid}: number(s) {', '.join(missing)} in the claim are not in its quote")
    return errors, warnings


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("storyboard")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pages-dir")
    g.add_argument("--text")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args(argv)
    doc = yaml.safe_load(Path(args.storyboard).read_text())
    errors, warnings = check(doc, load_pages(args.pages_dir, args.text), load_locators(args.pages_dir) if args.pages_dir else None)
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    n = len(doc["claims"])
    print(f"{n} claim(s) checked: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
