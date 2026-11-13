#!/usr/bin/env python3
"""Turn a paper's PDF into per-page text files that check_quotes.py can read.

For a paper with no Europe PMC full text (a publisher PDF you downloaded, or a repository copy).
Writes `<out>/pages/p001.txt`, `p002.txt`, ... where the number is the PDF's own page index
(page 1 is the first page of the file, whatever the journal printed on it).

    python scripts/pdf_to_pages.py paper.pdf -o sources/<slug>
    python scripts/pdf_to_pages.py paper.pdf -o sources/<slug> --mode columns

Modes (needs `pdftotext` from poppler):
  raw      (default) the order the text was written into the file, which is reading order for most
           journal PDFs and keeps a two-column sentence in one piece.
  columns  crop each page into a left and a right half and read them in turn. Use it when `raw`
           still interleaves the columns. Page 1 (title, abstract) is usually one wide column, so it is
           read in `raw` mode; `--columns-from 1` changes that.
  default  poppler's own layout analysis (the same as `pdftotext` with no flags).

Look at a page file before trusting a mode: a quote must be a contiguous run of words from it.
Page furniture that a publisher stamps on every page ("Downloaded from https://...") is removed,
because it is easy to copy into a quote by accident. Soft hyphens are kept; check_quotes.py joins them.
Nothing here checks the licence: confirm it from the article's own text and write where you found it
in CLAIM-CHECK.md and `meta.source.licence_checked`.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

FURNITURE = re.compile(r"downloaded from https?://", re.I)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout


def page_count(pdf):
    m = re.search(r"^Pages:\s+(\d+)", run(["pdfinfo", str(pdf)]), re.M)
    if not m:
        raise SystemExit("could not read the page count with pdfinfo")
    return int(m.group(1))


def page_size(pdf, n):
    m = re.search(r"Page\s+%d size:\s+([\d.]+) x ([\d.]+)" % n, run(["pdfinfo", "-f", str(n), "-l", str(n), str(pdf)]))
    return (float(m.group(1)), float(m.group(2))) if m else (595.0, 842.0)


def extract(pdf, n, mode):
    base = ["pdftotext", "-f", str(n), "-l", str(n)]
    if mode == "raw":
        return run(base + ["-raw", str(pdf), "-"])
    if mode == "default":
        return run(base + [str(pdf), "-"])
    w, h = page_size(pdf, n)
    half = int(w / 2)
    left = run(base + ["-x", "0", "-y", "0", "-W", str(half), "-H", str(int(h)), str(pdf), "-"])
    right = run(base + ["-x", str(half), "-y", "0", "-W", str(int(w) - half), "-H", str(int(h)), str(pdf), "-"])
    return left + "\n" + right


def clean(text):
    """Drop publisher page furniture; return (text, number of lines dropped)."""
    keep, dropped = [], 0
    for line in text.splitlines():
        if FURNITURE.search(line):
            dropped += 1
        else:
            keep.append(line)
    return "\n".join(keep).replace("\f", "") + "\n", dropped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf")
    ap.add_argument("-o", "--out", required=True, help="source folder, e.g. sources/<slug>")
    ap.add_argument("--mode", choices=["raw", "columns", "default"], default="raw")
    ap.add_argument("--columns-from", type=int, default=2, help="first page read as two columns in columns mode (default 2)")
    args = ap.parse_args(argv)

    if not shutil.which("pdftotext") or not shutil.which("pdfinfo"):
        print("pdftotext and pdfinfo are needed (poppler-utils: `sudo apt install poppler-utils`)", file=sys.stderr)
        return 2
    pdf = Path(args.pdf)
    pages_dir = Path(args.out) / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    n_pages = page_count(pdf)
    dropped_total, empty = 0, []
    for n in range(1, n_pages + 1):
        mode = "raw" if args.mode == "columns" and n < args.columns_from else args.mode
        text, dropped = clean(extract(pdf, n, mode))
        dropped_total += dropped
        if len(text.split()) < 20:
            empty.append(n)
        (pages_dir / f"p{n:03d}.txt").write_text(text)
    print(f"{n_pages} page(s) written to {pages_dir} (mode: {args.mode}; page numbers are the PDF's page index)")
    if dropped_total:
        print(f"removed {dropped_total} publisher footer line(s) (\"Downloaded from ...\")")
    if empty:
        print(f"almost no text on page(s) {empty}: scanned images or figures only? (OCR is not done here)")
    first = (pages_dir / "p001.txt").read_text().strip().splitlines()[:6]
    print("page 1 begins:\n  " + "\n  ".join(first))
    print("Next: read one body page file and check that a sentence is contiguous; if the two columns are\n"
          "interleaved, rerun with --mode columns. Then write the licence and the page offset (PDF page index\n"
          "against the journal's printed page) in CLAIM-CHECK.md.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
