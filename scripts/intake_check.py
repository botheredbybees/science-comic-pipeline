#!/usr/bin/env python3
"""Check a PDF (or a folder of PDFs) before a comic is made from it: is there real text to quote, and what kind of document is it?

    python scripts/intake_check.py paper.pdf
    python scripts/intake_check.py "UTAS_readings/Week07/pdfs" --json

For each PDF it reports pages, words, words per page, and flags:
  scanned         almost no text: a scanned image or a protected file; there is nothing to quote
  abstract-only   one to two pages with a short body: a conference poster or abstract, not a full paper
  reference-list  mostly citations (many "Surname, A. B." entries per 100 words): a bibliography, not an article
  fragment        a mid-document slice: starts without a title and the footer says "Printed page N of M" with N > 1
and a licence hint taken from the text itself ("CC BY ...", "All rights reserved", "Copyright ..."). The hint is for a person to
confirm; it is not a licence check. Needs `pdftotext` and `pdfinfo` (poppler).
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CITATION = re.compile(r"\b[A-Z][a-zA-Z\-']+,\s+(?:[A-Z]\.\s*)+(?:,|&|\()")
CC = re.compile(r"Creative Commons[^.\n]{0,80}|CC[ -]BY(?:-[A-Z]{2})*(?:[ -]\d\.\d)?", re.I)
RIGHTS = re.compile(r"All rights (?:are )?reserved|Copyright\s*(?:©|\(c\))[^\n]{0,60}|(?:©|\(c\))\s*\d{4}[^\n]{0,60}", re.I)
FOOTER = re.compile(r"Printed page (\d+) of (\d+)")


def assess(text, pages):
    """Flags and measures for the extracted text of a document of `pages` pages."""
    words = len(text.split())
    per_page = words / max(pages, 1)
    cites = len(CITATION.findall(text)) / max(words / 100, 1)
    flags = []
    if per_page < 40:
        flags.append("scanned")
    elif pages <= 2 and words < 900:
        flags.append("abstract-only")
    if cites > 4 and words >= 50:
        flags.append("reference-list")
    m = FOOTER.search(text)
    if m and int(m.group(1)) == 1 and not re.search(r"\b(?:abstract|introduction|chapter \d+)\b", text[:1500], re.I):
        flags.append("fragment")
    cc, rights = CC.search(text), RIGHTS.search(text)
    licence = (cc.group(0).strip() if cc else (rights.group(0).strip() if rights else ""))
    return {"pages": pages, "words": words, "words_per_page": round(per_page), "citations_per_100_words": round(cites, 1),
            "flags": flags, "licence_hint": licence[:90]}


def pdf_info(path):
    out = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
    m = re.search(r"Pages:\s+(\d+)", out)
    text = subprocess.run(["pdftotext", str(path), "-"], capture_output=True, text=True).stdout
    return text, int(m.group(1)) if m else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    p = Path(args.path)
    pdfs = sorted(p.rglob("*.pdf")) if p.is_dir() else [p]
    rows = []
    for f in pdfs:
        text, pages = pdf_info(f)
        rows.append({"file": f.name, **assess(text, pages)})
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        for r in rows:
            print(f"{r['pages']:>4}p {r['words']:>6}w {r['words_per_page']:>5}/p  {','.join(r['flags']) or 'ok':<24} {r['file'][:60]}  {r['licence_hint']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
