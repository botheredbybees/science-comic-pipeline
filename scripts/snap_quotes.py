#!/usr/bin/env python3
"""Move a model's near-verbatim quotes onto the exact text of the page, and reject the ones that are not there.

A language model asked for a verbatim quote usually returns the right sentence with a citation dropped, a word tidied or a
line break healed, which fails scripts/check_quotes.py even though the sentence is real. `snap` finds the stretch of the page
that matches the quote best and returns that stretch exactly as the page has it, so it passes the check by construction. It
refuses (returns None) when fewer than `min_ratio` of the quote's words are found in order close together on the page, so an
invented quote is rejected, not repaired.

    from snap_quotes import snap
    exact, ratio = snap(page_text, "the model's quote")

What snapping cannot tell you is whether the claim's paraphrase is supported by the quote: that still needs a reader.
"""
import difflib
import re
import unicodedata

TOKEN = re.compile(r"[^\W_]+(?:\.\d+)?")


def snap(page_text, quote, min_ratio=0.75):
    """Return (exact span of page_text, match ratio), or (None, ratio) when the quote is not on the page."""
    text = unicodedata.normalize("NFKC", page_text)
    ptoks = [(m.group().lower(), m.start(), m.end()) for m in TOKEN.finditer(text)]
    qtoks = [m.group().lower() for m in TOKEN.finditer(unicodedata.normalize("NFKC", quote))]
    if len(qtoks) < 4 or not ptoks:
        return None, 0.0
    matcher = difflib.SequenceMatcher(None, qtoks, [t[0] for t in ptoks], autojunk=False)
    blocks = [b for b in matcher.get_matching_blocks() if b.size >= 2]
    if not blocks:
        return None, 0.0
    best = None
    for i in range(len(blocks)):  # the densest run of blocks that is not much wider than the quote
        for j in range(i, len(blocks)):
            start, end = blocks[i].b, blocks[j].b + blocks[j].size
            if end - start > 1.6 * len(qtoks) + 3:
                break
            matched = sum(b.size for b in blocks[i:j + 1])
            if best is None or matched > best[0] or (matched == best[0] and end - start < best[2] - best[1]):
                best = (matched, start, end)
    matched, start, end = best
    ratio = matched / len(qtoks)
    if ratio < min_ratio:
        return None, ratio
    return text[ptoks[start][1]:ptoks[end - 1][2]], ratio


def snap_claim(pages, page, quote, min_ratio=0.75):
    """Snap on the named page first, then on every other page. Return (page, exact quote, ratio) or (None, None, best ratio)."""
    order = ([page] if page in pages else []) + [n for n in pages if n != page]
    best = 0.0
    for n in order:
        span, ratio = snap(pages[n], quote, min_ratio)
        best = max(best, ratio)
        if span:
            return n, span, ratio
    return None, None, best
