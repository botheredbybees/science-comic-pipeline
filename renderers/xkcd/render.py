#!/usr/bin/env python3
"""xkcd-style renderer: a storyboard becomes A4 SVG pages of stick-figure panels.

Look: outlined and borderless panels, a hand-drawn wobble on every line, stick figures, a short
line from speech to speaker instead of a balloon, almost no colour. The wobble is real geometry
(seeded, so the output is identical every run), so the pages survive PDF converters.

Panels are drawn from their `staging` block. A panel without one falls back to its scene text.
Nothing here is copied from xkcd; only the ideas about style are borrowed.

    python renderers/xkcd/render.py examples/akam-2026-cartooning/storyboard.yaml -o output/xkcd
"""
import argparse
import math
import sys
from html import escape
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from layout import pack_rows  # noqa: E402

from draw import (CHAR_W, FONT, INK, MID, PAPER, SOFT, Pen, block_h, clamp, esc, text, wrap)  # noqa: E402
from props import EXTRA, extra_prop  # noqa: E402

PAGE_W, PAGE_H, MARGIN, GUTTER = 1000, 1414, 40, 16  # A4 at 1000 units wide
FOOTER_H = 30
FIT_FACTORS = (0.55, 0.5, 0.45, 0.4, 0.36)  # scene height as a fraction of panel width, tallest first


# ---------------------------------------------------------------- stick figures
ARMS = {  # (back arm, front arm): points relative to the shoulder, for a figure facing right
    "stand": ([(-13, 16), (-17, 38)], [(13, 16), (17, 38)]),
    "point": ([(-13, 16), (-17, 38)], [(24, 0), (50, -4)]),
    "hold": ([(-13, 16), (-17, 38)], [(20, 12), (36, 2)]),
    "think": ([(-13, 16), (-17, 38)], [(18, 14), (6, -18)]),
    "shrug": ([(-22, 10), (-26, -6)], [(22, 10), (26, -6)]),
    "up": ([(-18, -10), (-24, -34)], [(18, -10), (24, -34)]),
    "sip": ([(-13, 16), (-17, 38)], [(18, 6), (8, -22)]),
}


def _holding(pen, holding, hx, hy, s, w):
    if holding == "marker":
        return pen.line((hx - 2 * s, hy + 3 * s), (hx + 13 * s, hy - 9 * s), 4.2 * s)
    if holding == "mug":
        return (pen.rect(hx - 5 * s, hy - 13 * s, 18 * s, 20 * s, w * 0.8, fill=PAPER, over=0)
                + pen.stroke([(hx + 13 * s, hy - 9 * s), (hx + 20 * s, hy - 5 * s), (hx + 13 * s, hy + 1 * s)], w * 0.8))
    if holding == "paper":
        return pen.rect(hx - 2 * s, hy - 15 * s, 16 * s, 21 * s, w * 0.8, fill=PAPER, over=0)
    return ""


def _face(pen, cx, cy, s, face, w, glasses=False):
    """Eyes, optional glasses and a mouth, for a face centred near (cx, cy), looking right."""
    o = []
    ex, ey = (cx - 1 * s, cx + 8.5 * s), cy - 3 * s
    if face == "deadpan":
        o += [pen.line((x - 3 * s, ey), (x + 3 * s, ey), w * 0.8, amp=0.2) for x in ex]
    elif face == "surprised":
        o += [pen.ellipse(x, ey, 2.4 * s, 2.8 * s, w * 0.6) for x in ex]
    else:
        o += [f'<circle cx="{x:.1f}" cy="{ey:.1f}" r="{1.7 * s:.1f}" fill="{INK}"/>' for x in ex]
    if glasses:
        o += [pen.ellipse(x, ey, 4.8 * s, 4.8 * s, w * 0.7) for x in ex]
        o.append(pen.line((ex[0] + 4.8 * s, ey), (ex[1] - 4.8 * s, ey), w * 0.7, amp=0.1))
    mx = cx + 4 * s
    mouth = {
        "neutral": [(mx - 5 * s, cy + 7 * s), (mx + 5 * s, cy + 7 * s)],
        "deadpan": [(mx - 4 * s, cy + 8 * s), (mx + 4 * s, cy + 8 * s)],
        "smile": [(mx - 6 * s, cy + 5 * s), (mx, cy + 10.5 * s), (mx + 6 * s, cy + 5 * s)],
        "worry": [(mx - 6 * s, cy + 10 * s), (mx, cy + 5.5 * s), (mx + 6 * s, cy + 10 * s)],
    }
    if face == "surprised":
        o.append(pen.ellipse(mx, cy + 8 * s, 2.6 * s, 3.2 * s, w * 0.7))
    else:
        o.append(pen.stroke(mouth.get(face, mouth["neutral"]), w * 0.8))
    return o


def _flip(svg, cx, facing):
    if facing == "left":
        return f'<g transform="translate({cx:.1f} 0) scale(-1 1) translate({-cx:.1f} 0)">{svg}</g>'
    return svg


def _diatom(pen, cx, base, s, pose, face, facing, holding, app):
    """A diatom: a pill-shaped glass shell with ridges, a face, stubby arms and legs."""
    W, H, LEG = 44 * s, 86 * s, 18 * s
    top, bot = base - LEG - H, base - LEG
    w = clamp(2.3 * s, 1.5, 3.0)
    mid = (top + bot) / 2
    pts = []
    for i in range(20):  # a squarish ellipse, hand-jittered
        t = math.tau * i / 20
        c, sn = math.cos(t), math.sin(t)
        pts.append((cx + W / 2 * math.copysign(abs(c) ** 0.55, c) * (1 + pen.n(0.015)),
                    mid + H / 2 * math.copysign(abs(sn) ** 0.75, sn) * (1 + pen.n(0.015))))
    o = [pen.line((cx - 9 * s, bot), (cx - 11 * s, base), w), pen.line((cx + 9 * s, bot), (cx + 11 * s, base), w)]
    back, front = ARMS.get(pose, ARMS["stand"])
    sh = mid - 4 * s
    for arm, side in ((back, -1), (front, 1)):
        x0 = cx + side * W / 2
        o.append(pen.stroke([(x0, sh)] + [(x0 + (dx - side * 13) * s, sh + dy * s) for dx, dy in arm], w))
    hx, hy = cx + W / 2 + (front[-1][0] - 13) * s, sh + front[-1][1] * s
    o.append(_holding(pen, holding, hx, hy, s, w))
    o.append(pen.stroke(pts, w, closed=True, fill=PAPER))
    for i in range(5):  # the ridges (striae) of the shell
        yy = top + H * (0.52 + 0.1 * i)
        o.append(pen.line((cx - W / 2 + 2 * s, yy), (cx - W / 2 + 9 * s, yy), w * 0.6, amp=0.3))
        o.append(pen.line((cx + W / 2 - 9 * s, yy), (cx + W / 2 - 2 * s, yy), w * 0.6, amp=0.3))
    o += _face(pen, cx, top + 0.3 * H, s * 1.1, face, w, False)
    return _flip("".join(o), cx, facing), (cx, top - 4 * s)


def figure(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """Draw one figure (a stick figure, or a diatom if appearance.body is 'diatom'); return (svg, head point)."""
    app = app or {}
    if app.get("body") == "diatom":
        return _diatom(pen, cx, base, s, pose, face, facing, holding, app)
    R, BODY, LEG = 15 * s, 46 * s, 48 * s
    cy, neck, hip = base - LEG - BODY - R, base - LEG - BODY, base - LEG
    sh = neck + 9 * s
    w = clamp(2.3 * s, 1.5, 3.0)
    o = [pen.line((cx, hip), (cx - 13 * s, base), w), pen.line((cx, hip), (cx + 13 * s, base), w),
         pen.line((cx, neck), (cx, hip), w)]
    back, front = ARMS.get(pose, ARMS["stand"])
    for arm in (back, front):
        o.append(pen.stroke([(cx, sh)] + [(cx + dx * s, sh + dy * s) for dx, dy in arm], w))
    o.append(_holding(pen, holding, cx + front[-1][0] * s, sh + front[-1][1] * s, s, w))
    if app.get("lanyard"):
        o.append(pen.stroke([(cx - 6 * s, neck + 1 * s), (cx, neck + 22 * s), (cx + 6 * s, neck + 1 * s)], w * 0.6))
        o.append(pen.rect(cx - 4.5 * s, neck + 22 * s, 9 * s, 10 * s, w * 0.6, fill=PAPER, over=0))
    o.append(pen.ellipse(cx, cy, R, R * 1.02, w, fill=PAPER))
    hair = app.get("hair", "none")
    if hair == "ponytail":
        o.append(pen.stroke([(cx - 11 * s, cy - 9 * s), (cx - 21 * s, cy - 2 * s), (cx - 24 * s, cy + 11 * s)], w))
        o.append(pen.line((cx - 5 * s, cy - R), (cx - 9 * s, cy - R - 7 * s), w * 0.8))
        o.append(pen.line((cx + 2 * s, cy - R), (cx + 1 * s, cy - R - 8 * s), w * 0.8))
    elif hair == "bun":
        o.append(pen.ellipse(cx - 7 * s, cy - R - 5 * s, 6 * s, 6 * s, w))
    elif hair == "beanie":  # a woolly hat sitting above the eyes: puffy crown, ribbed cuff, solid pompom
        o.append(pen.stroke([(cx - R * 1.06, cy - 11.5 * s), (cx - R * 1.0, cy - R * 1.2), (cx, cy - R * 1.55), (cx + R * 1.0, cy - R * 1.2), (cx + R * 1.06, cy - 11.5 * s)], w, fill=PAPER))
        o.append(pen.line((cx - R * 1.08, cy - 11.5 * s), (cx + R * 1.08, cy - 11.5 * s), w))
        o.append(pen.line((cx - R * 1.04, cy - 7.5 * s), (cx + R * 1.04, cy - 7.5 * s), w))
        o += [pen.line((cx + dx * s, cy - 11 * s), (cx + dx * s, cy - 8 * s), w * 0.6, amp=0.1) for dx in range(-12, 13, 4)]
        o.append(f'<circle cx="{cx:.1f}" cy="{cy - R * 1.55 - 4.6 * s:.1f}" r="{4.6 * s:.1f}" fill="{INK}"/>')
    elif hair == "spiky":
        for dx in (-7, 0, 7):
            o.append(pen.line((cx + dx * s, cy - R + 1 * s), (cx + dx * 1.3 * s, cy - R - 8 * s), w))
    o += _face(pen, cx, cy, s, face, w, app.get("glasses", False))
    top = cy - R - (17 * s if hair == "beanie" else 4 * s)
    return _flip("".join(o), cx, facing), (cx, top)


# ---------------------------------------------------------------- props
def _bars(pen, x, y, w, h, spec, fs):
    bars = spec["bars"]
    n = len(bars)
    mx = spec.get("max") or max(b["value"] for b in bars)
    pct = "%" if spec.get("unit") == "%" else ""
    show = spec.get("show_values", True)
    fsb = max(11.0, fs * 0.85)
    tick = f"{mx:g}{pct}" if show and spec.get("show_max", True) else ""
    ax = x + max(14, len(tick) * fsb * CHAR_W + 8)
    slot = (x + w - ax - 4) / n
    labs = [wrap(b.get("label", ""), slot - 4, fsb) for b in bars]
    lab_h = max(len(la) for la in labs) * fsb * 1.15 + 8
    top, bottom = y + fsb + 10, y + h - lab_h
    o = [pen.line((ax, top - 4), (ax, bottom), 2.2), pen.line((ax, bottom), (x + w, bottom), 2.2)]
    if tick:
        o.append(text(ax - 5, top - 4 - fsb * 0.2, [tick], fsb, anchor="end"))
    for i, b in enumerate(bars):
        bw = min(slot * 0.62, 86)
        cx = ax + slot * (i + 0.5)
        bh = clamp(b["value"] / mx, 0, 1) * (bottom - top)
        fill = PAPER if b.get("style") == "hollow" else INK
        o.append(pen.rect(cx - bw / 2, bottom - bh, bw, bh, 2.4, fill=fill, over=1.5))
        if show:
            o.append(text(cx, bottom - bh - fsb * 1.25, [f"{b['value']:g}{pct}"], fsb, anchor="middle"))
        o.append(text(cx, bottom + 4, labs[i], fsb, anchor="middle", lh=1.15))
    return "".join(o)


def prop(pen, x, y, w, h, p, cast, fs):
    k = p["kind"]
    lab = p.get("label", "")
    o = []
    if k in EXTRA:
        return extra_prop(pen, x, y, w, h, p, fs)
    if k == "bars":
        return _bars(pen, x, y, w, h, p, fs)
    if k == "board":
        o.append(pen.rect(x, y, w, h, 2.6, fill=PAPER))
        cards = p.get("cards", [])
        top = y + 12
        if p.get("title"):
            o.append(text(x + w / 2, y + 6, [p["title"]], fs, anchor="middle"))
            top += fs + 4
        if cards:
            n = len(cards)
            cw = (w - 24 - (n - 1) * 10) / n
            ch = clamp(h * 0.5, 30, 54)
            for i, c in enumerate(cards):
                cx0 = x + 12 + i * (cw + 10)
                if c.get("covered"):
                    o.append(pen.rect(cx0, top, cw, ch, 2, fill=SOFT, over=1))
                    o += [pen.line((cx0 + cw * t, top + ch), (cx0 + cw * t + ch * 0.5, top), 1.4, amp=0.4) for t in (0.1, 0.4, 0.7)]
                else:
                    o.append(pen.rect(cx0, top, cw, ch, 2, fill=PAPER, over=1))
                    o.append(text(cx0 + cw / 2, top + ch / 2 - fs * 0.55, [c["label"]], fs, anchor="middle"))
    elif k == "slide":
        sh = h * 0.86
        o += [pen.line((x + w / 2, y + sh), (x + w * 0.35, y + h), 2.2), pen.line((x + w / 2, y + sh), (x + w * 0.65, y + h), 2.2)]
        o.append(pen.rect(x, y, w, sh, 2.6, fill=PAPER))
        if p.get("title"):
            o.append(text(x + w / 2, y + 5, [p["title"]], fs, anchor="middle"))
        boxes = [(0.1, 0.38), (0.4, 0.52), (0.7, 0.34), (0.55, 0.74)]
        bw, bh = w * 0.18, sh * 0.15
        for bx, by in boxes:
            o.append(pen.rect(x + w * bx, y + sh * by, bw, bh, 1.8, over=1))
        for (a, b) in ((0, 1), (1, 2), (2, 3), (0, 3)):
            ax_, ay_ = x + w * (boxes[a][0]) + bw, y + sh * boxes[a][1] + bh / 2
            bx_, by_ = x + w * boxes[b][0], y + sh * boxes[b][1] + bh / 2
            o.append(pen.arrow((ax_, ay_), (bx_ if bx_ > ax_ else bx_ + bw, by_), 1.6, head=7))
    elif k == "paper":
        o.append(pen.rect(x, y, w, h, 2.4, fill=PAPER, over=1))
        o.append(pen.line((x + w - 14, y), (x + w, y + 14), 1.6, amp=0.2))
        top = y + 10
        if lab:
            o.append(text(x + w / 2, y + 8, [lab], fs * 1.05, anchor="middle"))
            top += fs * 1.4
        o += [pen.line((x + 10, yy), (x + w - 10, yy), 1.2, amp=0.5, color=MID) for yy in
              [top + i * 13 for i in range(max(0, int((y + h - 10 - top) / 13)))]]
    elif k == "phone":
        o.append(pen.rect(x, y, w, h, 2.6, fill=PAPER, over=1))
        for i in range(3):
            yy = y + 16 + i * (h - 30) / 3
            o.append(pen.rect(x + 8, yy, 8, 8, 1.6, over=0))
            o.append(pen.line((x + 22, yy + 5), (x + w - 8, yy + 5), 1.4, amp=0.4, color=MID))
        if lab:
            o.append(text(x + w / 2, y + h + 4, [lab], fs * 0.9, anchor="middle"))
    elif k == "bowl":
        rim = y + h * 0.35
        o += [f'<ellipse cx="{x + w * (0.25 + 0.25 * i) + pen.n(2):.1f}" cy="{rim - 4 + pen.n(2):.1f}" rx="6" ry="5" fill="{INK}"/>' for i in range(3)]
        o.append(pen.stroke([(x, rim), (x + w * 0.1, y + h * 0.85), (x + w / 2, y + h), (x + w * 0.9, y + h * 0.85), (x + w, rim)], 2.4, fill=PAPER))
        o.append(pen.line((x - 3, rim), (x + w + 3, rim), 2.4))
        if lab:
            o.append(text(x + w / 2, y + h + 4, [lab], fs * 0.9, anchor="middle"))
    elif k == "wall":
        o.append(pen.rect(x, y, w, h, 2.2, fill=SOFT, over=1))
        cols, rows = 3, 2
        pw, ph = (w - 20 - (cols - 1) * 12) / cols, (h - 24 - 12) / rows
        for r in range(rows):
            for c in range(cols):
                px, py = x + 10 + c * (pw + 12), y + 12 + r * (ph + 12)
                o.append(pen.rect(px, py, pw, ph, 1.8, fill=PAPER, over=0))
                o.append(pen.stroke([(px + pw * 0.3, py + ph * 0.55), (px + pw * 0.45, py + ph * 0.75), (px + pw * 0.72, py + ph * 0.3)], 1.8))
    elif k == "sign":
        o.append(pen.line((x + w / 2, y + h * 0.5), (x + w / 2, y + h), 2.4))
        o.append(pen.rect(x, y, w, h * 0.5, 2.4, fill=PAPER, over=1))
        o.append(text(x + w / 2, y + h * 0.25 - fs * 0.5, wrap(lab, w - 6, fs * 0.85)[:2], fs * 0.85, anchor="middle"))
    elif k == "picture":
        o.append(pen.rect(x, y, w, h, 2.8, fill=PAPER, over=1))
        if "staging" in p:
            o.append(stage(pen, x + 6, y + 6, w - 12, h - 12, p["staging"], cast, fs * 0.8)[0])
    elif k == "desk":
        o.append(pen.rect(x, y, w, h, 2.6, fill=PAPER, over=0))
    elif k == "label":
        size = {"small": 0.8, "large": 1.3}.get(p.get("size"), 1.0)
        o.append(text(x, y - fs * size * 0.5, [lab], fs * size, anchor="middle"))
    else:  # box: the fallback for anything else
        o.append(pen.rect(x, y, w, h, 2.2, fill=PAPER))
        o.append(text(x + w / 2, y + 6, wrap(lab, w - 10, fs), fs, anchor="middle"))
    return "".join(o)


def stage(pen, x, y, w, h, st, cast, fs):
    """Draw a staging block into the box; return (svg, {character id: head position})."""
    props = st.get("props", [])
    split = next((i for i, p in enumerate(props) if p["kind"] == "desk"), len(props))
    out, heads = [], {}

    def draw(p):
        if p["kind"] == "arrow":
            out.append(pen.arrow((x + p.get("x", 0) * w, y + p.get("y", 0) * h),
                                 (x + p.get("x2", 0) * w, y + p.get("y2", 0) * h), 2.2))
            return
        px = x + p.get("x", 0) * w
        py = y + p.get("y", 0) * h
        pw = p.get("w", 1.0 if p["kind"] == "desk" else 0.3) * w
        ph = p.get("h", 0.3) * h
        out.append(prop(pen, px, py, pw, ph, p, cast, fs))

    for p in props[:split]:
        draw(p)
    base_s = 0.00476 * h * clamp(1 + 0.18 * (w / h - 2.0), 1.0, 1.3)  # wide, short boxes get bigger figures
    for c in st.get("characters", []):
        app = cast.get(c["id"], {}).get("appearance")
        svg, head = figure(pen, x + c.get("x", 0.5) * w, y + c.get("y", 0.94) * h, base_s * c.get("scale", 1),
                           c.get("pose", "stand"), c.get("face", "neutral"), c.get("facing", "right"),
                           c.get("holding"), app)
        out.append(svg)
        heads.setdefault(c["id"], head)
    for p in props[split:]:
        draw(p)
    return "".join(out), heads


# ---------------------------------------------------------------- panels
PAD = 14


FONT_SIZE = 18  # one size for every caption and speech line, so nothing is harder to read than the rest
SPEECH_GAP = 26  # clear space between a speech block and the head it belongs to


def panel_font(w):
    return FONT_SIZE


def _head_offset(c, cast, w, h):
    """How far below the top of the scene a staged character's head sits."""
    diatom = (cast.get(c["id"], {}).get("appearance") or {}).get("body") == "diatom"
    s = 0.00476 * h * clamp(1 + 0.18 * (w / h - 2.0), 1.0, 1.3) * c.get("scale", 1)
    return c.get("y", 0.94) * h - (108 if diatom else 128) * s


def plan_panel(panel, w, k=0.55, cast=None):
    """Work out the text blocks and the natural height of a panel of width w."""
    cast = cast or {}
    fs = panel_font(w)
    inner = w - 2 * PAD
    staged = {c["id"]: c for c in (panel.get("staging") or {}).get("characters", [])}
    captions, talk = [], []
    for s in panel.get("speech", []):
        kind = s.get("kind", "say")
        if kind == "caption":
            captions.append(wrap(s["text"], inner - 16, fs))
        else:
            shown = s["text"] if "staging" in panel else f'{s["speaker"].replace("_", " ").title()}: {s["text"]}'
            if kind == "think":
                shown = f"\u201c{shown}\u201d"
            talk.append((s, wrap(shown, min(inner * 0.6, 260), fs)))
    scene_nat = clamp(k * w, 150, 520 * k)
    near = [(s, li) for s, li in talk if s["speaker"] in staged]
    far = [(s, li) for s, li in talk if s["speaker"] not in staged]
    # Speech sits just above its speaker's head; the scene only needs extra headroom when the head is too low.
    need = sum(block_h(li, fs) + SPEECH_GAP for _, li in near)
    free = min((_head_offset(staged[s["speaker"]], cast, inner, scene_nat) for s, _ in near), default=0)
    talk_h = max(0.0, need - free) + sum(block_h(li, fs) + 22 for _, li in far)
    cap_h = sum(block_h(c, fs) + 16 for c in captions) + (6 if captions else 0)
    return {"fs": fs, "captions": captions, "talk": talk, "cap_h": cap_h, "talk_h": talk_h,
            "scene_nat": scene_nat, "nat_h": PAD + cap_h + talk_h + scene_nat + PAD}


def draw_panel(panel, plan, w, h, cast):
    fs, pid = plan["fs"], panel["id"]
    pen = Pen(pid)
    scene_h = h - plan["nat_h"] + plan["scene_nat"]
    o = []
    if panel.get("frame", "outlined") == "outlined":
        o.append(pen.rect(0, 0, w, h, 2.8))
    y = PAD
    for lines in plan["captions"]:
        bh = block_h(lines, fs) + 16
        o.append(f'<rect x="{PAD}" y="{y:.1f}" width="{w - 2 * PAD:.1f}" height="{bh:.1f}" fill="{SOFT}"/>')
        o.append(text(PAD + 8, y + 7, lines, fs))
        y += bh + 6
    talk_top = y
    scene_y = talk_top + plan["talk_h"]
    heads = {}
    if "staging" in panel:
        svg, heads = stage(pen, PAD, scene_y, w - 2 * PAD, scene_h, panel["staging"], cast, fs)
        o.append(svg)
    else:
        lines = wrap(panel["scene"], w - 2 * PAD - 12, fs * 0.9)
        o.append(text(w / 2, scene_y + scene_h / 2 - block_h(lines, fs * 0.9) / 2, lines, fs * 0.9, anchor="middle", fill=MID))
    placed, ty = [], talk_top
    for s, lines in plan["talk"]:
        bh = block_h(lines, fs)
        tw = max(len(li) for li in lines) * fs * CHAR_W
        head = heads.get(s["speaker"])
        if not head:  # nobody to point at: stack the text at the top of the scene
            o.append(text(w / 2, ty, lines, fs, anchor="middle"))
            ty += bh + 22
            continue
        cx = clamp(head[0], PAD + tw / 2, w - PAD - tw / 2)
        bottom = head[1] - SPEECH_GAP
        top = bottom - bh
        for x0, x1, y0, y1 in placed:  # two speakers close together: stack rather than overlap
            if cx - tw / 2 < x1 and cx + tw / 2 > x0 and top < y1 and bottom > y0:
                top = y0 - 6 - bh
                bottom = top + bh
        placed.append((cx - tw / 2, cx + tw / 2, top, bottom))
        o.append(text(cx, top, lines, fs, anchor="middle", halo=True))
        dash = "3 5" if s.get("kind") == "think" else None
        o.append(pen.line((cx + (head[0] - cx) * 0.2, bottom + 3), (head[0], head[1] - 8), 2.0, dash=dash))
    cid = "clip-" + pid.replace(".", "-")
    alt = esc(panel["scene"])
    alt_attr = escape(str(panel["scene"]), quote=True)
    return (f'<g id="panel-{pid}" role="img" aria-label="{alt_attr}"><title>{alt}</title>'
            f'<clipPath id="{cid}"><rect x="-4" y="-4" width="{w + 8:.1f}" height="{h + 8:.1f}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{"".join(o)}</g></g>')


# ---------------------------------------------------------------- pages
def row_geometry(row, usable):
    net = usable - GUTTER * (len(row) - 1)
    return [net * u / 12 for _, u in row]


def build_items(doc, cast, k=0.55):
    """The flow of the comic: header, beat labels, rows, colophon, each with its height."""
    meta, src = doc["meta"], doc["meta"]["source"]
    usable = PAGE_W - 2 * MARGIN
    items = []
    title_lines = wrap(meta["title"], usable, 46)
    sub = wrap(f'From “{src["title"]}” by {", ".join(src["authors"])} ({src["year"]})', usable, 17)
    h = block_h(title_lines, 46, 1.1) + block_h(sub, 17) + 24
    items.append({"kind": "header", "h": h, "draw": lambda y, tl=title_lines, sb=sub: (
        text(MARGIN, y, tl, 46, lh=1.1) + text(MARGIN, y + block_h(tl, 46, 1.1) + 6, sb, 17, fill=MID))})
    for beat in doc["beats"]:
        first = True
        for row in pack_rows(beat["panels"]):
            widths = row_geometry(row, usable)
            plans = [plan_panel(p, w, k, cast) for (p, _), w in zip(row, widths)]
            rh = max(pl["nat_h"] for pl in plans)
            label = (beat.get("title") or beat["act"]) if first else None
            items.append({"kind": "row", "h": rh + (30 if label else 0), "label": label, "beat": beat["id"],
                          "draw": (lambda y, row=row, widths=widths, plans=plans, rh=rh, label=label: (
                              (text(MARGIN, y, [label], 18, fill=MID, weight="bold") if label else "") +
                              "".join(f'<g transform="translate({MARGIN + sum(widths[:i]) + GUTTER * i:.1f} {y + (30 if label else 0):.1f})">'
                                      + draw_panel(p, plans[i], widths[i], rh, cast) + "</g>"
                                      for i, (p, _) in enumerate(row))))})
            first = False
    note = (f'Adapted from “{src["title"]}” by {", ".join(src["authors"])} ({src["year"]})'
            + (f', doi {src["doi"]}' if src.get("doi") else "") + f'. Licence: {src["licence"]}. '
            "Condensed into a comic with invented characters and scenes; the authors did not write or endorse it.")
    colo = wrap(note, usable, 15)
    items.append({"kind": "colophon", "h": block_h(colo, 15) + 12,
                  "draw": lambda y, c=colo: text(MARGIN, y + 6, c, 15, fill=MID)})
    return items


def paginate(items):
    """Fill A4 pages top to bottom without splitting a row; keep a beat label with its row."""
    top, bottom = MARGIN, PAGE_H - MARGIN - FOOTER_H
    pages, cur, y = [], [], top
    for it in items:
        need = it["h"] + (GUTTER if cur else 0)
        if cur and y + need > bottom:
            pages.append(cur)
            cur, y, need = [], top, it["h"]
        y += GUTTER if cur else 0
        cur.append((y, it))
        y += it["h"]
    if cur:
        pages.append(cur)
    return pages


def render_pages(doc):
    """Return (svg strings, placements) for the whole comic."""
    cast = {c["id"]: c for c in doc["cast"]}
    # Try slightly shorter panels and keep the tallest setting that needs the fewest pages.
    tries = [paginate(build_items(doc, cast, k)) for k in FIT_FACTORS]
    pages = min(tries, key=lambda pg: len(pg))
    svgs, placements = [], []
    for n, page in enumerate(pages, 1):
        body = []
        for y, it in page:
            body.append(it["draw"](y))
            placements.append({"page": n, "y": y, "h": it["h"], "kind": it["kind"], "beat": it.get("beat")})
        foot = text(PAGE_W / 2, PAGE_H - MARGIN - 8, [f'{doc["meta"]["title"]} · page {n} of {len(pages)}'], 14, anchor="middle", fill=MID)
        svgs.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {PAGE_W} {PAGE_H}" width="210mm" height="297mm" '
                    f'font-family=\'{FONT}\' role="group" aria-label="Page {n} of {len(pages)}">'
                    f'<rect width="{PAGE_W}" height="{PAGE_H}" fill="{PAPER}"/>{"".join(body)}{foot}</svg>')
    return svgs, placements


# ---------------------------------------------------------------- contact sheet
SHEET_CSS = """
:root { --bg: #E9ECF1; --ink: #1C2330; --muted: #566174; --accent: #2B5BD7; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #0F1319; --ink: #E5E9F0; --muted: #9AA5B6; --accent: #8FADF6; color-scheme: dark; } }
:root[data-theme="dark"] { --bg: #0F1319; --ink: #E5E9F0; --muted: #9AA5B6; --accent: #8FADF6; color-scheme: dark; }
body { background: var(--bg); color: var(--ink); font-family: Inter, system-ui, sans-serif; line-height: 1.5;
  padding-block: 28px 56px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
.wrap { max-width: 860px; margin: 0 auto; display: grid; gap: 22px; }
h1 { margin: 0; font-size: 1.3rem; text-wrap: balance; } p { margin: 0; color: var(--muted); max-width: 70ch; }
.page { background: #fff; box-shadow: 0 2px 14px rgba(0,0,0,.28); }
.page svg { display: block; width: 100%; height: auto; }
.label { font-size: .72rem; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
"""


def build_sheet(doc, svgs, standalone=False):
    pages = "".join(f'<div class="page">{s}</div>' for s in svgs)
    body = (f'<title>{esc(doc["meta"]["title"])} xkcd Pages</title><meta name="claude:viewport-fit-sides" content="cover">'
            '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Patrick+Hand&display=swap">'
            f'<style>{SHEET_CSS}</style><div class="wrap"><div><span class="label">xkcd-style render</span>'
            f'<h1>{esc(doc["meta"]["title"])}: {len(svgs)} A4 pages</h1></div>'
            '<p>Drawn from the storyboard with stick figures and a hand-drawn wobble. Pages are A4 and read left to right, then down.</p>'
            f'{pages}</div>')
    if standalone:
        return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head><body>{body}</body></html>'
    return body


def render(doc, out_dir, standalone=False):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    svgs, _ = render_pages(doc)
    paths = []
    for n, svg in enumerate(svgs, 1):
        p = out / f"page-{n}.svg"
        p.write_text(svg)
        paths.append(p)
    (out / "sheet.html").write_text(build_sheet(doc, svgs, standalone=standalone))
    return paths


def style_warnings(doc):
    """xkcd mixes outlined and borderless panels; warn when a storyboard uses only one kind."""
    frames = [p.get("frame", "outlined") for b in doc["beats"] for p in b["panels"]]
    if len(frames) >= 6 and "borderless" not in frames:
        return ["every panel is outlined; xkcd mixes outlined and borderless panels (set frame: borderless on some)"]
    return []


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("storyboard")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--standalone", action="store_true", help="wrap the contact sheet in a full HTML document")
    args = ap.parse_args(argv)
    doc = yaml.safe_load(Path(args.storyboard).read_text())
    for w in style_warnings(doc):
        print(f"STYLE   {w}", file=sys.stderr)
    paths = render(doc, args.out, standalone=args.standalone)
    print(f"wrote {len(paths)} page(s) and sheet.html to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
