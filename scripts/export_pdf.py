#!/usr/bin/env python3
"""Export a storyboard as a PDF: one A4 page per comic page.

Renders the xkcd-style pages, then prints them with a headless Chrome or Chromium (which must be
installed). The contact sheet carries print rules, so each PDF page holds exactly one comic page.

    python scripts/export_pdf.py examples/lin-2017-wap-npc/storyboard.yaml -o output/lin-2017.pdf
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "renderers" / "xkcd"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render  # noqa: E402

BROWSERS = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome")


def find_browser():
    for name in BROWSERS:
        path = shutil.which(name)
        if path:
            return path
    return None


def export(storyboard, out_pdf, browser=None, wait_ms=15000):
    """Write the PDF and return its path."""
    browser = browser or find_browser()
    if not browser:
        raise RuntimeError("no Chrome or Chromium found; install one, or print the sheet.html yourself")
    doc = yaml.safe_load(Path(storyboard).read_text())
    out_pdf = Path(out_pdf).resolve()
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        render.render(doc, tmp, standalone=True)
        subprocess.run(
            [browser, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
             f"--virtual-time-budget={wait_ms}", f"--print-to-pdf={out_pdf}", f"file://{tmp}/sheet.html"],
            check=True, capture_output=True, timeout=180)
    return out_pdf


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("storyboard")
    ap.add_argument("-o", "--out", required=True)
    args = ap.parse_args(argv)
    print(f"wrote {export(args.storyboard, args.out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
