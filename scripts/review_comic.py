#!/usr/bin/env python3
"""A review form for one comic's claims, jokes and panels, and a command that applies the answers.

    python scripts/review_comic.py build tortell --pages-dir sources/tortell-2023-st-chlf/pages -o output/review.html
    python scripts/review_comic.py build nester --pages-root sources --claims all --panels
    python scripts/review_comic.py apply tortell answers.json [--dry-run]

`build` writes one self-contained web page. Publish it as an Artifact with the `db` capability (the page saves each answer as it is given, one
document per item in the collection `review`) or open it in a browser, where the answers stay in that browser. Three kinds of item:

  * a **claim**: the claim, its quote and the page text around the quote (the quote marked), with three things to check; Fair / Reword / Drop;
  * a **joke**: the panel drawn, the lines that carry the joke, its note, and the six questions of skills/humour-pass (the last: it still lands if the reader skips the caption); Approve / Reword / Cut;
  * a **panel** (with `--panels`): the panel drawn, with its words and claims; OK / Fix / Redo.

`--claims` picks which claims are listed: `unverified` (the default: every ledger claim that is not `verified`), `cited` (the claims the
panels use) or `all`. Pages for the page text come from `--pages-dir` (one source) or `--pages-root` (a folder of `<source id>/pages`).

Every joke and panel also has a collapsed "Change the words, scene, characters, props or actions" block (each spoken line, to retype, remove or add; the scene text; each character's action, face,
facing and what they hold; each prop's kind and label, or remove it; one prop and one character to add). After Submit the page shows the
whole comic as it stands, with retyped words already in it (the page re-wraps captions, speech and labels in every copy of the panel; figures, props and scenes need `apply`). Every other word a picture draws (frame labels of a strip, titles, cards, prop labels) has a box too. `--no-comic` leaves the comic out.

`apply` reads the answers (a JSON file: item id to {verdict, notes, checks}; the list of documents the ArtifactData tool returns; or the folder it writes with `out_dir`) and does
only what is unambiguous: a claim marked Fair becomes `status: verified` in its ledger, and a joke marked Approve gets `keeps_claims_intact:
true`; picture changes are written into the panel's beat file (a line that is not a one-line `{ ... }` mapping goes on the worklist instead); the storyboard is rebuilt. Everything else (Reword, Drop, Cut, Fix, Redo, and every note) is printed as a worklist for a person or
Claude to act on, because it needs a rewrite. A verdict given with some of its checks unticked is applied but reported.
"""
import argparse
import glob
import json
import re
import sys
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "renderers" / "xkcd"))
import review_form as F  # noqa: E402
from check_quotes import load_pages  # noqa: E402
from jokes import load_jokes, pick, rebuild, set_confirmed  # noqa: E402

ROOT = HERE.parent
H = F.H

CLAIM_CHECKS = ["Every number, unit and hedge in the claim is in the quote",
                "The claim says no more than the quote: no stronger verb, no wider scope",
                "The quote is on the page, in the place, that the claim says"]
JOKE_CHECKS = ["Every number, unit and hedge is exactly as in the claim",
               "It is plainly the comic's own voice, not the paper's",
               "The butt is an organism, an instrument or the comic itself: not the authors or any people",
               "Every caveat keeps its full strength",
               "It would read as honest to the authors",
               "It still lands if the reader skips the caption (judge it from the picture and the speech)"]
PANEL_CHECKS = ["Nothing overlaps, touches or is cut off",
                "Each speech line comes from the figure it points at",
                "The picture shows what the caption says, and no more",
                "It reads at a glance"]


def item_id(kind, key):
    return f"{kind}-{key.replace('.', '_')}"


def ledger_files(folder):
    return sorted(glob.glob(str(folder / "claims*.yaml")) + glob.glob(str(folder / "claims" / "*.yaml")))


def load_ledger(folder):
    out = {}
    for f in ledger_files(folder):
        for c in (yaml.safe_load(Path(f).read_text()) or {}).get("claims", []):
            out[c["id"]] = c
    return out


def snippet(pages, page, quote, window=450):
    """HTML for the page text around a quote, the quote's words marked. Returns (html, found)."""
    text = (pages or {}).get(page)
    if not text:
        return "", False
    flat = re.sub(r"\s+", " ", text)
    hits = []
    for frag in [f.strip() for f in re.split(r"\s*(?:\.\.\.|…)\s*", quote or "") if f.strip()]:
        words = frag.split()
        # find the fragment allowing any whitespace between words
        m = re.search(r"\s+".join(re.escape(w) for w in words), flat, re.I)
        if m:
            hits.append((m.start(), m.end()))
    if not hits:
        return H.escape(flat[:2 * window]) + " ...", False
    a, b = min(h[0] for h in hits), max(h[1] for h in hits)
    lo, hi = max(0, a - window), min(len(flat), b + window)
    out, pos = [], lo
    for s, e in sorted(hits):
        out += [H.escape(flat[pos:s]), "<mark>", H.escape(flat[s:e]), "</mark>"]
        pos = e
    out.append(H.escape(flat[pos:hi]))
    return ("... " if lo else "") + "".join(out) + (" ..." if hi < len(flat) else ""), True


def claim_item(c, cited_by, pages):
    src = c.get("source") or {}
    page = src.get("page")
    snip, found = snippet(pages, page, src.get("quote", ""))
    pagebox = ""
    if snip:
        pagebox = f'<details><summary>Page {page} text around the quote{"" if found else " (quote not found in the page text)"}</summary><p>{snip}</p></details>'
    elif page:
        pagebox = f'<p class="meta">No page text loaded for page {page}.</p>'
    where = ", ".join(cited_by) if cited_by else "not cited by any panel yet"
    info = (f'<div class="info"><p class="claim">{H.escape(c["text"])}</p>'
            f'<blockquote>{H.escape(src.get("quote", "(no quote)"))}</blockquote>'
            f'<p class="meta">{H.escape(c.get("kind", ""))} &middot; status: {H.escape(c.get("status", ""))} &middot; page {page or "?"}, {H.escape(src.get("locator", ""))} &middot; cited by: {H.escape(where)}'
            + (f' &middot; note: {H.escape(c["note"])}' if c.get("note") else "") + f'</p>{pagebox}</div>')
    return {"id": item_id("claim", c["id"]), "name": c["id"], "variants": [], "checks": CLAIM_CHECKS, "info_html": info,
            "labels": {"keep": "Fair", "fix": "Reword", "drop": "Drop"}}


def panel_picture(panel_svgs, pid):
    got = panel_svgs.get(pid)
    if not got:
        return []
    svg, w, h = got
    # drawn about a third larger than on the page, so a panel can be read: a full-width panel gets the whole card, a narrow one stays narrow
    return [{"id": pid, "label": "as drawn", "svg": F.framed_svg(svg, f"Panel {pid}", int(w) + 4, int(h) + 4), "maxw": int(w * 1.35)}]


def words_html(panel):
    rows = []
    for s in panel.get("speech", []):
        who = "Caption" if s.get("kind") == "caption" else s["speaker"].title()
        rows.append(f'<p><b>{H.escape(who)}:</b> {H.escape(s["text"])}</p>')
    return "".join(rows)


def vocab():
    """The values the storyboard schema allows for a character's action, face, facing and holding, and for a prop's kind."""
    s = json.loads((ROOT / "schema" / "storyboard.schema.json").read_text())["$defs"]["staging"]["properties"]
    ch, pr = s["characters"]["items"]["properties"], s["props"]["items"]["properties"]
    return {"poses": ch["pose"]["enum"], "faces": ch["face"]["enum"], "facings": ch["facing"]["enum"], "holdings": ch["holding"]["enum"],
            "kinds": sorted(pr["kind"]["enum"])}


def edit_for(panel, doc):
    """What the 'change the picture' block needs for one panel: its scene, characters, props, the cast and the vocabulary."""
    names = {c["id"]: c["name"] for c in doc["cast"]}
    st = panel.get("staging") or {}
    chars = [{"name": names.get(c["id"], c["id"].title()), **{k: c.get(k, "") for k in ("pose", "face", "facing", "holding")}} for c in st.get("characters", [])]
    props = [{"kind": p["kind"], "label": p.get("label", "")} for p in st.get("props", [])]
    lines = [{"who": "Caption" if s.get("kind") == "caption" else names.get(s["speaker"], s["speaker"].title()), "text": s["text"]} for s in panel.get("speech", [])]
    texts = [{"path": "/".join(map(str, path)), "what": what, "text": text} for path, text, what in staging_texts(st)]
    return {"scene": panel.get("scene", ""), "lines": lines, "texts": texts, "characters": chars, "props": props, "cast": [{"id": c["id"]} for c in doc["cast"]], "vocab": vocab()}


def joke_item(j, panel_svgs, edit=None):
    lines = "".join(f'<p class="joke-lines">{n}. <b>{H.escape(l["speaker"].title())}:</b> {H.escape(l["text"])}</p>'
                    for n, l in enumerate(j["lines"], 1) if l.get("kind", "say") != "caption")
    caps = "".join(f'<p class="meta">Caption: {H.escape(l["text"])}</p>' for l in j["lines"] if l.get("kind") == "caption")
    claims = "".join(f'<p class="meta"><b>{c["id"]}</b> {H.escape(c["text"])}</p>' for c in j["claims"])
    note = j["humour"].get("note", "")
    info = f'<div class="info">{lines}{caps}<p class="meta">The note: {H.escape(note)}</p>{claims}</div>'
    return {"id": item_id("joke", j["panel"]), "name": f'{j["panel"]}: {j["beat"]}', "variants": panel_picture(panel_svgs, j["panel"]),
            "checks": JOKE_CHECKS, "info_html": info, "labels": {"keep": "Approve", "fix": "Reword", "drop": "Cut"}, "edit": edit, "panel": j["panel"]}


def panel_item(beat, p, claims, panel_svgs, edit=None):
    cl = "".join(f'<p class="meta"><b>{c}</b> {H.escape((claims.get(c) or {}).get("text", ""))}</p>' for c in p.get("claim_ids", []))
    info = f'<div class="info">{words_html(p)}{cl}</div>'
    return {"id": item_id("panel", p["id"]), "name": f'{p["id"]}: {beat.get("title", beat["id"])}', "variants": panel_picture(panel_svgs, p["id"]),
            "checks": PANEL_CHECKS, "info_html": info, "labels": {"keep": "OK", "fix": "Fix", "drop": "Redo"}, "edit": edit, "panel": p["id"]}


def render_panels(doc):
    """({panel id: (svg, width, height)} as the comic draws them, the page svgs of the whole comic)."""
    import render as R
    seen, orig = {}, R.draw_panel

    def spy(panel, plan, w, h, cast):
        svg = orig(panel, plan, w, h, cast)
        seen[panel["id"]] = (svg, w, h)
        return svg
    R.draw_panel = spy
    try:
        pages, _ = R.render_pages(doc)
    finally:
        R.draw_panel = orig
    return seen, pages


def comic_html(pages):
    """The whole comic, one figure per page; hidden until the review is submitted."""
    figs = "".join(f'<figure>{svg}</figure>' for svg in pages)
    return (f'<section id="comic" class="comic hide"><h2>The full comic</h2>'
            f'<p class="meta">As it stands now, with your changes not yet applied. {len(pages)} pages.</p><div class="pages">{figs}</div></section>')


def build(folder, name, pages_by_source, which="unverified", with_panels=False, beats=None, with_comic=True):
    doc = yaml.safe_load((folder / "storyboard.yaml").read_text())
    story_claims = {c["id"]: c for c in doc["claims"]}
    ledger = load_ledger(folder) or story_claims
    cited = {}
    for b in doc["beats"]:
        for p in b["panels"]:
            for cid in p.get("claim_ids", []):
                cited.setdefault(cid, []).append(p["id"])
    if which == "cited":
        pool = [ledger.get(c) or story_claims[c] for c in sorted(cited)]
    elif which == "all":
        pool = list(ledger.values())
    else:
        pool = [c for c in ledger.values() if c.get("status") != "verified"]
    jokes = [j for j in load_jokes(folder) if not j["confirmed"]]
    panel_svgs, comic_pages = render_panels(doc) if (jokes or with_panels or with_comic) else ({}, [])
    panels_by_id = {p["id"]: p for b in doc["beats"] for p in b["panels"]}
    groups = []
    if pool:
        items = []
        for c in pool:
            ref = (c.get("source") or {}).get("ref")
            pages = pages_by_source.get(ref) if ref else pages_by_source.get(None)
            items.append(claim_item(c, cited.get(c["id"], []), pages))
        groups.append((f"Claims ({which})", items))
    if jokes:
        groups.append(("Jokes waiting for a person", [joke_item(j, panel_svgs, edit_for(panels_by_id[j["panel"]], doc)) for j in jokes if j["panel"] in panels_by_id]))
    if with_panels:
        items = [panel_item(b, p, story_claims, panel_svgs, edit_for(p, doc)) for b in doc["beats"] if not beats or b["id"] in beats for p in b["panels"]]
        groups.append(("Panels", items))
    title = f"Review: {doc['meta'].get('title', name)}"
    intro = ("Judge each item as you read it; every answer saves as you go. Fair, Approve and OK are your sign-off: a Fair claim becomes verified in the ledger, "
             "an Approved joke is released. Reword, Drop, Cut, Fix and Redo, with what you want in the notes, go on a worklist for Claude.")
    short = " ".join(re.split(r"[?:]", doc["meta"].get("title", name))[0].split()[:5])
    return F.build_html(title, intro, groups, collection="review", tally_words=("ok", "to change", "rejected"), storage=f"review-comic-{name}",
                        page_title=f"Review: {short}", after_html=comic_html(comic_pages) if (with_comic and comic_pages) else "")


# ---------------------------------------------------------------- apply
def load_answers(path):
    """Answers from a JSON file, or from a folder of `<item id>.json` files (what ArtifactData's `out_dir` writes)."""
    if Path(path).is_dir():
        files = sorted(Path(path).rglob("*.json"))
        return {f.stem: json.loads(f.read_text()) for f in files}
    data = json.loads(Path(path).read_text())
    if isinstance(data, dict) and "documents" in data:
        data = data["documents"]
    if isinstance(data, list):
        data = {d.get("id") or d.get("doc_id"): (d.get("data") if isinstance(d.get("data"), dict) else d) for d in data}
    return data


def set_claim_status(folder, cid, status):
    """Set one claim's `status:` in place in whichever ledger holds it. Returns the file changed, or None."""
    for f in ledger_files(folder):
        text = Path(f).read_text()
        m = re.search(rf"(?m)^[ \t]*- id: {re.escape(cid)}\s*$", text)
        if not m:
            continue
        nxt = re.search(r"(?m)^[ \t]*- id: ", text[m.end():])
        end = m.end() + nxt.start() if nxt else len(text)
        block, n = re.subn(r"(?m)^([ \t]+status:) *\S+", rf"\1 {status}", text[m.start():end], count=1)
        if n:
            Path(f).write_text(text[:m.start()] + block + text[end:])
            return f
    return None


_BARE = re.compile(r"[A-Za-z][A-Za-z0-9_.\-]*")
_RESERVED = ("true", "false", "null", "yes", "no", "on", "off")


def flowval(v):
    """One value as YAML flow text, in the style of the beat files: bare words stay bare, other text is double-quoted."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "null"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return v if _BARE.fullmatch(v) and v.lower() not in _RESERVED else json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        return "[ " + ", ".join(flowval(x) for x in v) + " ]" if v else "[]"
    return "{ " + ", ".join(f"{k}: {flowval(x)}" for k, x in v.items()) + " }" if v else "{}"


def flow(d):
    """One mapping as a single-line YAML flow mapping, in the style of the beat files: `{ id: otto, x: 0.14, pose: sip }`."""
    return flowval(d)


def emit_block(d, ind):
    """A staging (or one frame of a split) as block YAML lines at `ind` spaces, as the beat files are written: scalars and short lists on one
    line, props and characters as one-line mappings, the frames of a split as block mappings."""
    pad, out = " " * ind, []
    for k, v in d.items():
        if isinstance(v, list) and v and all(isinstance(x, dict) for x in v):
            out.append(f"{pad}{k}:")
            for x in v:
                if any(key in x for key in ("props", "characters", "split")):  # a frame of a split
                    sub = emit_block(x, ind + 4)
                    out.append(f"{pad}  - {sub[0].lstrip()}")
                    out += sub[1:]
                else:
                    out.append(f"{pad}  - {flowval(x)}")
        else:
            out.append(f"{pad}{k}: {flowval(v)}")
    return out


TEXT_KEYS = ("label", "title", "unit", "x_label", "y_label", "caption")


def _texts_in(node, path, what, out):
    """Every drawn word under a prop: its label, title, unit, axis labels and captions, and those of its cards, items, notes and bars."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and k in TEXT_KEYS:
                out.append((path + (k,), v, f"{what} {k.replace('_', ' ')}"))
            elif isinstance(v, (list, dict)) and k != "staging":
                _texts_in(v, path + (k,), f"{what} {k.rstrip('s')}" if isinstance(v, list) else what, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _texts_in(v, path + (i,), f"{what} {i + 1}", out)


def staging_texts(st, prefix="", base=(), skip_top_labels=True):
    """[(path, text, what)] for every word a staging draws beyond its characters' speech: the label of each frame of a split, and the texts of
    its props (and of the frames' props). A top-level prop's `label` is left out when `skip_top_labels`, since the props row has its own box."""
    out = []
    n = len(st.get("split") or [])
    labels = st.get("split_labels") or []
    for i in range(n):
        out.append((base + ("split_labels", i), labels[i] if i < len(labels) else "", f"{prefix}Frame {i + 1} label"))
    for j, p in enumerate(st.get("props", [])):
        got = []
        _texts_in(p, base + ("props", j), f"{prefix}{p['kind']}", got)
        out += [g for g in got if not (skip_top_labels and not base and g[0][-1] == "label" and len(g[0]) == 3)]
    for i, sub in enumerate(st.get("split") or []):
        out += staging_texts(sub, f"Frame {i + 1}: ", base + ("split", i), skip_top_labels=False)
    return out


def set_path(root, path, value):
    """Set root[path...] = value; a split_labels list shorter than the path is padded with empty labels."""
    for key in path[:-1]:
        root = root.setdefault(key, []) if key == "split_labels" and isinstance(root, dict) else root[key]
    last = path[-1]
    if isinstance(root, list):
        while len(root) <= last:
            root.append("")
    root[last] = value


def staging_span(lines, i, j):
    """(line of `staging:`, first line after it) within the panel's lines i..j, or None when it has no staging."""
    for k in range(i, j):
        m = re.match(r"^(\s*)staging:\s*$", lines[k])
        if m:
            ind, e = len(m.group(1)), k + 1
            while e < j and not (lines[e].strip() and len(lines[e]) - len(lines[e].lstrip()) <= ind):
                e += 1
            return k, e
    return None


def apply_texts(folder, pid, texts, dry_run=False):
    """Change words in a panel's staging (a frame label, a prop's title, a board card...) by path, and write the staging back in the beat files' style.
    Returns (done, todo, changed)."""
    found = panel_lines(folder, pid)
    if not found:
        return [], [f"panel {pid}: word changes asked for but the panel was not found in the beat files: {json.dumps(texts, ensure_ascii=False)}"], False
    f, lines, i, j = found
    span = staging_span(lines, i, j)
    panel = next((p for beat in yaml.safe_load(f.read_text()) for p in beat["panels"] if p["id"] == pid), {})
    st = panel.get("staging")
    if not span or not st:
        return [], [f"panel {pid}: word changes asked for but it has no staging: {json.dumps(texts, ensure_ascii=False)}"], False
    done, todo = [], []
    for path_s, new in texts.items():
        path = tuple(int(x) if x.isdigit() else x for x in path_s.split("/"))
        try:
            old = st
            for key in path:
                old = old[key]
        except (KeyError, IndexError, TypeError):
            old = ""
        try:
            set_path(st, path, new)
        except (KeyError, IndexError, TypeError):
            todo.append(f"panel {pid}: change {path_s} to \"{new}\" (its place was not found)")
            continue
        done.append(f"{path_s}: \"{old}\" -> \"{new}\"")
    if done and not dry_run:
        k, e = span
        ind = len(re.match(r"^(\s*)", lines[k]).group(1)) + 2
        lines[k + 1:e] = [ln + "\n" for ln in emit_block(st, ind)]
        f.write_text("".join(lines))
    said = "would: " if dry_run else ""
    return [f"panel {pid}: {said}{d}" for d in done], todo, bool(done) and not dry_run


def panel_lines(folder, pid):
    """(file, its lines, first line of the panel, line after its last) for the panel `pid` in the beat files, or None."""
    for f in sorted((Path(folder) / "beats").glob("*.yaml")):
        lines = f.read_text().splitlines(keepends=True)
        for i, line in enumerate(lines):
            m = re.match(rf"^(\s*)- id:\s*{re.escape(pid)}\s*$", line)
            if m:
                ind, j = len(m.group(1)), i + 1
                while j < len(lines) and not (lines[j].strip() and len(lines[j]) - len(lines[j].lstrip()) <= ind):
                    j += 1
                return f, lines, i, j
    return None


FLOW_ITEM = re.compile(r"^(\s*)- (\{.*\})\s*$")


def apply_edit(folder, panel, pid, edit, dry_run=False):
    """Write one panel's requested picture changes (scene, characters, props, added props and characters) into its beat file.

    Returns (done, todo, changed): what was changed, what could not be (a line that is not a one-line flow mapping, a missing list) so a person must do it."""
    done, todo = [], []
    found = panel_lines(folder, pid)
    if not found:
        return done, [f"panel {pid}: picture changes asked for but the panel was not found in the beat files: {json.dumps(edit)}"], False
    f, lines, i, j = found
    st = panel.get("staging") or {}
    ops = []  # (line index, "set" | "del" | "after", text), applied from the bottom up

    def section(name):
        for k in range(i, j):
            if re.match(rf"^\s+{name}:\s*$", lines[k]):
                idx = []
                for m in range(k + 1, j):
                    if FLOW_ITEM.match(lines[m]):
                        idx.append(m)
                    elif lines[m].strip():
                        break
                return idx
        return None

    if "scene" in edit:
        k = next((k for k in range(i, j) if re.match(r"^\s+scene:\s*\S", lines[k])), None)
        if k is None or re.match(r"^\s+scene:\s*[>|]", lines[k]):
            todo.append(f"panel {pid}: change the scene to: {edit['scene']}")
        else:
            ind = re.match(r"^(\s*)", lines[k]).group(1)
            ops.append((k, "set", f"{ind}scene: {json.dumps(edit['scene'], ensure_ascii=False)}\n"))
            done.append(f"scene changed")
    chars = section("characters")
    props = section("props")
    speech = section("speech")
    spoken = panel.get("speech", [])
    for n, ch in (edit.get("lines") or {}).items():
        n = int(n)
        if speech is None or len(speech) != len(spoken) or n >= len(speech):
            todo.append(f"panel {pid}: change line {n + 1}: {json.dumps(ch, ensure_ascii=False)}")
            continue
        m = FLOW_ITEM.match(lines[speech[n]])
        try:
            d = yaml.safe_load(m.group(2))
        except yaml.YAMLError:
            todo.append(f"panel {pid}: change line {n + 1}: {json.dumps(ch, ensure_ascii=False)}")
            continue
        who = "caption" if d.get("kind") == "caption" else d.get("speaker")
        if ch.get("remove"):
            ops.append((speech[n], "del", ""))
            done.append(f"{who} line {n + 1} removed: \"{d.get('text')}\"")
        elif "text" in ch:
            was, d["text"] = d.get("text"), ch["text"]
            ops.append((speech[n], "set", f"{m.group(1)}- {flow(d)}\n"))
            done.append(f"{who} line {n + 1} now reads \"{ch['text']}\" (was \"{was}\")")
        if who == "caption":
            todo.append(f"panel {pid}: a caption was changed; check it still says what its claims say (check_quotes, validate_storyboard --strict)")
    for al in edit.get("add_lines") or []:
        if not speech:
            todo.append(f"panel {pid}: add a line: {json.dumps(al, ensure_ascii=False)}")
            continue
        d = {"speaker": "narrator", "kind": "caption", "text": al["text"]} if al["speaker"] == "caption" else {"speaker": al["speaker"], "text": al["text"]}
        ops.append((speech[-1], "after", f"{FLOW_ITEM.match(lines[speech[-1]]).group(1)}- {flow(d)}\n"))
        done.append(f"{al['speaker']} line added: \"{al['text']}\"")
    for key, idxs, want, label in (("chars", chars, len(st.get("characters", [])), "character"), ("props", props, len(st.get("props", [])), "prop")):
        for n, ch in (edit.get(key) or {}).items():
            n = int(n)
            if idxs is None or len(idxs) != want or n >= len(idxs):
                todo.append(f"panel {pid}: change {label} {n + 1}: {json.dumps(ch)}")
                continue
            m = FLOW_ITEM.match(lines[idxs[n]])
            try:
                d = yaml.safe_load(m.group(2))
            except yaml.YAMLError:
                todo.append(f"panel {pid}: change {label} {n + 1}: {json.dumps(ch)}")
                continue
            if ch.get("remove"):
                ops.append((idxs[n], "del", ""))
                done.append(f"{label} {n + 1} ({d.get('id') or d.get('kind')}) removed")
                continue
            for k, v in ch.items():
                if v == "":
                    d.pop(k, None)
                else:
                    d[k] = v
            ops.append((idxs[n], "set", f"{m.group(1)}- {flow(d)}\n"))
            done.append(f"{label} {n + 1} ({d.get('id') or d.get('kind')}): " + ", ".join(f"{k} -> {v or 'none'}" for k, v in ch.items()))
    for ap in edit.get("add_props") or []:
        if not props:
            todo.append(f"panel {pid}: add a prop: {json.dumps(ap)}")
            continue
        d = {"kind": ap["kind"], "x": 0.55, "y": 0.3, "w": 0.3, "h": 0.45}
        if ap.get("label"):
            d["label"] = ap["label"]
        ops.append((props[-1], "after", f"{FLOW_ITEM.match(lines[props[-1]]).group(1)}- {flow(d)}\n"))
        done.append(f"prop {ap['kind']} added at the default spot (x 0.55, y 0.3): check the picture")
    for ac in edit.get("add_chars") or []:
        if not chars:
            todo.append(f"panel {pid}: add a character: {json.dumps(ac)}")
            continue
        xs = []
        for k in chars:
            try:
                xs.append(float(yaml.safe_load(FLOW_ITEM.match(lines[k]).group(2)).get("x", 0.5)))
            except (yaml.YAMLError, TypeError, ValueError):
                pass
        x = max((0.15, 0.5, 0.85), key=lambda c: min([abs(c - e) for e in xs] or [1]))
        d = {"id": ac["id"], "x": x, **{k: ac[k] for k in ("pose", "face", "facing") if ac.get(k)}}
        ops.append((chars[-1], "after", f"{FLOW_ITEM.match(lines[chars[-1]]).group(1)}- {flow(d)}\n"))
        done.append(f"character {ac['id']} added at x {x}: check the picture")
    if ops and not dry_run:
        for k, op, text in sorted(ops, key=lambda o: o[0], reverse=True):
            if op == "set":
                lines[k] = text
            elif op == "del":
                del lines[k]
            else:
                lines.insert(k + 1, text)
        f.write_text("".join(lines))
    said = "would: " if dry_run else ""
    return [f"panel {pid}: {said}{what}" for what in done], todo, bool(ops) and not dry_run


def apply(folder, answers, dry_run=False):
    """Do the unambiguous answers; return {"done": [...], "todo": [...], "warnings": [...], "general": str}."""
    doc = yaml.safe_load((folder / "storyboard.yaml").read_text())
    panels = {p["id"].replace(".", "_"): p["id"] for b in doc["beats"] for p in b["panels"]}
    out = {"done": [], "todo": [], "warnings": [], "general": (answers.get("general") or {}).get("notes", "")}
    need = {"claim": len(CLAIM_CHECKS), "joke": len(JOKE_CHECKS), "panel": len(PANEL_CHECKS)}
    changed = False
    for key, a in sorted(answers.items()):
        kind, _, rest = (key or "").partition("-")
        if kind not in need or not isinstance(a, dict):
            continue
        verdict, notes = a.get("verdict") or "", (a.get("notes") or "").strip()
        label = rest if kind == "claim" else panels.get(rest, rest)
        ticked = len(a.get("checks") or {})
        if a.get("edit") and kind in ("joke", "panel"):
            pid = panels.get(rest)
            by_id = {p["id"]: p for b in doc["beats"] for p in b["panels"]}
            if pid and a["edit"].get("texts"):  # words first: it rewrites only the staging, and every index the other edits use stays put
                d0, t0, c0 = apply_texts(folder, pid, a["edit"]["texts"], dry_run)
                out["done"] += d0
                out["todo"] += t0
                changed = changed or c0
            d, t, c = apply_edit(folder, by_id.get(pid, {}), pid, a["edit"], dry_run) if pid else ([], [f"{kind} {rest}: picture changes asked for but the panel was not found: {json.dumps(a['edit'])}"], False)
            out["done"] += d
            out["todo"] += t
            changed = changed or c
        if verdict == "keep" and ticked < need[kind]:
            out["warnings"].append(f"{kind} {label}: marked OK with {ticked} of {need[kind]} checks ticked")
        if verdict == "keep" and kind == "claim":
            if dry_run:
                out["done"].append(f"claim {label}: would be verified")
            elif set_claim_status(folder, label, "verified"):
                out["done"].append(f"claim {label}: verified")
                changed = True
            else:
                out["todo"].append(f"claim {label}: marked Fair but its ledger entry or status line was not found")
        elif verdict == "keep" and kind == "joke":
            if dry_run:
                out["done"].append(f"joke {label}: would be approved")
            elif set_confirmed(folder, label, True):
                out["done"].append(f"joke {label}: approved")
                changed = True
            else:
                out["todo"].append(f"joke {label}: marked Approve but the panel was not found in the beat files")
        elif verdict in ("fix", "drop"):
            what = {"claim": {"fix": "reword", "drop": "drop"}, "joke": {"fix": "reword", "drop": "cut"}, "panel": {"fix": "fix", "drop": "redo"}}[kind][verdict]
            out["todo"].append(f"{kind} {label}: {what}" + (f" -- {notes}" if notes else " (no note)"))
        elif notes:
            out["todo"].append(f"{kind} {label}: note -- {notes}")
    if changed:
        rebuild(folder)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="write the review page")
    b.add_argument("comic")
    b.add_argument("-o", "--out", required=True)
    g = b.add_mutually_exclusive_group()
    g.add_argument("--pages-dir", help="the page files (pNNN.txt) of a one-paper comic")
    g.add_argument("--pages-root", help="a folder holding <source id>/pages, for a topic comic")
    b.add_argument("--claims", choices=("unverified", "cited", "all"), default="unverified")
    b.add_argument("--panels", action="store_true", help="also list every panel, drawn, for a layout review")
    b.add_argument("--beats", help="with --panels: only these beats, comma separated (B2,B3)")
    b.add_argument("--no-comic", action="store_true", help="leave out the full comic that appears after Submit")
    a = sub.add_parser("apply", help="apply a finished review's answers")
    a.add_argument("comic")
    a.add_argument("answers")
    a.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    name, folder = pick(ROOT, args.comic)
    folder = Path(folder)
    if args.cmd == "build":
        pages = {}
        if args.pages_dir:
            pages[None] = load_pages(args.pages_dir)
        elif args.pages_root:
            for d in Path(args.pages_root).glob("*/pages"):
                pages[d.parent.name] = load_pages(d)
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        html = build(folder, name, pages, args.claims, args.panels, set(args.beats.split(",")) if args.beats else None, not args.no_comic)
        Path(args.out).write_text(html)
        print(f"wrote {args.out} ({len(html) // 1024} KB)")
        return 0
    res = apply(folder, load_answers(args.answers), args.dry_run)
    for k, title in (("done", "Applied"), ("warnings", "Check these"), ("todo", "Worklist")):
        if res[k]:
            print(f"{title}:")
            for line in res[k]:
                print(f"  - {line}")
    if res["general"]:
        print(f"General notes: {res['general']}")
    if not any(res[k] for k in ("done", "warnings", "todo")):
        print("Nothing to apply.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
