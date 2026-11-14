#!/usr/bin/env python3
"""Draft a claims ledger from a PDF with a local language model, then force every quote onto the page text or drop it.

    LLM_MODEL=<model name> python scripts/extract_cards.py paper.pdf -o cards/<slug>
    python scripts/extract_cards.py paper.pdf -o cards/<slug> --backend openai --base-url http://localhost:8080/v1 --model <name> --ref smith-2020

Steps: split the PDF into numbered pages (scripts/pdf_to_pages.py), ask the model for claims with quotes (long documents in
overlapping page windows), snap each quote to the exact words of its page (scripts/snap_quotes.py), drop any that cannot be found,
and write `cards.yaml`. Every card has status `unverified`: the quote is real, but nobody has yet read whether the paraphrase is
fair to it. Run scripts/check_quotes.py on the result, then have a person or a second pass read the claims against their quotes
before any is marked `verified` and drawn.

Any model will do (see scripts/llm.py and docs/SETUP.md): a local server or a hosted service, chosen with --backend, --base-url and
--model or the LLM_* environment variables. A model with a small context window needs a smaller --window-words (about 3000 for 8k).
Test the connection first with `python scripts/llm.py --ping`.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_quotes import load_pages  # noqa: E402
from llm import add_arguments, chat, settings, LLMError  # noqa: E402
from snap_quotes import snap_claim  # noqa: E402

KINDS = ["background", "method", "result", "interpretation", "caveat", "argument", "practice", "future_research"]
WINDOW_WORDS = 14000  # words of page text per model call; a longer document is read in overlapping windows

PROMPT = """Read this document and extract its key claims so a cartoonist can draw them accurately.

Return JSON: {{"claims": [{{"page": <int, the PAGE number the quote is on>, "quote": "<an EXACT contiguous run of 8 to 30 words copied from that page; no changes, no ellipses>", "kind": "<one of {kinds}>", "paraphrase": "<one plain-English sentence in your own words, keeping the authors' hedges>"}}]}}

Rules: copy quotes character for character from one page; never join text from different pages; give claims in reading order; at most 40 claims for these pages; include the authors' own cautions and limitations; use kind "future_research" for any sentence where the authors say what research or practice is still needed, and quote it exactly; do not invent.

TEXT:
{body}"""


def windows(pages, window_words=WINDOW_WORDS):
    """Split {page: text} into lists of page numbers of about window_words words, overlapping by one page."""
    nums, out, cur, size = sorted(pages), [], [], 0
    for n in nums:
        w = len(pages[n].split())
        if cur and size + w > window_words:
            out.append(cur)
            cur, size = [cur[-1]], len(pages[cur[-1]].split())
        cur.append(n)
        size += w
    if cur:
        out.append(cur)
    return out


def parse_claims(text):
    """The claims list from the model's JSON, salvaging the complete entries if the reply was cut off."""
    try:
        return json.loads(text)["claims"]
    except (ValueError, KeyError):
        cut = text.rfind("},")
        return json.loads(text[:cut + 1] + "]}")["claims"] if cut > 0 else []


def extract(pages, ref, ask_fn, min_ratio=0.75, window_words=WINDOW_WORDS):
    """Return (cards, stats) from the pages using ask_fn(prompt) -> model reply text."""
    cards, seen, stats = [], set(), {"asked": 0, "exact": 0, "snapped": 0, "dropped": 0, "duplicate": 0}
    for window in windows(pages, window_words):
        body = "\n".join(f"=== PAGE {n} ===\n{pages[n]}" for n in window)
        for c in parse_claims(ask_fn(PROMPT.format(kinds=" | ".join(KINDS), body=body))):
            stats["asked"] += 1
            page, quote = c.get("page"), c.get("quote", "")
            if not isinstance(page, int) or not quote or c.get("kind") not in KINDS:
                stats["dropped"] += 1
                continue
            found_page, exact, ratio = snap_claim(pages, page, quote, min_ratio)
            if exact is None:
                stats["dropped"] += 1
                continue
            norm = " ".join(exact.lower().split())
            if any(pg == found_page and (norm in s or s in norm) for pg, s in seen):  # the same sentence, or one inside the other
                stats["duplicate"] += 1
                continue
            seen.add((found_page, norm))
            stats["exact" if ratio == 1.0 and exact == quote else "snapped"] += 1
            cards.append({"text": c.get("paraphrase", "").strip(), "kind": c["kind"], "source": {"locator": f"page {found_page}", "page": found_page, "quote": " ".join(exact.split()), "ref": ref},
                          "status": "unverified", "note": "model-extracted; the quote is exact, the paraphrase has not been read against it"})
    cards.sort(key=lambda c: c["source"]["page"])
    for i, c in enumerate(cards, 1):
        c["id"] = f"C{i}"
    cards = [{"id": c["id"], **{k: v for k, v in c.items() if k != "id"}} for c in cards]
    return cards, stats


def run_one(pdf, out, args):
    out.mkdir(parents=True, exist_ok=True)
    if not (out / "pages").is_dir():
        subprocess.run([sys.executable, str(Path(__file__).with_name("pdf_to_pages.py")), str(pdf), "-o", str(out)], check=True, capture_output=True)
    pages = load_pages(out / "pages")
    cfg = settings(args.backend, args.base_url, args.model)
    ask = lambda p: chat(p, cfg, temperature=0.1, max_tokens=args.max_tokens, num_ctx=args.num_ctx)  # noqa: E731
    cards, stats = extract(pages, args.ref or Path(pdf).stem, ask, args.min_ratio, args.window_words)
    (out / "cards.yaml").write_text(yaml.dump({"claims": cards}, sort_keys=False, width=100, allow_unicode=True))
    return len(cards), len(pages), stats


def safe_name(name):
    return "".join(ch if ch.isalnum() else "-" for ch in Path(name).stem.lower()).strip("-")[:60] or "doc"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("pdf", help="a PDF, or a folder of PDFs (each is checked by intake_check first and skipped if it is scanned, a reference list or a fragment)")
    ap.add_argument("-o", "--out", required=True, help="folder for pages/ and cards.yaml")
    add_arguments(ap, model_help="the model that drafts the cards")
    ap.add_argument("--window-words", type=int, default=WINDOW_WORDS, help="words of page text per model call (default %(default)s; about 3000 suits an 8k-token context)")
    ap.add_argument("--max-tokens", type=int, default=16000, help="the longest reply to ask for (default %(default)s)")
    ap.add_argument("--num-ctx", type=int, default=32768, help="context size to request from Ollama (ignored by other backends)")
    ap.add_argument("--ref", default="")
    ap.add_argument("--min-ratio", type=float, default=0.75)
    args = ap.parse_args(argv)
    try:
        settings(args.backend, args.base_url, args.model)
    except LLMError as e:
        sys.exit(str(e))
    src, out = Path(args.pdf), Path(args.out)
    if not src.is_dir():
        n, pages, stats = run_one(src, out, args)
        print(f"{n} cards from {pages} pages: {stats}")
        return 0
    from intake_check import assess, pdf_info
    rows = []
    for f in sorted(src.rglob("*.pdf")):
        text, pages = pdf_info(f)
        info = assess(text, pages)
        skip = [fl for fl in info["flags"] if fl in ("scanned", "reference-list", "fragment")]
        if skip:
            rows.append((f.name, pages, "skipped", ",".join(skip), ""))
            print(f"skip {f.name}: {skip}")
            continue
        try:
            n, npages, stats = run_one(f, out / safe_name(f.name), args)
            rows.append((f.name, pages, "cards", n, str(stats)))
            print(f"{f.name}: {n} cards {stats}", flush=True)
        except Exception as e:  # keep going: one bad PDF must not stop a batch
            rows.append((f.name, pages, "error", str(e)[:80], ""))
            print(f"error {f.name}: {e}", flush=True)
    (out / "report.tsv").write_text("\n".join("\t".join(map(str, r)) for r in rows) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
