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
import re
import sys
from html import escape
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from layout import pack_rows  # noqa: E402

from draw import (CHAR_W, FONT, INK, MID, PAPER, SOFT, Pen, block_h, clamp, esc, text, wrap)  # noqa: E402
from props import EXTRA, extra_prop  # noqa: E402
from animals import ANIMALS  # noqa: E402

PAGE_W, PAGE_H, MARGIN, GUTTER = 1000, 1414, 40, 16  # A4 at 1000 units wide
FOOTER_H = 30
PIPELINE_URL = "https://github.com/botheredbybees/science-comic-pipeline"
PIPELINE_NAME = "science-comic-pipeline"
FIT_FACTORS = (0.55, 0.5, 0.45, 0.4, 0.36)  # scene height as a fraction of panel width, tallest first


# ---------------------------------------------------------------- stick figures
ARMS = {  # (back arm, front arm): points relative to the shoulder, for a figure facing right
    "stand": ([(-13, 16), (-17, 38)], [(13, 16), (17, 38)]),
    "point": ([(-13, 16), (-17, 38)], [(24, 0), (50, -4)]),
    "hold": ([(-13, 16), (-17, 38)], [(20, 12), (36, 2)]),
    "think": ([(-13, 16), (-17, 38)], [(18, 14), (6, -18)]),
    "shrug": ([(-22, 10), (-26, -6)], [(22, 10), (26, -6)]),
    "up": ([(-18, -10), (-24, -34)], [(18, -10), (24, -34)]),
    "sip": ([(-13, 16), (-17, 38)], [(20, 8), (13, -4)]),  # the mug stops just in front of the mouth, clear of the face
}


def _holding(pen, holding, hx, hy, s, w):
    if holding == "marker":
        return pen.line((hx - 2 * s, hy + 3 * s), (hx + 13 * s, hy - 9 * s), 4.2 * s)
    if holding == "mug":  # held by the handle, which is the hand's end of the mug, with steam rising off the coffee
        top = hy - 12 * s
        steam = [pen.stroke([(hx + x * s, top - 3 * s), (hx + (x - 2.5) * s, top - 8 * s), (hx + (x + 2.5) * s, top - 13 * s),
                             (hx + x * s, top - 18 * s)], w * 0.5) for x in (8, 12.5, 17)]
        return (pen.stroke([(hx + 4 * s, hy - 8 * s), (hx - 3 * s, hy - 7 * s), (hx - 3 * s, hy - 1 * s), (hx + 4 * s, hy)], w * 0.8)
                + pen.rect(hx + 4 * s, top, 17 * s, 19 * s, w * 0.8, fill=PAPER, over=0) + "".join(steam))
    if holding == "clipboard":
        return (pen.rect(hx - 3 * s, hy - 17 * s, 17 * s, 23 * s, w * 0.8, fill=PAPER, over=0)
                + pen.rect(hx + 1.5 * s, hy - 19.5 * s, 8 * s, 4 * s, w * 0.7, fill=INK, over=0)
                + "".join(pen.line((hx - 0 * s, hy - 11 * s + i * 5 * s), (hx + 11 * s, hy - 11 * s + i * 5 * s), w * 0.45, amp=0.15)
                          for i in range(3)))
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


# Hair and hats are one big simple shape laid over the head, as in a newspaper-strip stick figure: solid black
# hair (the face is what is left uncovered), or a plain white hat that overhangs the head. Points are in head
# radii from the head's centre, for a figure facing right, so the back of the head is to the left.
HAIR_CAP = {  # the outline of hair that covers the top and back of the head, ending in a fringe across the forehead
    "bob": [(0.95, -0.28), (0.62, -0.98), (0.0, -1.2), (-0.85, -0.98), (-1.24, -0.2), (-1.22, 0.55), (-0.85, 0.8),
            (-0.6, 0.3), (-0.5, -0.2), (0.0, -0.5), (0.5, -0.45)],
    "long": [(0.95, -0.28), (0.62, -0.98), (0.0, -1.2), (-0.85, -0.98), (-1.28, -0.1), (-1.3, 1.1), (-1.05, 1.9),
             (-0.5, 1.95), (-0.55, 0.6), (-0.5, -0.2), (0.0, -0.5), (0.5, -0.45)],
    "short": [(0.92, -0.25), (0.6, -0.97), (0.0, -1.16), (-0.85, -0.92), (-1.14, -0.2), (-0.92, 0.2), (-0.5, -0.15),
              (0.0, -0.45), (0.5, -0.4)],
}
PONYTAIL = [(-1.0, -0.5), (-1.7, -0.45), (-2.15, 0.15), (-2.1, 0.95), (-1.8, 1.25), (-1.65, 0.55), (-1.15, 0.05)]
SPIKES = [(-1.1, -0.1), (-1.4, -0.65), (-0.95, -0.8), (-0.95, -1.3), (-0.4, -1.0), (0.0, -1.5), (0.35, -1.0), (0.9, -1.3),
          (0.92, -0.78), (1.22, -0.62), (0.9, -0.3), (0.45, -0.6), (0.0, -0.4), (-0.45, -0.6), (-0.85, -0.2)]
BEANIE = [(-1.2, -0.42), (-1.18, -1.05), (-0.62, -1.62), (0.0, -1.76), (0.62, -1.62), (1.18, -1.05), (1.22, -0.42),
          (0.6, -0.5), (0.0, -0.54), (-0.6, -0.5)]


HAIR_OUTER_N = {"bob": 7, "long": 8, "short": 6}  # how many of a cap's points run along its outside (the rest are the fringe)


def _strands(pen, cap, cx, cy, R, w, n=11):
    """Hair as a handful of curved strokes combed from a parting at the front of the crown, back over the head and
    down to points spaced along the outside of the hair, plus a few across the forehead. A white patch underneath
    hides the top of the head circle, as the hair does."""
    full = [(cx + x * R, cy + y * R) for x, y in HAIR_CAP[cap]]
    outer = full[:HAIR_OUTER_N[cap]]
    seg = [math.dist(outer[i], outer[i + 1]) for i in range(len(outer) - 1)]
    total = sum(seg)
    out = [pen.stroke(full, 0.1, closed=True, fill=PAPER, color=PAPER)]
    part = (cx + 0.3 * R, cy - 1.14 * R)

    def strand(end, bow):
        mid = ((part[0] + end[0]) / 2, (part[1] + end[1]) / 2)
        away = (mid[0] - cx, mid[1] - cy)
        norm = math.hypot(*away) or 1
        mid = (mid[0] + away[0] / norm * bow * R, mid[1] + away[1] / norm * bow * R)
        return pen.stroke([(part[0] + pen.n(0.25), part[1] + pen.n(0.25)), mid, end], w * 0.6)

    for k in range(n):
        d, i = total * (k + 0.5) / n, 0
        while d > seg[i]:
            d -= seg[i]
            i += 1
        t = d / seg[i]
        out.append(strand((outer[i][0] + (outer[i + 1][0] - outer[i][0]) * t, outer[i][1] + (outer[i + 1][1] - outer[i][1]) * t), 0.12))
    out += [strand(p, 0.05) for p in full[-2:]]  # across the forehead
    return out


def _hair(pen, kind, cx, cy, R, w, tone="dark"):
    """The hair or hat for a head of radius R, drawn over the head circle and under the face.
    Dark hair is solid black; light (blond) hair is the same shape as an outline with a white fill."""
    fill = INK if tone == "dark" else PAPER
    if tone == "strands" and kind in ("bob", "long", "ponytail", "bun"):
        o = _strands(pen, "short" if kind in ("ponytail", "bun") else kind, cx, cy, R, w, n=9 if kind == "long" else 8)
        if kind == "ponytail":  # the tail: three strokes from the nape to the tip
            o += [pen.stroke([(cx - 1.0 * R, cy - 0.45 * R), (cx - 1.75 * R, cy - 0.2 * R + dy * R), (cx - 1.8 * R + dx * R, cy + 1.2 * R)], w * 0.6)
                  for dx, dy in ((0, 0), (0.25, 0.25), (-0.2, -0.2))]
        elif kind == "bun":
            o.append(f'<circle cx="{cx - 0.55 * R:.1f}" cy="{cy - 1.3 * R:.1f}" r="{0.42 * R:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="{w * 0.6:.1f}"/>')
        return o
    if tone == "strands":
        tone, fill = "dark", INK  # spiky hair and hats have no strand form

    def P(pts):
        return [(cx + x * R, cy + y * R) for x, y in pts]
    if kind in ("bob", "long"):
        return [pen.stroke(P(HAIR_CAP[kind]), w, closed=True, fill=fill)]
    if kind in ("ponytail", "bun"):
        o = []
        if kind == "bun":  # the bun goes under the cap, so that a light bun's outline does not cross the hair
            o.append(f'<circle cx="{cx - 0.55 * R:.1f}" cy="{cy - 1.3 * R:.1f}" r="{0.42 * R:.1f}" fill="{fill}" stroke="{INK}" stroke-width="{w:.1f}"/>')
        o.append(pen.stroke(P(HAIR_CAP["short"]), w, closed=True, fill=fill))
        if kind == "ponytail":
            o.append(pen.stroke(P(PONYTAIL), w, closed=True, fill=fill))
        return o
    if kind == "spiky":
        return [pen.poly(P(SPIKES), w, fill=fill, jit=0.4)]
    if kind == "beanie":
        return [pen.stroke(P(BEANIE), w, closed=True, fill=PAPER),
                pen.line((cx - 1.2 * R, cy - 0.78 * R), (cx + 1.2 * R, cy - 0.78 * R), w * 0.8, amp=0.3),
                f'<circle cx="{cx + 0.05 * R:.1f}" cy="{cy - 1.9 * R:.1f}" r="{0.3 * R:.1f}" fill="{INK}"/>']
    return []


HAIR_TOP = {"bob": 1.2, "long": 1.2, "ponytail": 1.2, "bun": 1.75, "spiky": 1.55, "beanie": 1.85}  # head radii above the head's centre


def figure(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """Draw one figure (a stick figure, or a diatom if appearance.body is 'diatom'); return (svg, head point)."""
    app = app or {}
    if app.get("body") == "diatom":
        return _diatom(pen, cx, base, s, pose, face, facing, holding, app)
    if app.get("body") in ANIMALS:
        return ANIMALS[app["body"]](pen, cx, base, s, pose, face, facing, holding, app)
    R, BODY, LEG = 15 * s, 46 * s, 48 * s
    cy, neck, hip = base - LEG - BODY - R, base - LEG - BODY, base - LEG
    sh = neck + 9 * s
    w = clamp(2.3 * s, 1.5, 3.0)
    o = [pen.line((cx, hip), (cx - 13 * s, base), w, amp=0.35), pen.line((cx, hip), (cx + 13 * s, base), w, amp=0.35),
         pen.line((cx, neck), (cx, hip), w, amp=0.35)]
    if app.get("coat"):  # a lab coat: one outline round the torso, hanging over the tops of the legs, a V collar, a pocket
        o.append(pen.poly([(cx - 4 * s, neck), (cx - 11 * s, neck + 7 * s), (cx - 18 * s, hip + 24 * s), (cx + 18 * s, hip + 24 * s),
                           (cx + 11 * s, neck + 7 * s), (cx + 4 * s, neck)], w, fill=PAPER, jit=0.3))
        o += [pen.line((cx - 4 * s, neck), (cx, neck + 15 * s), w * 0.8, amp=0.2), pen.line((cx + 4 * s, neck), (cx, neck + 15 * s), w * 0.8, amp=0.2),
              pen.line((cx, neck + 15 * s), (cx, hip + 24 * s), w * 0.8, amp=0.3),
              pen.rect(cx + 6 * s, hip, 8 * s, 9 * s, w * 0.7, fill=PAPER, over=0)]
    if pose == "think" and holding:  # the thinking hand rests on the chin; with something in it, hold it out instead
        pose = "hold"
    back, front = ARMS.get(pose, ARMS["stand"])
    for arm in (back, front):  # an upper arm and a forearm: two straight strokes meeting at the elbow
        side = 1 if arm is front else -1
        start = (cx + side * 9 * s, sh) if app.get("coat") else (cx, sh)  # a coat's sleeves leave from its shoulders
        pts = [start] + [(cx + dx * s, sh + dy * s) for dx, dy in arm]
        o += [pen.line(a, b, w, amp=0.35) for a, b in zip(pts, pts[1:])]
    o.append(_holding(pen, holding, cx + front[-1][0] * s, sh + front[-1][1] * s, s, w))
    o.append(pen.ellipse(cx, cy, R, R, w, fill=PAPER, jit=0.012))
    hair = app.get("hair", "none")
    o += _hair(pen, hair, cx, cy, R, w, app.get("hair_tone", "dark"))
    o += _face(pen, cx, cy, s, face, w, app.get("glasses", False))
    top = cy - R * HAIR_TOP.get(hair, 1.0) - 4 * s
    return _flip("".join(o), cx, facing), (cx, top)


# ---------------------------------------------------------------- props
def _num(v):
    """A number as the storyboard wrote it: 25.0 stays 25.0 and 25 stays 25, so a label matches its claim."""
    return str(v)


def _bars(pen, x, y, w, h, spec, fs):
    """Vertical bars from a zero line. Values below zero hang down from it (a signed index such as
    Ivlev's); `min` and `max` set the scale, otherwise it fits the data. A `title` is drawn above."""
    bars = spec["bars"]
    n = len(bars)
    vals = [b["value"] for b in bars]
    hi = spec.get("max") or max(max(vals), 0) or 1
    lo = spec.get("min", min(0, min(vals)))
    pct = "%" if spec.get("unit") == "%" else ""
    show = spec.get("show_values", True)
    fsb = max(11.0, fs * 0.85)
    ticks = [f"{_num(hi)}{pct}"] + ([f"{_num(lo)}{pct}"] if lo < 0 else [])
    tick_w = max(len(t) for t in ticks) * fsb * CHAR_W + 8 if show and spec.get("show_max", True) else 0
    ax = x + max(14, tick_w)
    slot = (x + w - ax - 4) / n
    labs = [wrap(b.get("label", ""), slot - 4, fsb) for b in bars]
    lab_h = max(len(la) for la in labs) * fsb * 1.15 + 8
    title = spec.get("title", "")
    top, bottom = y + fsb + 10 + (fsb * 1.4 if title else 0), y + h - lab_h
    if lo < 0:  # leave room for the value labels of bars that hang below the zero line
        bottom -= fsb * 1.3

    def yv(v):
        return bottom - (v - lo) / (hi - lo) * (bottom - top)

    o = []
    if title:
        o.append(text(ax + (x + w - ax) / 2, y, [title], fsb, anchor="middle"))
    o += [pen.line((ax, top - 4), (ax, bottom), 2.2), pen.line((ax, yv(0)), (x + w, yv(0)), 2.2)]
    if tick_w:
        o.append(text(ax - 5, top - 4 - fsb * 0.2, [ticks[0]], fsb, anchor="end"))
        if lo < 0:
            o.append(text(ax - 5, bottom - fsb * 0.2, [ticks[1]], fsb, anchor="end"))
    for i, b in enumerate(bars):
        bw = min(slot * 0.62, 86)
        cx = ax + slot * (i + 0.5)
        v = clamp(b["value"], lo, hi)
        y0, y1 = yv(0), yv(v)
        fill = PAPER if b.get("style") == "hollow" else INK
        o.append(pen.rect(cx - bw / 2, min(y0, y1), bw, abs(y1 - y0), 2.4, fill=fill, over=1.5))
        if show:
            ly = y1 - fsb * 1.25 if b["value"] >= 0 else y1 + 4
            o.append(text(cx, ly, [f"{_num(b['value'])}{pct}"], fsb, anchor="middle"))
        o.append(text(cx, bottom + 4 + (fsb * 1.3 if lo < 0 else 0), labs[i], fsb, anchor="middle", lh=1.15))
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
                    fc = clamp((cw - 8) / (max(len(c["label"]), 1) * CHAR_W), 9.0, fs)  # shrink a label to fit its card
                    o.append(text(cx0 + cw / 2, top + ch / 2 - fc * 0.55, [c["label"]], fc, anchor="middle"))
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
        o.append(text(x + w / 2, y + h * 0.25 - fs * 0.5, wrap(lab, w - 6, fs * 0.85), fs * 0.85, anchor="middle"))
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
        if c.get("body"):  # a body on the staged character overrides the cast's, so `extra` can be an animal
            app = {**(app or {}), "body": c["body"]}
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
    body = c.get("body") or (cast.get(c["id"], {}).get("appearance") or {}).get("body")
    s = 0.00476 * h * clamp(1 + 0.18 * (w / h - 2.0), 1.0, 1.3) * c.get("scale", 1)
    rise = {"diatom": 108, "penguin": 102, "whale": 96, "krill": 52, "salp": 66}.get(body, 128)  # head height above the feet, at s = 1
    return c.get("y", 0.94) * h - rise * s


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
    extra = max(0.0, need - free)
    talk_h = extra + sum(block_h(li, fs) + 22 for _, li in far)
    # Heads sit roughly in proportion to the scene's height, so a shorter scene lowers the room for speech.
    shrink_ok = float("inf") if not near else (0.0 if extra > 0 else 2.0 * (free - need))
    cap_h = sum(block_h(c, fs) + 16 for c in captions) + (6 if captions else 0)
    return {"fs": fs, "captions": captions, "talk": talk, "cap_h": cap_h, "talk_h": talk_h,
            "scene_nat": scene_nat, "nat_h": PAD + cap_h + talk_h + scene_nat + PAD, "shrink_ok": shrink_ok}


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
        start = clamp(head[0], cx - tw / 2 + 8, cx + tw / 2 - 8)  # the point of the text's lower edge nearest the speaker
        o.append(pen.line((start, bottom + 3), (head[0], head[1] - 8), 2.0, dash=dash))
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
    prev_widths, prev_open = None, False
    for beat in doc["beats"]:
        first = True
        for row in pack_rows(beat["panels"], prev=prev_widths):
            # Two rows of nothing but open panels run together, so the second gets its widest panel outlined.
            all_open = all(p.get("frame", "outlined") == "borderless" for p, _ in row)
            if all_open and prev_open:
                widest = max(range(len(row)), key=lambda i: row[i][1])
                row = [({**p, "frame": "outlined"} if i == widest else p, u) for i, (p, u) in enumerate(row)]
                all_open = False
            prev_widths, prev_open = tuple(u for _, u in row), all_open
            widths = row_geometry(row, usable)
            plans = [plan_panel(p, w, k, cast) for (p, _), w in zip(row, widths)]
            rh = max(pl["nat_h"] for pl in plans)
            label = (beat.get("title") or beat["act"]) if first else None
            items.append({"kind": "row", "h": rh + (30 if label else 0), "label": label, "beat": beat["id"],
                          "label_h": 30 if label else 0, "widths": tuple(u for _, u in row), "all_open": all_open,
                          **_row_limits(row, plans, rh),
                          "draw": _row_drawer(row, widths, plans, rh, label, cast)})
            first = False
    lic_url = _licence_url(src["licence"])
    note = (f'Adapted from “{src["title"]}” by {", ".join(src["authors"])} ({src["year"]})'
            + (f', doi {src["doi"]}' if src.get("doi") else "")
            + f'. Licence: {src["licence"]}. '
            "Condensed into a comic with invented characters and scenes using the science-comic-pipeline; "
            "the paper's authors did not write or endorse this document.")
    colo = wrap(note, usable, 15)
    paper = src.get("url") or (f'https://doi.org/{src["doi"]}' if src.get("doi") else "")
    links = [(f"Read the original paper: {paper}", paper)] if paper else []
    if lic_url:
        links.append((f"Licence terms: {lic_url}", lic_url))

    def draw_colophon(y, c=colo, ls=links):
        """The footer in the caption grey. The pipeline's name and the lines below are links (clickable in a browser
        and in the PDF), underlined but not heavier than the text around them."""
        def inline(line):
            return esc(line).replace(PIPELINE_NAME, f'<a href="{PIPELINE_URL}" target="_blank"><tspan style="text-decoration:underline" font-weight="normal">{PIPELINE_NAME}</tspan></a>')
        spans = "".join(f'<tspan x="{MARGIN:.1f}" dy="{(15 if i == 0 else 18):.1f}">{inline(t)}</tspan>' for i, t in enumerate(c))
        out = [f'<text x="{MARGIN:.1f}" y="{y + 6:.1f}" font-size="15" font-weight="normal" fill="{MID}">{spans}</text>']
        for i, (label, href) in enumerate(ls):
            ly = y + 6 + block_h(c, 15) + 4 + i * 15 * 1.3
            out.append(f'<a href="{esc(href)}" target="_blank">'
                       + text(MARGIN, ly, [label], 15, fill=MID).replace("<text ", '<text style="text-decoration:underline" ', 1) + "</a>")
        return "".join(out)

    items.append({"kind": "colophon", "h": block_h(colo, 15) + len(links) * 15 * 1.3 + 16, "draw": draw_colophon})
    return items


HEIGHT_HINTS = {"short": 0.35, "standard": 1.0, "tall": 2.2}  # how much of a page's spare height a row asks for
GROW_CAP = {"short": 0.1, "standard": 0.5, "tall": 1.0}  # most a row may grow, as a fraction of its natural height
CHART_KINDS = {"bars", "plot", "axis", "pie", "flow", "steps", "stack"}  # props that scale up well with a taller scene


def _row_limits(row, plans, rh):
    """What a row asks of its page: a hint-based appetite, and how rich its content is."""
    hints = [p.get("height", "standard") for p, _ in row]
    hint = "tall" if "tall" in hints else ("short" if all(h == "short" for h in hints) else "standard")
    props = [pr for p, _ in row for pr in (p.get("staging") or {}).get("props", [])]
    chars = [c for p, _ in row for c in (p.get("staging") or {}).get("characters", [])]
    rich = (2.0 * sum(pr["kind"] in CHART_KINDS for pr in props) + 0.7 * len(props) + 0.4 * len(chars)
            + (1.5 if any(p.get("weight") == "full" for p, _ in row) else 0.0)
            + (0.8 if any(p.get("frame", "outlined") == "outlined" for p, _ in row) else 0.0))
    return {"flex": HEIGHT_HINTS[hint], "hint": hint, "rich": rich, "grow": GROW_CAP[hint],
            "scene_nat": max(pl["scene_nat"] for pl in plans), "nat_row": rh,
            "shrink_ok": min(pl["shrink_ok"] for pl in plans)}


def _row_drawer(row, widths, plans, rh, label, cast):
    def draw(y, h=None):
        h = rh if h is None else h
        top = y + (30 if label else 0)
        head = text(MARGIN, y, [label], 18, fill=MID, weight="bold") if label else ""
        return head + "".join(
            f'<g transform="translate({MARGIN + sum(widths[:i]) + GUTTER * i:.1f} {top:.1f})">'
            + draw_panel(p, plans[i], widths[i], h, cast) + "</g>" for i, (p, _) in enumerate(row))
    return draw


def _share_out(rows, avail):
    """Heights for the rows of one page so that they fill `avail`.

    Rows are ranked by richness: the richest ask for the most room and the plainest give a little up,
    so the rows on a page differ in height. A row's own height hint scales its share."""
    rich = [r["rich"] for r in rows]
    lo_r, hi_r = min(rich), max(rich)
    norm = [(x - lo_r) / (hi_r - lo_r) if hi_r > lo_r else 0.5 for x in rich]
    flex = [r["flex"] * (0.35 + 1.65 * n) for r, n in zip(rows, norm)]
    lo = [r["h"] - (min(0.22 * r["scene_nat"], r["shrink_ok"])
                    if (n < 0.3 and r["hint"] != "tall") or r["hint"] == "short" else 0.0)
          for r, n in zip(rows, norm)]
    hi = [r["h"] + r["nat_row"] * r["grow"] * (0.5 + n) for r, n in zip(rows, norm)]
    h = lo[:]
    slack = avail - sum(h)
    for _ in range(25):
        active = [i for i in range(len(h)) if h[i] < hi[i] - 1e-6]
        if slack < 1e-6 or not active:
            break
        total = sum(flex[i] for i in active)
        used = 0.0
        for i in active:
            d = min(slack * flex[i] / total, hi[i] - h[i])
            h[i] += d
            used += d
        slack -= used
    return h


def settle(pages):
    """Re-measure each page: spread its spare height over its rows unevenly, so pages fill and rows differ."""
    top, bottom = MARGIN, PAGE_H - MARGIN - FOOTER_H
    out = []
    for n, page in enumerate(pages):
        items = [it for _, it in page]
        rows = [it for it in items if it["kind"] == "row"]
        fixed = sum(it["h"] for it in items if it["kind"] != "row") + GUTTER * (len(items) - 1)
        natural = fixed + sum(r["h"] for r in rows)
        sparse_last = n == len(pages) - 1 and natural < 0.6 * (bottom - top)
        heights = [r["h"] for r in rows] if (not rows or sparse_last) else _share_out(rows, bottom - top - fixed)
        y, k, placed = top, 0, []
        for it in items:
            if it["kind"] == "row":
                h = heights[k]
                k += 1
            else:
                h = it["h"]
            placed.append((y, it, h))
            y += h + GUTTER
        out.append(placed)
    return out


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
    pages = settle(min(tries, key=lambda pg: len(pg)))
    svgs, placements = [], []
    for n, page in enumerate(pages, 1):
        body = []
        for y, it, h in page:
            body.append(it["draw"](y, h - it["label_h"]) if it["kind"] == "row" else it["draw"](y))
            placements.append({"page": n, "y": y, "h": h, "kind": it["kind"], "beat": it.get("beat")})
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
/* Printing or saving as PDF: one A4 sheet per comic page, nothing else. */
@media print {
  @page { size: A4; margin: 0; }
  html, body { background: #fff !important; margin: 0 !important; padding: 0 !important; }
  .wrap { display: block; max-width: none; margin: 0; }
  .wrap > :not(.page) { display: none; }
  .page { width: 210mm; height: 297mm; box-shadow: none; overflow: hidden; break-inside: avoid;
    break-after: page; page-break-after: always; }
  .page:last-child { break-after: auto; page-break-after: auto; }
  .page svg { display: block; width: 210mm; height: 297mm; }
}
"""


def _licence_url(label):
    """The Creative Commons deed for a label such as "CC BY 4.0" or "CC BY-SA 4.0"; "" for anything else."""
    m = re.match(r"^CC[ -](BY(?:-SA)?|0)(?:[ -](\d\.\d))?$", label.strip(), re.I)
    if not m:
        return ""
    kind = m.group(1).lower()
    if kind == "0":
        return "https://creativecommons.org/publicdomain/zero/1.0/"
    return f"https://creativecommons.org/licenses/{kind}/{m.group(2) or '4.0'}/"


def build_sheet(doc, svgs, standalone=False):
    pages = "".join(f'<div class="page">{s}</div>' for s in svgs)
    body = (f'<title>{esc(doc["meta"]["title"])}</title><meta name="claude:viewport-fit-sides" content="cover">'
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
