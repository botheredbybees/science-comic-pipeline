#!/usr/bin/env python3
"""Check the promotional text for a comic against its claims ledger, and write it out ready to post.

A comic folder may hold `PROMO.yaml`: an abstract, headline candidates and social posts, each naming the claims it
rests on. This script holds that text to the same rule as the panels: nothing in a post that a cited, verified claim
does not say, and no claim made stronger. It is the machine half of the `promote` skill.

    python scripts/check_post.py examples/<slug>                 # check; exit 1 on errors
    python scripts/check_post.py examples/<slug> --write         # also write PROMO.md (copy-and-paste text, with each post's evidence)
    python scripts/check_post.py examples/<slug> --strict        # warnings and unapproved items fail too

PROMO.yaml
    version: 1
    link: "https://.../<slug>.pdf"          # where the full comic lives (omit for a comic with no public link)
    overview: "https://.../<slug>-overview.pdf"   # optional: the one-page version
    abstract: { text: "100 to 150 words", claims: [C1, C5], approved: false }
    headlines:
      - { text: "...", claims: [C5], format: "question" }
    posts:
      - { id: P1, kind: micro, type: reframe, text: "<= 280 characters", claims: [C5], panel: B2.4, link: true, approved: false }
      - { id: P2, kind: long,  type: lens,    text: "<= 1200 characters", claims: [C6, C9] }

Errors (a post must not go out like this)
    a private comic (nothing private is promoted); a claim that does not exist or is not `verified`; no claim cited;
    a number (digit or number word) that no cited claim contains; a claim made stronger ("proves", "breakthrough");
    engagement bait ("What's your take?", "Read on to find out"); a length limit broken (abstract 100 to 150 words,
    micro 280 characters, long 1200, counting a link as 24); a post that leans on a panel whose joke is not approved.
Warnings (read them; fix unless you can say why not)
    a hedge in a cited claim that the post drops; a quantifier ("most", "many", "often") or absolute ("all", "never") the
    claims do not use; a causal word ("causes", "because") the claims do not use; a post that opens with "This" or "It" and
    so cannot stand alone; stock phrases ("changes everything", "That's not X, it's Y", "delve").
PROMO.md carries the credit line (authors, year, DOI, licence) to put in or under every post, so the posts need not name the paper.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_storyboard  # noqa: E402
from validate_storyboard import PLAIN_NUMBER, WORDS, _norm, _supported_numbers  # noqa: E402

LINK_CHARS = 24          # a link costs this much in a post on the common platforms
LIMITS = {"micro": 280, "long": 1200}
ABSTRACT_WORDS = (100, 150)

HEDGES = ("approximately", "about", "around", "roughly", "nearly", "almost", "less than", "more than", "at least", "up to",
          "may", "might", "could", "suggest", "suggests", "suggested", "likely", "possibly", "potentially", "probably",
          "appear", "appears", "seem", "seems", "similar", "not all", "some", "in this study", "in the study", "in these")
QUANTIFIERS = ("most", "many", "majority", "few", "some", "several", "often", "usually", "typically", "rarely", "mostly",
               "generally", "frequently")
ABSOLUTES = ("all", "every", "always", "never", "none", "nobody", "everyone", "entire", "entirely", "completely", "totally",
             "definitely", "clearly", "obviously", "everything", "nothing", "only")
CAUSAL = ("causes", "caused", "causing", "because", "leads to", "led to", "drives", "driven by", "due to", "results in",
          "resulted in", "responsible for", "thanks to")
OVERCLAIM = re.compile(r"\b(prove[sd]?|proven|proof|revolution\w*|breakthrough|game[- ]?chang\w*|ground[- ]?breaking|"
                       r"shocking|stunning|miracle|solves?|solved|cure[sd]?|first[- ]ever|world[- ]first|unprecedented)\b", re.I)
BAIT = re.compile(r"(what'?s your (take|view|thought)|drop a comment|let me know in the comments|(^|[.!?]\s)(thoughts|agree)\?|"
                  r"read on\b|keep reading|find out (why|how|what)|you won'?t believe|link in (bio|the comments)|"
                  r"follow (me )?for more|don'?t miss|stay tuned|click (here|the link)|\bRT if\b|please share|like and share|"
                  r"\bthread\b.{0,6}(below|follows)|🧵)", re.I)
STOCK = re.compile(r"(changes everything|full stop\b|end of story|that'?s the shape of it|"
                   r"\b(it'?s|it is|that'?s|that is|this is) not\b[^.;!?]{1,70}?[,—–-]+\s*(it'?s|it is|that'?s|that is|this is|but)\b|"
                   r"\b(delve|tapestry|realm|unlock(s|ing)?|dive into|deep dive|in today'?s|fascinating|exciting|incredible|"
                   r"amazing|remarkable)\b|\bimagine\b|here'?s (what|why|how|the)|did you know|what if i told you|"
                   r"discover how|ever wondered)", re.I)
OPENERS = re.compile(r"^\W*(this|these|that|those|it|they|here)\b", re.I)


def _words(text):
    return re.findall(r"[A-Za-z0-9'’%.-]+", text)


def _has(text, phrases):
    """The phrases (whole words or phrases) that appear in `text`."""
    low = text.lower()
    return [p for p in phrases if re.search(r"(?<![a-z])" + re.escape(p) + r"(?![a-z])", low)]


def _claim_text(c):
    q = ((c.get("source") or {}).get("quote")) or ""
    return f'{c.get("text", "")} {q}'


def load(folder):
    """(promo, doc, ledger): the PROMO.yaml, the comic's built storyboard document, and every ledger claim by id."""
    folder = Path(folder)
    promo = yaml.safe_load((folder / "PROMO.yaml").read_text()) or {}
    doc, _, _, _ = build_storyboard.build(folder)
    ledger = {}
    for f in sorted(folder.glob("claims*.yaml")) + sorted((folder / "claims").glob("*.yaml")):
        for c in (yaml.safe_load(f.read_text()) or {}).get("claims", []):
            ledger[c["id"]] = c
    return promo, doc, ledger


def _items(promo):
    """Every piece of text to check: (label, kind, item)."""
    out = []
    if promo.get("abstract"):
        out.append(("abstract", "abstract", promo["abstract"]))
    for i, h in enumerate(promo.get("headlines") or [], 1):
        out.append((f"headline {i}", "headline", h))
    for p in promo.get("posts") or []:
        out.append((f'post {p.get("id", "?")}', p.get("kind", "micro"), p))
    return out


def check_item(label, kind, item, ledger, panels, has_link, n_sources=1):
    """(errors, warnings) for one piece of text. A comic drawn from several papers may count them."""
    errs, warns = [], []
    text = (item.get("text") or "").strip()
    if not text:
        return [f"{label}: no text"], warns
    ids = item.get("claims") or []
    if not ids:
        errs.append(f"{label}: cites no claim (every sentence of a post rests on a claim)")
    cited = []
    for cid in ids:
        c = ledger.get(cid)
        if c is None:
            errs.append(f"{label}: claim {cid} is not in the ledger")
        elif c.get("status") != "verified":
            errs.append(f"{label}: claim {cid} is {c.get('status')}, not verified")
        else:
            cited.append(c)
    support = " ".join(_claim_text(c) for c in cited)

    # numbers: a figure, a count in words, a percentage
    supported = _supported_numbers(support)
    if n_sources > 1:
        supported.add(str(n_sources))
    seen = set()
    for n in PLAIN_NUMBER.findall(_norm(text)):
        if n not in supported and n not in seen:
            seen.add(n)
            errs.append(f"{label}: the number {n} is in no cited claim ({', '.join(ids) or 'none cited'})")
    for w in re.findall(r"[a-z]+", text.lower()):
        n = WORDS.get(w)
        if n and w not in ("one", "single") and n not in supported and w not in seen:
            seen.add(w)
            errs.append(f"{label}: the count '{w}' is in no cited claim ({', '.join(ids) or 'none cited'})")

    # a claim made stronger, and engagement bait
    for m in OVERCLAIM.finditer(text):
        if m.group(0).lower() not in support.lower():
            errs.append(f"{label}: '{m.group(0)}' claims more than a paper does")
    for m in BAIT.finditer(text):
        errs.append(f"{label}: engagement bait '{m.group(0)}': the post should land on its own substance")

    # hedges, quantifiers, absolutes, cause
    claim_hedges = _has(support, HEDGES)
    if claim_hedges and not _has(text, HEDGES):
        warns.append(f"{label}: the cited claims hedge ({', '.join(claim_hedges[:4])}) and the post does not")
    for kw, words in (("a quantifier", QUANTIFIERS), ("an absolute", ABSOLUTES), ("a causal word", CAUSAL)):
        for w in _has(text, words):
            if w not in _has(support, words):
                warns.append(f"{label}: '{w}' ({kw}) is not in any cited claim: check the claim says so")
    for m in STOCK.finditer(text):
        warns.append(f"{label}: stock phrase '{m.group(0).strip()}'")
    if kind in ("micro", "long") and OPENERS.match(text):
        warns.append(f"{label}: opens with a pronoun, so it cannot stand alone")

    # length
    if kind == "abstract":
        n = len(_words(text))
        if not ABSTRACT_WORDS[0] <= n <= ABSTRACT_WORDS[1]:
            errs.append(f"{label}: {n} words, should be {ABSTRACT_WORDS[0]} to {ABSTRACT_WORDS[1]}")
    elif kind in LIMITS:
        n = len(text) + (LINK_CHARS + 1 if item.get("link") else 0)
        if n > LIMITS[kind]:
            errs.append(f"{label}: {n} characters, the limit for a {kind} post is {LIMITS[kind]}")
        if item.get("link") and not has_link:
            errs.append(f"{label}: asks for a link but PROMO.yaml has no `link`")
    elif kind == "headline" and len(text) > 100:
        warns.append(f"{label}: {len(text)} characters, a headline should be about 100 or fewer")

    # the panel it leans on
    pid = item.get("panel")
    if pid:
        p = panels.get(pid)
        if p is None:
            errs.append(f"{label}: panel {pid} does not exist")
        elif "humour" in p and not p["humour"].get("keeps_claims_intact"):
            errs.append(f"{label}: panel {pid} carries a joke that is not approved yet")
    return errs, warns


def check(promo, doc, ledger):
    """(errors, warnings) for a whole PROMO.yaml."""
    errs, warns = [], []
    meta = doc["meta"]
    if meta.get("private"):
        return ["this comic is private (meta.private): nothing private is promoted"], warns
    panels = {p["id"]: p for b in doc["beats"] for p in b["panels"]}
    items = _items(promo)
    n_sources = len(meta.get("sources") or [])
    if not items:
        return ["PROMO.yaml has no abstract, headlines or posts"], warns
    seen = {}
    for label, kind, item in items:
        if kind not in ("abstract", "headline", "micro", "long"):
            errs.append(f"{label}: kind '{kind}' is not micro or long")
            continue
        e, w = check_item(label, kind, item, ledger, panels, bool(promo.get("link")), n_sources)
        errs += e
        warns += w
        t = " ".join((item.get("text") or "").lower().split())
        if t in seen:
            errs.append(f"{label}: the same text as {seen[t]}")
        seen[t] = label
    if not promo.get("link"):
        warns.append("PROMO.yaml has no `link` to the full comic")
    return errs, warns


def _surname(author):
    return author.split()[-1] if author else ""


def credit_line(meta):
    """The attribution to post with the comic."""
    srcs = [meta["source"]] if meta.get("source") else list(meta.get("sources") or [])
    bits = []
    for s in srcs:
        a = s.get("authors") or []
        who = f"{_surname(a[0])} et al." if len(a) > 1 else (_surname(a[0]) if a else "")
        bits.append(f"{who} ({s.get('year')}) doi:{s['doi']}" if s.get("doi") else f"{who} ({s.get('year')})")
    lic = sorted({s.get("licence", "") for s in srcs if s.get("licence")})
    return ("Comic adapted from " + "; ".join(bits) + (f", {', '.join(lic)}" if lic else "")
            + ". The papers' authors did not write or endorse it.")


def render_md(promo, doc, ledger):
    """PROMO.md: the text to copy, each item with its length, status and the evidence it rests on."""
    meta = doc["meta"]
    out = [f"# Promotion text: {meta['title']}", "",
           "Generated by `scripts/check_post.py --write` from `PROMO.yaml`: edit that, not this. "
           "Read each item against the quotes under it before posting; an item marked DRAFT has not been approved.", ""]
    if promo.get("link"):
        out += [f"**Full comic:** {promo['link']}"]
    if promo.get("overview"):
        out += [f"**One-page overview:** {promo['overview']}"]
    out += [f"**Credit line (put it in or under every post):** {credit_line(meta)}", ""]

    def block(label, kind, item):
        text = item["text"].strip()
        n = len(_words(text)) if kind == "abstract" else len(text) + (LINK_CHARS + 1 if item.get("link") else 0)
        unit = "words" if kind == "abstract" else "characters"
        status = "approved" if item.get("approved") else "DRAFT"
        head = f"### {label}" + (f" ({item.get('type')})" if item.get("type") else "") + f": {n} {unit}, {status}"
        lines = [head, "", *(f"> {ln}" if ln else ">" for ln in text.splitlines())]
        if item.get("link") and promo.get("link"):
            lines += [">", f"> {promo['link']}"]
        lines += ["", "Rests on:"]
        for cid in item.get("claims") or []:
            c = ledger.get(cid, {})
            s = c.get("source") or {}
            lines.append(f"- {cid}: “{(s.get('quote') or c.get('text', '')).strip()}”" + (f" (p. {s['page']})" if s.get("page") else ""))
        if item.get("panel"):
            lines.append(f"- picture: panel {item['panel']}")
        return lines + [""]

    if promo.get("abstract"):
        out += ["## Abstract", ""] + block("Abstract", "abstract", promo["abstract"])
    if promo.get("headlines"):
        out += ["## Headlines", ""]
        for i, h in enumerate(promo["headlines"], 1):
            out.append(f"{i}. {h['text'].strip()}" + (f"  *({h['format']}; {', '.join(h.get('claims') or [])})*" if h.get("format") else
                                                       f"  *({', '.join(h.get('claims') or [])})*"))
        out.append("")
    if promo.get("posts"):
        out += ["## Posts", ""]
        for p in promo["posts"]:
            out += block(p.get("id", "post"), p.get("kind", "micro"), p)
    return "\n".join(out).rstrip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("folder", help="a comic's working folder holding PROMO.yaml")
    ap.add_argument("--write", action="store_true", help="write PROMO.md beside PROMO.yaml (only when there are no errors)")
    ap.add_argument("--strict", action="store_true", help="warnings, and items not marked approved, also fail")
    args = ap.parse_args(argv)
    promo, doc, ledger = load(args.folder)
    errs, warns = check(promo, doc, ledger)
    if args.strict:
        errs += [f"{label}: not approved" for label, _, it in _items(promo) if not it.get("approved")]
    for e in errs:
        print("ERROR  ", e)
    for w in warns:
        print("warning", w)
    n = len(_items(promo))
    print(f"{n} items; {len(errs)} errors, {len(warns)} warnings")
    if args.write and not [e for e in errs if "not approved" not in e]:
        out = Path(args.folder) / "PROMO.md"
        out.write_text(render_md(promo, doc, ledger))
        print(f"wrote {out}")
    return 1 if errs or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
