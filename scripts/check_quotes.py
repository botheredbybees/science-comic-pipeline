#!/usr/bin/env python3
"""Check that every claim's quote really appears in the source, on the page the claim names.

This is the machine half of "verified": a claim may only be `verified` if it carries a `quote`
and a `page`, and the quote is found on that page of the source text. Matching ignores case,
punctuation, line breaks, hyphenation at line ends and ligatures, so a quote copied from a
PDF extraction matches however the lines broke.

The source is either a directory of per-page text files (p001.txt, p002.txt, ...) or one text
file whose pages are separated by form feeds (what `pdftotext` writes).

    python scripts/check_quotes.py storyboard.yaml --pages-dir private/labstaf/source/pages
    python scripts/check_quotes.py storyboard.yaml --text source.txt

Errors: a verified claim with no quote or page, or whose quote is not on its page.
Warnings: a quote found only on another page; a claim with no quote; a number in the claim's
text that is not in its quote (a common sign of a misquote). Exit code 1 on errors.
"""
import argparse
import re
import sys
import unicodedata
from pathlib import Path

import yaml

NUMBER = re.compile(r"\d+(?:\.\d+)?")


def tokens(text):
    """Lower-case word and number tokens, with hyphenated line breaks joined and ligatures undone."""
    text = unicodedata.normalize("NFKC", text).replace("­", "")
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = text.lower().replace("−", "-")
    return re.findall(r"[^\W_]+(?:\.\d+)?", text)


def load_pages(pages_dir=None, text_file=None):
    if pages_dir:
        files = sorted(Path(pages_dir).glob("p*.txt"))
        return {int(re.sub(r"\D", "", f.stem)): f.read_text(errors="ignore") for f in files}
    return {i: t for i, t in enumerate(Path(text_file).read_text(errors="ignore").split("\f"), 1)}


def contains(page_tokens, quote_tokens):
    n = len(quote_tokens)
    return bool(n) and any(page_tokens[i:i + n] == quote_tokens for i in range(len(page_tokens) - n + 1))


def check(doc, pages):
    """Return (errors, warnings)."""
    errors, warnings = [], []
    toks = {n: tokens(t) for n, t in pages.items()}
    for c in doc["claims"]:
        src, cid = c["source"], c["id"]
        quote, page = src.get("quote"), src.get("page")
        if not quote:
            (errors if c["status"] == "verified" else warnings).append(f"{cid}: no quote to check")
            continue
        if not page:
            (errors if c["status"] == "verified" else warnings).append(f"{cid}: has a quote but no page")
            continue
        q = tokens(quote)
        if page not in toks:
            errors.append(f"{cid}: page {page} is not in the source")
        elif not contains(toks[page], q):
            elsewhere = [n for n, t in toks.items() if contains(t, q)]
            hint = f"; the quote is on page(s) {elsewhere}" if elsewhere else "; the quote is not on any page"
            (errors if c["status"] == "verified" else warnings).append(f"{cid}: quote not found on page {page}{hint}")
            continue
        missing = sorted(set(NUMBER.findall(c["text"])) - set(NUMBER.findall(quote)))
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
    errors, warnings = check(doc, load_pages(args.pages_dir, args.text))
    for e in errors:
        print(f"ERROR   {e}")
    for w in warnings:
        print(f"WARNING {w}")
    n = len(doc["claims"])
    print(f"{n} claim(s) checked: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
