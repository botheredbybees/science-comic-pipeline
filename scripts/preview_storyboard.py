#!/usr/bin/env python3
"""Turn a storyboard YAML file into a readable HTML page.

The page shows the panels in order (as a sideways strip or a vertical stack, switchable),
each with its scene, dialogue, joke note and the claims it relies on, then the claims
ledger and the list of what the comic leaves out. It is a reading aid, not a renderer.

    python scripts/preview_storyboard.py examples/akam-2026-cartooning/storyboard.yaml -o output/preview.html
"""
import argparse
import sys
from html import escape as e
from pathlib import Path

import yaml

STATUS_GLYPH = {"verified": "✓", "abstract_only": "!", "unverified": "?"}

CSS = """
/* Layout: a header with the story spine, a toolbar, one strip or stack of panels, then the claims ledger. */
:root {
  --bg: #F5F7FA; --surface: #FFFFFF; --ink: #1C2330; --muted: #566174; --line: #D3D9E2;
  --accent: #2B5BD7; --accent-soft: #E4EBFB; --ok: #1B7447; --ok-soft: #E1F2E9;
  --warn: #8F5A00; --warn-soft: #FBEFD5;
  --hand: "Patrick Hand", "Comic Sans MS", "Segoe Print", cursive;
  --sans: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #11151B; --surface: #19202A; --ink: #E5E9F0; --muted: #9AA5B6; --line: #2C3644;
    --accent: #8FADF6; --accent-soft: #212C46; --ok: #6FCB9A; --ok-soft: #17301F;
    --warn: #E5B35E; --warn-soft: #382A10; color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #11151B; --surface: #19202A; --ink: #E5E9F0; --muted: #9AA5B6; --line: #2C3644;
  --accent: #8FADF6; --accent-soft: #212C46; --ok: #6FCB9A; --ok-soft: #17301F;
  --warn: #E5B35E; --warn-soft: #382A10; color-scheme: dark;
}
body { background: var(--bg); color: var(--ink); font-family: var(--sans); font-size: 15px; line-height: 1.5;
  padding-block: 28px 64px; padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.wrap { max-width: 1180px; margin: 0 auto; display: grid; gap: 28px; }
h1, h2, h3 { text-wrap: balance; margin: 0; line-height: 1.2; }
h1 { font-family: var(--hand); font-size: clamp(2rem, 5vw, 2.8rem); font-weight: 400; }
h2 { font-size: 1.05rem; font-weight: 650; }
a { color: var(--accent); }
.muted { color: var(--muted); }
.label { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

header { display: grid; gap: 14px; }
.source { font-size: .9rem; color: var(--muted); max-width: 70ch; }
.spine { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
.spine div { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 12px 14px; min-width: 0; }
.spine b { display: block; font-family: var(--hand); font-size: 1.25rem; font-weight: 400; color: var(--accent); }
.spine p { margin: 2px 0 0; font-size: .9rem; }
.facts { display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: .9rem; }
.facts span b { font-variant-numeric: tabular-nums; }

.toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 10px 16px; }
.seg { display: inline-flex; border: 1px solid var(--line); border-radius: 6px; overflow: hidden; background: var(--surface); }
.seg button, .nav button { font: inherit; border: 0; background: transparent; color: var(--ink); padding: 7px 14px; cursor: pointer; }
.seg button[aria-pressed="true"] { background: var(--accent); color: var(--bg); font-weight: 600; }
.nav { display: inline-flex; gap: 6px; }
.nav button { border: 1px solid var(--line); border-radius: 6px; background: var(--surface); padding: 7px 12px; }
.legend { font-size: .82rem; color: var(--muted); display: inline-flex; gap: 14px; align-items: center; flex-wrap: wrap; }
.sw { display: inline-block; width: 26px; height: 16px; vertical-align: -3px; margin-right: 5px; }
.sw.out { border: 2px solid var(--ink); border-radius: 255px 15px 225px 15px / 15px 225px 15px 255px; }
.sw.bare { border: 2px dashed var(--line); border-radius: 4px; }

.flow { display: flex; gap: 16px; align-items: stretch; }
.flow[data-layout="strip"] { overflow-x: auto; scroll-snap-type: x proximity; padding-bottom: 14px; }
.flow[data-layout="stack"] { flex-direction: column; max-width: 640px; }
.pagemark { flex: 0 0 auto; writing-mode: vertical-rl; transform: rotate(180deg); font-family: var(--hand); font-size: 1.3rem;
  color: var(--accent); padding: 6px 2px; align-self: stretch; text-align: center; }
.flow[data-layout="stack"] .pagemark { writing-mode: horizontal-tb; transform: none; text-align: left; border-bottom: 1px solid var(--line); padding: 14px 0 6px; }
.panel { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 14px; display: grid;
  gap: 12px; align-content: start; scroll-snap-align: start; min-width: 0; }
.flow[data-layout="strip"] .panel { flex: 0 0 min(330px, 84vw); }
.phead { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; }
.pid { font-family: var(--mono); font-size: .8rem; color: var(--muted); }
.act { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; font-weight: 600; color: var(--accent); }
.frame { padding: 16px; min-height: 120px; display: grid; align-content: center; }
.frame.outlined { border: 2.5px solid var(--ink); border-radius: 255px 16px 225px 16px / 16px 225px 16px 255px; }
.frame.borderless { border: 2px dashed var(--line); border-radius: 4px; }
.scene { margin: 0; font-style: italic; color: var(--muted); font-size: .9rem; }
.speech { display: grid; gap: 8px; }
.line { font-family: var(--hand); font-size: 1.22rem; line-height: 1.3; overflow-wrap: anywhere; }
.line .who { font-family: var(--sans); font-size: .7rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); display: block; }
.line.think { font-style: italic; }
.line.think .t::before { content: "\\201C"; } .line.think .t::after { content: "\\201D"; }
.line.caption { background: var(--accent-soft); border: 1px solid var(--line); border-radius: 3px; padding: 8px 10px; }
.joke { background: var(--warn-soft); color: var(--ink); border-radius: 4px; padding: 7px 9px; font-size: .84rem; }
.joke b { color: var(--warn); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { font-family: var(--mono); font-size: .76rem; padding: 2px 8px; border-radius: 999px; text-decoration: none; border: 1px solid transparent; }
.chip.verified { background: var(--ok-soft); color: var(--ok); }
.chip.abstract_only, .chip.unverified { background: var(--warn-soft); color: var(--warn); }
.chip:hover { border-color: currentColor; }

section.ledger, section.leftout { display: grid; gap: 12px; }
.claims { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 420px), 1fr)); gap: 12px; }
.claim { background: var(--surface); border: 1px solid var(--line); border-radius: 6px; padding: 12px 14px; display: grid; gap: 6px; min-width: 0; scroll-margin-top: 16px; }
.claim:target { border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent-soft); }
.claim p { margin: 0; }
.chead { display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; }
.kind { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.src { font-family: var(--mono); font-size: .78rem; color: var(--muted); overflow-wrap: anywhere; }
.note { background: var(--warn-soft); border-radius: 4px; padding: 7px 9px; font-size: .86rem; }
.used { font-size: .82rem; color: var(--muted); }
.used a { font-family: var(--mono); }
ul.out { margin: 0; padding-left: 1.2rem; display: grid; gap: 6px; max-width: 78ch; }
@media (prefers-reduced-motion: no-preference) { .flow[data-layout="strip"] { scroll-behavior: smooth; } }
"""

JS = """
(function () {
  var flow = document.getElementById('flow');
  var btns = document.querySelectorAll('[data-set-layout]');
  function set(l) {
    flow.setAttribute('data-layout', l);
    btns.forEach(function (b) { b.setAttribute('aria-pressed', String(b.getAttribute('data-set-layout') === l)); });
    document.getElementById('nav').hidden = (l !== 'strip');
    try { localStorage.setItem('storyboard-layout', l); } catch (e) {}
  }
  var saved = null;
  try { saved = localStorage.getItem('storyboard-layout'); } catch (e) {}
  set(saved || (window.innerWidth >= 800 ? 'strip' : 'stack'));
  btns.forEach(function (b) { b.addEventListener('click', function () { set(b.getAttribute('data-set-layout')); }); });
  document.querySelectorAll('[data-scroll]').forEach(function (b) {
    b.addEventListener('click', function () { flow.scrollBy({ left: Number(b.getAttribute('data-scroll')) * 346, behavior: 'smooth' }); });
  });
})();
"""


def _claim_chip(cid, claims):
    status = claims[cid]["status"]
    return (f'<a class="chip {e(status)}" href="#claim-{e(cid)}" '
            f'title="{e(claims[cid]["kind"])}, {e(status)}">{STATUS_GLYPH[status]} {e(cid)}</a>')


def _panel(p, claims):
    parts = [f'<article class="panel" id="panel-{e(p["id"])}">',
             f'<div class="phead"><span class="pid">{e(p["id"])}</span><span class="act">{e(p["act"])}</span></div>',
             f'<div class="frame {e(p.get("frame", "outlined"))}"><p class="scene">{e(p["scene"])}</p></div>']
    if p.get("speech"):
        parts.append('<div class="speech">')
        for s in p["speech"]:
            kind = s.get("kind", "say")
            who = "" if s["speaker"] == "narrator" and kind == "caption" else f'<span class="who">{e(s["speaker"])}</span>'
            parts.append(f'<div class="line {e(kind)}">{who}<span class="t">{e(s["text"])}</span></div>')
        parts.append("</div>")
    if p.get("humour"):
        h = p["humour"]
        mark = " Reviewed: keeps the claims intact." if h.get("keeps_claims_intact") else " Not yet reviewed."
        parts.append(f'<div class="joke"><b>Joke.</b> {e(h["note"])}<span class="muted">{e(mark)}</span></div>')
    if p.get("claim_ids"):
        parts.append('<div class="chips">' + "".join(_claim_chip(c, claims) for c in p["claim_ids"]) + "</div>")
    parts.append("</article>")
    return "".join(parts)


def build(doc, standalone=False):
    claims = {c["id"]: c for c in doc["claims"]}
    panels = [p for page in doc["pages"] for p in page["panels"]]
    used = {}
    for p in panels:
        for cid in p.get("claim_ids", []):
            used.setdefault(cid, []).append(p["id"])
    meta, src = doc["meta"], doc["meta"]["source"]
    n_ver = sum(c["status"] == "verified" for c in doc["claims"])
    n_joke = sum("humour" in p for p in panels)

    out = [f'<title>{e(meta["title"])} Storyboard</title>',
           '<meta name="claude:viewport-fit-sides" content="cover">',
           '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;650&family=Patrick+Hand&family=IBM+Plex+Mono&display=swap">',
           f"<style>{CSS}</style>", '<div class="wrap">']
    spine = meta["spine"]
    out.append(
        f'<header><span class="label">Storyboard</span><h1>{e(meta["title"])}</h1>'
        f'<p class="source">From <i>{e(src["title"])}</i> by {e(", ".join(src["authors"]))} ({src["year"]}). '
        f'Licence: {e(src["licence"])}.'
        + (f' <a href="{e(src["url"])}">Read the paper</a>.' if src.get("url") else "")
        + "</p>"
        f'<div class="spine"><div><b>And</b><p>{e(spine["and"])}</p></div>'
        f'<div><b>But</b><p>{e(spine["but"])}</p></div><div><b>Therefore</b><p>{e(spine["therefore"])}</p></div></div>'
        f'<p class="facts"><span><b>{len(panels)}</b> panels on <b>{len(doc["pages"])}</b> pages</span>'
        f'<span><b>{len(doc["claims"])}</b> claims, <b>{n_ver}</b> verified</span><span><b>{n_joke}</b> jokes</span></p></header>')
    out.append(
        '<div class="toolbar"><div class="seg" role="group" aria-label="Layout">'
        '<button type="button" data-set-layout="strip" aria-pressed="false">Sideways strip</button>'
        '<button type="button" data-set-layout="stack" aria-pressed="false">Vertical stack</button></div>'
        '<div class="nav" id="nav"><button type="button" data-scroll="-1" aria-label="Previous panel">‹</button>'
        '<button type="button" data-scroll="1" aria-label="Next panel">›</button></div>'
        '<span class="legend"><span><i class="sw out"></i>outlined panel</span><span><i class="sw bare"></i>borderless panel</span></span></div>')
    out.append('<div class="flow" id="flow" tabindex="0" aria-label="Panels in reading order">')
    for page in doc["pages"]:
        out.append(f'<div class="pagemark">{e(page["id"])} · {e(page.get("title", ""))}</div>')
        out.extend(_panel(p, claims) for p in page["panels"])
    out.append("</div>")

    out.append('<section class="ledger"><h2>Claims ledger</h2><p class="muted">Every fact in a panel traces to one of these, and each one to the paper.</p><div class="claims">')
    for c in doc["claims"]:
        q = f' “{e(c["source"]["quote"])}”' if c["source"].get("quote") else ""
        uses = ", ".join(f'<a href="#panel-{e(i)}">{e(i)}</a>' for i in used.get(c["id"], [])) or "no panel"
        note = f'<div class="note">{e(c["note"])}</div>' if c.get("note") else ""
        out.append(
            f'<article class="claim" id="claim-{e(c["id"])}"><div class="chead">'
            f'<span class="chip {e(c["status"])}">{STATUS_GLYPH[c["status"]]} {e(c["id"])} {e(c["status"])}</span>'
            f'<span class="kind">{e(c["kind"])}</span></div><p>{e(c["text"])}</p>'
            f'<div class="src">{e(c["source"]["locator"])}{q}</div>{note}<div class="used">Used in: {uses}</div></article>')
    out.append("</div></section>")

    if meta.get("left_out"):
        out.append('<section class="leftout"><h2>Left out of this draft</h2><ul class="out">'
                   + "".join(f"<li>{e(t)}</li>" for t in meta["left_out"]) + "</ul></section>")
    out.append(f"</div><script>{JS}</script>")

    body = "\n".join(out)
    if standalone:
        return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>{body}</body></html>'
    return body


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("storyboard")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--standalone", action="store_true", help="wrap in a full HTML document")
    args = ap.parse_args(argv)
    doc = yaml.safe_load(Path(args.storyboard).read_text())
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(build(doc, standalone=args.standalone))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
