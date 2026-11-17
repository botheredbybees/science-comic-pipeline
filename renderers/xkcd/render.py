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
import json
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
from faces import ANIMAL_FACE, FACES, draw_face  # noqa: E402

PAGE_W, PAGE_H, MARGIN, GUTTER = 1000, 1414, 40, 16  # A4 at 1000 units wide
FOOTER_H = 30
PIPELINE_URL = "https://github.com/botheredbybees/science-comic-pipeline"
PIPELINE_NAME = "science-comic-pipeline"
FIT_FACTORS = (0.55, 0.5, 0.45, 0.4, 0.36)  # scene height as a fraction of panel width, tallest first


# ---------------------------------------------------------------- stick figures
HEAD_SCALE = 1.2  # the default head size: a little bigger than the original 1.0, as in a newspaper strip

ARMS = {  # (back arm, front arm): points relative to the shoulder, for a figure facing right
    "stand": ([(-13, 16), (-17, 38)], [(13, 16), (17, 38)]),
    "point": ([(-13, 16), (-17, 38)], [(21, 0), (43, -3)]),
    "hold": ([(-13, 16), (-17, 38)], [(20, 12), (36, 2)]),
    "think": ([(-13, 16), (-17, 38)], [(14, 10), (4, -10)]),
    "shrug": ([(-22, 10), (-26, -6)], [(22, 10), (26, -6)]),
    "up": ([(-18, -10), (-24, -34)], [(18, -10), (24, -34)]),
    "sip": ([(-13, 16), (-17, 38)], [(20, 8), (13, -4)]),  # the mug stops just in front of the mouth, clear of the face
    "sit": ([(-2, 20), (14, 33)], [(10, 20), (27, 32)]),  # hands resting on the lap
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
    if holding == "teacup":  # a small cup held by its handle, the tea bag's tag over the rim, and steam
        top = hy - 8 * s
        tag = [pen.stroke([(hx + 14 * s, top), (hx + 18 * s, top + 5 * s), (hx + 18.5 * s, top + 9 * s)], w * 0.4),
               pen.rect(hx + 16.5 * s, top + 9 * s, 4 * s, 4 * s, w * 0.4, fill=PAPER, over=0)]
        steam = [pen.stroke([(hx + x * s, top - 3 * s), (hx + (x - 2) * s, top - 7 * s), (hx + (x + 2) * s, top - 11 * s), (hx + x * s, top - 15 * s)], w * 0.5)
                 for x in (8, 12)]
        return (pen.stroke([(hx + 4 * s, hy - 5 * s), (hx - 2 * s, hy - 4 * s), (hx - 2 * s, hy + 1 * s), (hx + 4 * s, hy + 1.5 * s)], w * 0.7)
                + pen.stroke([(hx + 3 * s, top), (hx + 5 * s, hy + 6 * s), (hx + 17 * s, hy + 6 * s), (hx + 19 * s, top)], w * 0.8, closed=True, fill=PAPER)
                + "".join(tag) + "".join(steam))
    if holding == "flask":  # a conical flask with a stopper and some liquid
        return (pen.stroke([(hx + 4 * s, hy - 19 * s), (hx + 4 * s, hy - 8 * s), (hx - 3 * s, hy + 6 * s), (hx + 15 * s, hy + 6 * s),
                            (hx + 8 * s, hy - 8 * s), (hx + 8 * s, hy - 19 * s)], w * 0.8, closed=True, fill=PAPER)
                + pen.stroke([(hx - 1 * s, hy + 1 * s), (hx + 12 * s, hy + 1 * s), (hx + 14 * s, hy + 6 * s), (hx - 3 * s, hy + 6 * s)], 0.5, closed=True, fill=SOFT, color=SOFT)
                + pen.line((hx + 3 * s, hy - 19 * s), (hx + 9 * s, hy - 19 * s), w * 0.9, amp=0.1))
    if holding == "magnifier":  # a hand lens: a ring on a handle
        return (pen.line((hx - 1 * s, hy + 3 * s), (hx + 6 * s, hy - 7 * s), w * 1.1, amp=0.2)
                + pen.ellipse(hx + 11 * s, hy - 13 * s, 8 * s, 8 * s, w * 0.9, fill=PAPER, jit=0.01)
                + pen.stroke([(hx + 7 * s, hy - 15 * s), (hx + 9 * s, hy - 18 * s)], w * 0.4, color=MID))
    if holding == "clipboard":
        return (pen.rect(hx - 3 * s, hy - 17 * s, 17 * s, 23 * s, w * 0.8, fill=PAPER, over=0)
                + pen.rect(hx + 1.5 * s, hy - 19.5 * s, 8 * s, 4 * s, w * 0.7, fill=INK, over=0)
                + "".join(pen.line((hx - 0 * s, hy - 11 * s + i * 5 * s), (hx + 11 * s, hy - 11 * s + i * 5 * s), w * 0.45, amp=0.15)
                          for i in range(3)))
    if holding == "flower":  # a flower on a stem held up: six round petals round a centre, and a leaf
        top = (hx + 3 * s, hy - 17 * s)
        petals = "".join(pen.ellipse(top[0] + 4.6 * s * math.cos(a), top[1] + 4.6 * s * math.sin(a), 3.1 * s, 3.1 * s, w * 0.5, fill=SOFT, jit=0.04)
                         for a in (math.tau * k / 6 + 0.3 for k in range(6)))
        return (pen.line((hx - 0.5 * s, hy + 4 * s), (top[0], top[1] + 5 * s), w * 0.8, amp=0.2) + petals
                + pen.ellipse(top[0], top[1], 2.9 * s, 2.9 * s, w * 0.5, fill=PAPER, jit=0.04)
                + pen.stroke([(hx + 1 * s, hy - 4 * s), (hx + 7 * s, hy - 9 * s), (hx + 8 * s, hy - 5 * s), (hx + 2 * s, hy - 3 * s)], w * 0.5, closed=True, fill=SOFT))
    if holding == "photo":  # a framed photograph held by its edge: a hill and a sun in it
        x0, y0 = hx - 2 * s, hy - 20 * s
        return (pen.rect(x0, y0, 17 * s, 22 * s, w * 0.8, fill=PAPER, over=0)
                + pen.rect(x0 + 2.5 * s, y0 + 2.5 * s, 12 * s, 14 * s, w * 0.4, fill=SOFT, over=0)
                + pen.stroke([(x0 + 2.5 * s, y0 + 14 * s), (x0 + 7 * s, y0 + 8 * s), (x0 + 10 * s, y0 + 12 * s), (x0 + 14.5 * s, y0 + 7 * s)], w * 0.45, color=MID)
                + f'<circle cx="{x0 + 11.5 * s:.1f}" cy="{y0 + 5.5 * s:.1f}" r="{1.5 * s:.1f}" fill="{INK}"/>')
    if holding == "book":  # a closed book held up, its spine on the hand's side, two short lines for a title
        x0, y0 = hx - 2 * s, hy - 20 * s
        return (pen.rect(x0, y0, 16 * s, 22 * s, w * 0.8, fill=PAPER, over=0)
                + pen.rect(x0, y0, 3.2 * s, 22 * s, w * 0.6, fill=SOFT, over=0)
                + pen.line((x0 + 6 * s, y0 + 6 * s), (x0 + 13 * s, y0 + 6 * s), w * 0.5, amp=0.1)
                + pen.line((x0 + 6 * s, y0 + 10 * s), (x0 + 11 * s, y0 + 10 * s), w * 0.5, amp=0.1))
    if holding == "paper":  # a sheet held up with a folded corner and three lines of writing
        x0, y0 = hx - 2 * s, hy - 20 * s
        return (pen.poly([(x0, y0), (x0 + 11 * s, y0), (x0 + 16 * s, y0 + 5 * s), (x0 + 16 * s, y0 + 22 * s), (x0, y0 + 22 * s)], w * 0.8, fill=PAPER, jit=0.1)
                + pen.line((x0 + 11 * s, y0), (x0 + 11 * s, y0 + 5 * s), w * 0.5, amp=0.1) + pen.line((x0 + 11 * s, y0 + 5 * s), (x0 + 16 * s, y0 + 5 * s), w * 0.5, amp=0.1)
                + "".join(pen.line((x0 + 3 * s, y0 + (9 + 4 * i) * s), (x0 + (13 - i) * s, y0 + (9 + 4 * i) * s), w * 0.4, amp=0.1) for i in range(3)))
    return ""


def _face(pen, cx, cy, s, face, w, glasses=False):
    """Eyes, optional glasses and a mouth, for a face centred near (cx, cy), looking right. The five original faces are
    drawn here; every other face is drawn by faces.draw_face (brows, marks and more eye and mouth shapes)."""
    if face in FACES:
        return draw_face(pen, cx, cy, s, face, w, glasses)
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
    back, front = ARMS.get("stand" if pose == "sit" else pose, ARMS["stand"])
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
HAIR_CAP = {  # the outline of hair that covers the top and back of the head, ending in a fringe that stops well above the eyes
    "bob": [(0.95, -0.4), (0.62, -0.95), (0.0, -1.1), (-0.8, -0.95), (-1.14, -0.25), (-1.12, 0.5), (-0.8, 0.7), (-0.6, 0.25),
            (-0.5, -0.3), (0.0, -0.74), (0.5, -0.7)],
    "long": [(0.95, -0.4), (0.62, -0.95), (0.0, -1.1), (-0.8, -0.95), (-1.18, -0.15), (-1.2, 1.0), (-1.0, 1.8), (-0.5, 1.85),
             (-0.55, 0.55), (-0.5, -0.3), (0.0, -0.74), (0.5, -0.7)],
    "shoulder": [(0.95, -0.4), (0.62, -0.95), (0.0, -1.1), (-0.8, -0.95), (-1.16, -0.15), (-1.2, 0.7), (-1.05, 1.35), (-0.6, 1.4),
                 (-0.55, 0.5), (-0.5, -0.3), (0.0, -0.74), (0.5, -0.7)],
    "short": [(0.92, -0.38), (0.6, -0.92), (0.0, -1.06), (-0.8, -0.9), (-1.06, -0.25), (-0.88, 0.15), (-0.5, -0.2), (0.0, -0.68), (0.5, -0.64)],
}
PONYTAIL = [(-1.02, -0.58), (-1.5, -0.5), (-1.88, -0.12), (-2.05, 0.5), (-2.2, 1.18), (-1.98, 0.98), (-1.9, 1.42), (-1.7, 1.02), (-1.5, 1.3), (-1.42, 0.7), (-1.2, -0.2), (-1.02, -0.4)]  # narrow at the tie, flaring to pointed locks
SPIKES = [(-1.0, -0.1), (-1.25, -0.6), (-0.85, -0.74), (-0.85, -1.15), (-0.36, -0.94), (0.0, -1.32), (0.32, -0.94), (0.8, -1.15),
          (0.82, -0.74), (1.08, -0.6), (0.82, -0.36), (0.45, -0.78), (0.0, -0.66), (-0.45, -0.78), (-0.78, -0.25)]

BEANIE = [(-1.2, -0.42), (-1.18, -1.05), (-0.62, -1.62), (0.0, -1.76), (0.62, -1.62), (1.18, -1.05), (1.22, -0.42),
          (0.6, -0.5), (0.0, -0.54), (-0.6, -0.5)]


HARDHAT = [(-1.04, -0.78), (-1.05, -1.12), (-0.62, -1.62), (0.0, -1.78), (0.62, -1.62), (1.05, -1.12), (1.04, -0.78)]  # the dome of a hard hat, clear of the eyes and glasses


def _bun(pen, cx, cy, R, w, fill):
    """A hair bun on the crown: a small ball with a curl in it (in the contrasting colour) so that a dark bun still reads as a bun."""
    bx, by, br = cx - 0.5 * R, cy - 1.18 * R, 0.34 * R
    curl = INK if fill != INK else PAPER
    return [f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{br:.1f}" fill="{fill}" stroke="{INK}" stroke-width="{w:.1f}"/>',
            pen.stroke([(bx - 0.55 * br, by + 0.1 * br), (bx, by - 0.5 * br), (bx + 0.55 * br, by + 0.1 * br)], w * 0.45, color=curl)]


def _hair(pen, kind, cx, cy, R, w, tone="dark"):
    """The hair or hat for a head of radius R, drawn over the head circle and under the face.
    Dark hair is solid black; light (blond) hair is the same shape as an outline with a white fill."""
    fill = {"dark": INK, "grey": HAIR_GREY}.get(tone, PAPER)

    def P(pts):
        return [(cx + x * R, cy + y * R) for x, y in pts]
    if kind in ("bob", "long", "shoulder", "short"):
        return [pen.stroke(P(HAIR_CAP[kind]), w, closed=True, fill=fill)]
    if kind in ("beret", "boater", "flatcap"):  # hats take the tone as their colour: dark is black, light is white, grey is grey
        return _hat(pen, kind, cx, cy, R, w, fill, tone)
    if kind in ("ponytail", "bun"):
        o = []
        if kind == "bun":  # the bun goes under the cap, so that a light bun's outline does not cross the hair
            o += _bun(pen, cx, cy, R, w, fill)
        o.append(pen.stroke(P(HAIR_CAP["short"]), w, closed=True, fill=fill))
        if kind == "ponytail":
            o.append(pen.poly(P(PONYTAIL), w, fill=fill, jit=0.12))
        return o
    if kind == "spiky":
        return [pen.poly(P(SPIKES), w, fill=fill, jit=0.4)]
    if kind == "beanie":
        return [pen.stroke(P(BEANIE), w, closed=True, fill=PAPER),
                pen.line((cx - 1.2 * R, cy - 0.78 * R), (cx + 1.2 * R, cy - 0.78 * R), w * 0.8, amp=0.3),
                f'<circle cx="{cx + 0.05 * R:.1f}" cy="{cy - 1.9 * R:.1f}" r="{0.3 * R:.1f}" fill="{INK}"/>']
    if kind == "hardhat":  # a dome with a ridge, and a brim that sticks out in front
        return [pen.stroke(P(HARDHAT), w, closed=True, fill=SOFT),
                pen.stroke([(cx + 0.0 * R, cy - 1.76 * R), (cx + 0.05 * R, cy - 1.3 * R), (cx + 0.02 * R, cy - 0.8 * R)], w * 0.7, color=INK),
                pen.poly([(cx - 1.12 * R, cy - 0.78 * R), (cx + 1.5 * R, cy - 0.78 * R), (cx + 1.54 * R, cy - 0.6 * R), (cx - 1.1 * R, cy - 0.62 * R)], w, fill=SOFT, jit=0.1)]
    return []


HAIR_GREY = MID  # grey hair: the palette's mid grey, with the usual outline


def _hat(pen, kind, cx, cy, R, w, fill, tone):
    """A beret (a soft flat disc with a stalk), a boater (a flat-topped crown, a wide flat brim and a band) or a flat cap (a low
    dome with a short peak). Each is drawn a little smaller than the head's width and tilted, as a hat is worn, not level."""
    trim = PAPER if tone == "dark" else INK  # the band and the stalk show against the hat

    def T(pts, size, tilt, dx=0.0):  # scale about where the hat sits on the head, tilt it (negative lifts the front), shift it (negative: back), place it on the head
        px, py = 0.0, -0.8
        c, sn = math.cos(tilt), math.sin(tilt)
        return [(cx + (px + dx + (x - px) * size * c - (y - py) * size * sn) * R, cy + (py + (x - px) * size * sn + (y - py) * size * c) * R) for x, y in pts]
    if kind == "beret":
        body = [(-1.4, -0.62), (-1.45, -1.0), (-1.0, -1.42), (-0.2, -1.58), (0.7, -1.42), (1.2, -1.05), (1.18, -0.7), (0.5, -0.78), (-0.4, -0.72)]
        a, b = T([(-0.15, -1.58), (-0.1, -1.88)], 0.68, -0.3, -0.25)
        return [pen.stroke(T(body, 0.68, -0.3, -0.25), w, closed=True, fill=fill), pen.line(a, b, w * 0.9, amp=0.1)]
    if kind == "boater":
        brim = [(1.8 * math.cos(t * math.tau / 20), -0.86 + 0.2 * math.sin(t * math.tau / 20)) for t in range(20)]
        crown = [(-0.9, -0.88), (-0.88, -1.95), (0.9, -1.95), (0.92, -0.88)]
        band = [(-0.895, -1.18), (0.905, -1.18), (0.9, -1.42), (-0.89, -1.42)]  # outlined at both ends so the crown does not float
        return [pen.stroke(T(brim, 0.8, -0.15), w, closed=True, fill=fill), pen.poly(T(crown, 0.8, -0.15), w, fill=fill, jit=0.15),
                pen.poly(T(band, 0.8, -0.15), w * 0.8, fill=trim, jit=0.1)]
    body = [(-1.2, -0.7), (-1.15, -1.1), (-0.6, -1.45), (0.3, -1.55), (1.0, -1.25), (1.2, -0.85), (1.05, -0.7)]  # flat cap
    peak = [(0.55, -0.85), (1.9, -0.72), (1.95, -0.52), (0.7, -0.6)]
    return [pen.stroke(T(peak, 0.8, -0.1), w, closed=True, fill=fill),  # the peak first, so the dome covers where they meet
            pen.stroke(T(body, 0.8, -0.1), w, closed=True, fill=fill)]


HAIR_TOP = {"bob": 1.1, "long": 1.1, "shoulder": 1.1, "short": 1.06, "ponytail": 1.1, "bun": 1.65, "spiky": 1.4, "beanie": 1.85, "hardhat": 1.85,
            "beret": 1.6, "boater": 1.75, "flatcap": 1.45}  # head radii above the head's centre


def _outfit(pen, kind, cx, neck, hip, s, w):
    """A garment over the torso, drawn after the torso line and before the arms: `floatcoat` (a chunky float jacket with a
    collar, waist strap and reflective patches), `parka` (a long quilted jacket; its hood is drawn by `_hood`) or `hivis`
    (a sleeveless high-visibility vest with reflective bands)."""
    if kind == "parka":
        o = [pen.poly([(cx - 6 * s, neck), (cx - 14 * s, neck + 6 * s), (cx - 18 * s, hip + 22 * s), (cx + 18 * s, hip + 22 * s),
                       (cx + 14 * s, neck + 6 * s), (cx + 6 * s, neck)], w, fill=SOFT, jit=0.3)]
        for dy in (16, 28, 40):  # the quilting
            o.append(pen.stroke([(cx - 14 * s, neck + dy * s), (cx, neck + (dy + 2) * s), (cx + 14 * s, neck + dy * s)], w * 0.5, color=MID))
        o += [pen.line((cx, neck + 6 * s), (cx, hip + 22 * s), w * 0.8, amp=0.25),
              pen.line((cx + 5 * s, hip + 4 * s), (cx + 13 * s, hip + 11 * s), w * 0.6, amp=0.1),
              pen.line((cx - 5 * s, hip + 4 * s), (cx - 13 * s, hip + 11 * s), w * 0.6, amp=0.1)]
        return o
    if kind == "floatcoat":
        o = [pen.poly([(cx - 7 * s, neck), (cx - 15 * s, neck + 4 * s), (cx - 17 * s, neck + 24 * s), (cx - 15 * s, hip + 8 * s),
                       (cx + 15 * s, hip + 8 * s), (cx + 17 * s, neck + 24 * s), (cx + 15 * s, neck + 4 * s), (cx + 7 * s, neck)], w, fill=INK, jit=0.3)]
        o += [pen.line((cx, neck + 6 * s), (cx, hip + 8 * s), w * 0.8, amp=0.2, color=PAPER),
              pen.rect(cx - 16 * s, hip - 4 * s, 32 * s, 5 * s, w * 0.7, fill=PAPER, over=0.2),  # the waist strap
              pen.rect(cx - 3 * s, hip - 5 * s, 6 * s, 7 * s, w * 0.6, fill=INK, over=0),  # its buckle
              pen.rect(cx - 12 * s, neck + 10 * s, 7 * s, 6 * s, w * 0.5, fill=PAPER, over=0),  # reflective patches
              pen.rect(cx + 5 * s, neck + 10 * s, 7 * s, 6 * s, w * 0.5, fill=PAPER, over=0),
              pen.ellipse(cx, neck + 1 * s, 11 * s, 4 * s, w * 0.8, fill=MID)]  # the collar
        return o
    if kind == "hivis":
        o = [pen.poly([(cx - 9 * s, neck), (cx - 14 * s, neck + 10 * s), (cx - 14 * s, hip + 8 * s), (cx + 14 * s, hip + 8 * s),
                       (cx + 14 * s, neck + 10 * s), (cx + 9 * s, neck)], w, fill=SOFT, jit=0.4)]
        for sgn in (-1, 1):  # the V of the neck, as two soft curves
            o.append(pen.stroke([(cx + sgn * 9 * s, neck), (cx + sgn * (4.5 + pen.n(0.4)) * s, neck + 5 * s), (cx, neck + 11 * s)], w * 0.7))
        for dy in (19, 32):  # the reflective bands wrap round the body, so each one sags in the middle and wobbles
            y0 = neck + dy * s
            top = [(cx + x * s, y0 + sag * s + pen.n(0.25 * s)) for x, sag in ((-14, 0), (-7, 0.8), (0, 1.2), (7, 0.8), (14, 0))]
            bot = [(x, y + 3.4 * s) for x, y in reversed(top)]
            o.append(pen.stroke(top + bot, w * 0.6, closed=True, fill=PAPER))
        for dx in (-7, 7):  # the shoulder-to-hem stripes: loose white bands with an outline, not rulers
            xs = [(neck + 8 * s, 0.0), (neck + 22 * s, 0.12), (hip + 8 * s, 0.05)]
            left = [(cx + (dx - 1.3) * s * (1 + k) + pen.n(0.3 * s), y) for y, k in xs]
            right = [(cx + (dx + 1.3) * s * (1 + k) + pen.n(0.3 * s), y) for y, k in reversed(xs)]
            o.append(pen.stroke(left + right, w * 0.5, closed=True, fill=PAPER))
        return o
    return []


def _hood(pen, cx, cy, R, w):
    """The hood of a parka, up: a ring round the head with a fur edge. Drawn before the head, so the face shows inside it."""
    o = [pen.ellipse(cx - 0.05 * R, cy + 0.05 * R, 1.45 * R, 1.42 * R, w, fill=SOFT)]
    for k in range(18):  # the fur trim: short strokes round the edge
        a = math.tau * k / 18
        r0, r1 = 1.42 * R, 1.62 * R
        o.append(pen.line((cx - 0.05 * R + r0 * math.cos(a), cy + 0.05 * R + r0 * math.sin(a)), (cx - 0.05 * R + r1 * math.cos(a), cy + 0.05 * R + r1 * math.sin(a)), w * 0.6, amp=0.1))
    return o


def figure(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """Draw one figure (a stick figure, or a diatom if appearance.body is 'diatom'); return (svg, head point)."""
    app = app or {}
    if app.get("body") == "diatom":
        return _diatom(pen, cx, base, s, pose, face, facing, holding, app)
    if app.get("body") in ANIMALS:
        return ANIMALS[app["body"]](pen, cx, base, s, pose, ANIMAL_FACE.get(face, face), facing, holding, app)
    seated = pose == "sit"  # sitting: the hips at seat height, the thighs forward, the shins down
    hs = float(app.get("head_scale", HEAD_SCALE))  # the head relative to the body: the face and hair scale with it
    R, BODY, LEG = 15 * s * hs, 46 * s, (37 if seated else 48) * s
    cy, neck, hip = base - LEG - BODY - R, base - LEG - BODY, base - LEG
    sh = neck + 9 * s
    w = clamp(2.3 * s, 1.5, 3.0)
    if seated:
        legs = [pen.line((cx, hip), (cx + 25 * s, hip + 1 * s), w, amp=0.35), pen.line((cx + 25 * s, hip + 1 * s), (cx + 26 * s, base), w, amp=0.35),
                pen.line((cx + 26 * s, base), (cx + 32 * s, base), w, amp=0.2),
                pen.line((cx, hip), (cx + 20 * s, hip + 4 * s), w, amp=0.35), pen.line((cx + 20 * s, hip + 4 * s), (cx + 21 * s, base), w, amp=0.35),
                pen.line((cx + 21 * s, base), (cx + 27 * s, base), w, amp=0.2)]
    else:
        legs = [pen.line((cx, hip), (cx - 13 * s, base), w, amp=0.35), pen.line((cx, hip), (cx + 13 * s, base), w, amp=0.35)]
    o = legs + [pen.line((cx, neck), (cx, hip), w, amp=0.35)]
    outfit = app.get("outfit")
    if outfit:
        o += _outfit(pen, outfit, cx, neck, hip, s, w)
    elif app.get("coat"):  # a lab coat: one outline round the torso, hanging over the tops of the legs, a V collar, a pocket
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
        sleeved = app.get("coat") or outfit in ("parka", "floatcoat", "hivis")
        start = (cx + side * 9 * s, sh) if sleeved else (cx, sh)  # a coat's sleeves leave from its shoulders
        pts = [start] + [(cx + dx * s, sh + dy * s) for dx, dy in arm]
        o += [pen.line(a, b, w, amp=0.35) for a, b in zip(pts, pts[1:])]
    o.append(_holding(pen, holding, cx + front[-1][0] * s, sh + front[-1][1] * s, s, w))
    if outfit == "parka":
        o += _hood(pen, cx, cy, R, w)
    o.append(pen.ellipse(cx, cy, R, R, w, fill=PAPER, jit=0.012))
    hair = app.get("hair", "none")
    o += _hair(pen, hair, cx, cy, R, w, app.get("hair_tone", "dark"))
    o += _face(pen, cx, cy, s * hs, face, w, app.get("glasses", False))
    top = cy - R * max(HAIR_TOP.get(hair, 1.0), 1.7 if outfit == "parka" else 0) - 4 * s
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
    # with no `max` set the top of the scale is the tallest bar, whose own value label already says the number: do not print it twice
    echo = "max" not in spec and lo >= 0 and hi in vals
    tick_w = max(len(t) for t in ticks) * fsb * CHAR_W + 8 if show and spec.get("show_max", True) and not echo else 0
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
    elif k == "paper":
        o.append(pen.rect(x, y, w, h, 2.4, fill=PAPER, over=1))
        o.append(pen.line((x + w - 14, y), (x + w, y + 14), 1.6, amp=0.2))
        top = y + 10
        if lab:
            o.append(text(x + w / 2, y + 8, [lab], fs * 1.05, anchor="middle"))
            top += fs * 1.4
        o += [pen.line((x + 10, yy), (x + w - 10, yy), 1.2, amp=0.5, color=MID) for yy in
              [top + i * 13 for i in range(max(0, int((y + h - 10 - top) / 13)))]]
    elif k == "picture":
        o.append(pen.rect(x, y, w, h, 2.8, fill=PAPER, over=1))
        if "staging" in p:
            o.append(stage(pen, x + 6, y + 6, w - 12, h - 12, p["staging"], cast, fs * 0.8)[0])
    elif k == "desk":
        o.append(pen.rect(x, y, w, h, 2.6, fill=PAPER, over=0))
    elif k == "label":
        size = {"small": 0.8, "large": 1.3}.get(p.get("size"), 1.0)
        o.append(text(x, y - fs * size * 0.5, [lab], fs * size, anchor="middle"))
    else:  # box: the fallback for anything else; it grows to hold its words and centres them
        blines = wrap(lab, w - 10, fs)
        bh = max(h, block_h(blines, fs, 1.2) + 12)
        o.append(pen.rect(x, y, w, bh, 2.2, fill=PAPER))
        o.append(text(x + w / 2, y + max(6, (bh - block_h(blines, fs, 1.2)) / 2), blines, fs, anchor="middle"))
    return "".join(o)


CLOSE_HEAD = (0.54, 0.42)  # a close shot's head as a share of the scene's height: one figure, two
CLOSE_CHIN = 0.86  # where the chin sits, as a share of the scene's height: below it the neck and shoulders are cropped


def shot_characters(st, cast, w, h, base_s):
    """Fill in the scale and place of each figure from the staging's `shot`, for whatever the author left out.

    `close` makes the head a little over half of the scene's height (one figure) or just over two fifths (two), with the chin clear of the scene's foot and the neck and shoulders cropped there (the paper's caption sits under the scene, so nothing may spill past it); `wide` makes the
    figures small and sets them a little above the foot of the panel with a ground line under them. A figure's own `scale`, `x` or
    `y` always wins, and no `shot` (or `mid`) leaves every figure exactly as it was."""
    chars = st.get("characters", [])
    shot = st.get("shot", "mid")
    if shot == "mid" or not chars:
        return chars
    out, open_slots = [], [c for c in chars if "scale" not in c]
    for i, c in enumerate(chars):
        c = dict(c)
        if shot == "wide":
            c.setdefault("scale", 0.45)
            c.setdefault("y", 0.8)
        else:  # close
            app = cast.get(c["id"], {}).get("appearance") or {}
            hs = float(app.get("head_scale", HEAD_SCALE))
            across = 0.5 if len(chars) == 1 else 0.3 + 0.4 * i / max(len(chars) - 1, 1)
            c.setdefault("x", round(across, 3))
            if "scale" not in c:
                c["scale"] = CLOSE_HEAD[len(open_slots) != 1] * h / (30 * hs * base_s)
            if "y" not in c:
                body = c.get("body") or app.get("body") or "stick"
                if body == "stick":  # the head's centre sits this many units above the feet (legs, body and the head's radius)
                    up = (37 if c.get("pose") == "sit" else 48) + 46 + 15 * hs
                else:  # animals and diatoms: the point figure() returns for the head, at scale 1
                    _, (_hx, hy) = figure(Pen(0), 0.0, 0.0, 1.0, c.get("pose", "stand"), "neutral", "right", None, {**app, "body": body})
                    up = -hy
                c["y"] = (CLOSE_CHIN - CLOSE_HEAD[len(open_slots) != 1] / 2) + up * base_s * c["scale"] / h
        out.append(c)
    return out


def stage(pen, x, y, w, h, st, cast, fs):
    """Draw a staging block into the box; return (svg, {character id: head position})."""
    props = st.get("props", [])
    split = next((i for i, p in enumerate(props) if p["kind"] == "desk"), len(props))
    front = [p for i, p in enumerate(props) if p.get("front") and i < split]  # drawn after the characters, whatever their place in the list
    props = [p for i, p in enumerate(props) if not (p.get("front") and i < split)]
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
    chars = shot_characters(st, cast, w, h, base_s)
    if st.get("shot") == "wide" and chars and st.get("ground", True):  # a line under the feet, so small figures stand somewhere
        gy = y + max(c.get("y", 0.94) for c in chars) * h + 3
        out.append(pen.line((x, gy), (x + w, gy), 2.0, amp=1.0, color=MID))
    for c in chars:
        app = cast.get(c["id"], {}).get("appearance")
        if c.get("body"):  # a body on the staged character overrides the cast's, so `extra` can be an animal
            app = {**(app or {}), "body": c["body"]}
        svg, head = figure(pen, x + c.get("x", 0.5) * w, y + c.get("y", 0.94) * h, base_s * c.get("scale", 1),
                           c.get("pose", "stand"), c.get("face", "neutral"), c.get("facing", "right"),
                           c.get("holding"), app)
        out.append(svg)
        heads.setdefault(c["id"], head)
    for p in props[split:] + front:
        draw(p)
    if st.get("split"):  # two stagings, a line between them, words with each
        labels = st.get("split_labels") or []
        for i, cell in enumerate(split_cells(st, x, y, w, h, fs)):
            kind, geom = cell["frame"]
            if kind == "rect":
                out.append(pen.rect(*geom, 2.4, fill=PAPER, over=1))
            else:  # a slanted divider: each half is a wedge, and its staging is clipped to it
                out.append(pen.poly(geom, 2.4, fill=PAPER, jit=0.6))
            if i < len(labels) and labels[i]:
                lx, ly, anchor = cell["label"]
                out.append(text(lx, ly, [labels[i]], fs * 0.9, anchor=anchor))
            svg, hd = stage(pen, *cell["sub"], st["split"][i], cast, fs * 0.8)
            if kind == "poly":
                cid = f"split-{pen.seed}-{int(x)}-{int(y)}-{i}".replace(".", "-")
                pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in geom)
                svg = f'<clipPath id="{cid}"><polygon points="{pts}"/></clipPath><g clip-path="url(#{cid})">{svg}</g>'
            out.append(svg)
            for k, v in hd.items():
                heads[f"{k}@{i + 1}"] = v  # a speech line's `cell` picks this frame's figure when the same character is in several
                heads.setdefault(k, v)
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
    rise = {"diatom": 108, "penguin": 102, "whale": 96, "krill": 52, "salp": 66, "copepod": 92, "fish": 62,
            "worm": 42, "jellyfish": 108, "urchin": 62, "seal": 56, "seabird": 88, "moss": 62, "bacterium": 50, "seastar": 48,
            "dinoflagellate": 100, "squid": 54, "amphipod": 82, "puppet": 130}.get(body, 128)  # head height above the feet, at s = 1
    return c.get("y", 0.94) * h - rise * s


def split_cells(st, x, y, w, h, fs):
    """Where the two halves of a split screen go, for `split_direction`: `side` (the default: left and right, a vertical divider), `stack` (top and
    bottom, a horizontal divider) or `slope` (two wedges cut by a slanted divider; each staging is drawn in the widest rectangle that fits its wedge, so nothing crosses the line).
    Returns two dicts: `frame` (`rect` x y w h, or `poly` points), `sub` (the box the half's staging is drawn into) and `label` (x, y, anchor)."""
    labelled = any(st.get("split_labels") or [])
    top = fs * 1.3 if labelled else 0.0
    gap = 12.0
    mode = st.get("split_direction", "side")
    if mode == "stack":
        half = (h - gap - 2 * top) / 2
        cells = []
        for i in range(2):
            cy = y + i * (half + gap + top) + top
            cells.append({"frame": ("rect", (x, cy, w, half)), "sub": (x + 6, cy + 6, w - 12, half - 12), "label": (x + w / 2, cy - top, "middle")})
        return cells
    if mode == "slope":
        lean = w * 0.12  # the divider runs from the top edge at 0.5 w + lean to the bottom edge at 0.5 w - lean
        tx, bx = x + w / 2 + lean, x + w / 2 - lean
        left = [(x, y), (tx - gap / 2, y), (bx - gap / 2, y + h), (x, y + h)]
        right = [(tx + gap / 2, y), (x + w, y), (x + w, y + h), (bx + gap / 2, y + h)]
        inner = w / 2 - lean - gap / 2  # the widest rectangle that fits each wedge: figures placed in it cannot cross the divider
        return [{"frame": ("poly", left), "sub": (x, y, inner, h), "label": (x + 8, y + 4, "start")},
                {"frame": ("poly", right), "sub": (x + w - inner, y, inner, h), "label": (x + w - 8, y + h - fs * 1.3, "end")}]
    n = max(2, len(st.get("split") or []))  # a strip: three or four frames side by side
    half = (w - gap * (n - 1)) / n
    return [{"frame": ("rect", (x + i * (half + gap), y + top, half, h - top)), "sub": (x + i * (half + gap) + 6, y + top + 6, half - 12, h - top - 12),
             "label": (x + i * (half + gap) + half / 2, y, "middle")} for i in range(n)]


def staged_offsets(st, cast, w, h):
    """{character id: how far below the top of the scene its head sits} for a staging, including both halves of a split screen."""
    st = st or {}
    out = {c["id"]: _head_offset(c, cast, w, h) for c in st.get("characters", [])}
    if st.get("split"):
        for n, (cell, sub) in enumerate(zip(split_cells(st, 0, 0, w, h, FONT_SIZE), st["split"]), 1):
            _, sy, sw, sh = cell["sub"]
            for k, v in staged_offsets(sub, cast, sw, sh).items():
                if "@" not in k:
                    out[f"{k}@{n}"] = v + sy  # `id@n`: that frame's figure, for a speech line's `cell`
                out.setdefault(k, v + sy)
    return out


def speaker_key(s):
    """What a speech line looks up in the heads and offsets: the speaker's id, or `id@cell` when the line names a frame."""
    return f'{s["speaker"]}@{s["cell"]}' if s.get("cell") else s["speaker"]


def cell_box(staging, cell, x, y, w, h, fs):
    """(left, right) of a numbered frame of a split screen, or None when the staging has no such frame."""
    cells = split_cells(staging, x, y, w, h, fs) if (staging or {}).get("split") else []
    if not cell or cell > len(cells) or cells[cell - 1]["frame"][0] != "rect":
        return None
    fx, _, fw, _ = cells[cell - 1]["frame"][1]
    return fx, fx + fw


def speech_room(panel, s, inner, fs):
    """The width a speech line is first wrapped to: most of the panel, or the frame of a strip it is in."""
    room = min(inner * 0.6, 260)
    frame = cell_box(panel.get("staging"), s.get("cell"), 0, 0, inner, 300, fs)
    if frame:  # a line in one frame of a strip stays inside that frame
        room = min(room, frame[1] - frame[0] - 16)
    return room


def plan_panel(panel, w, k=0.55, cast=None):
    """Work out the text blocks and the natural height of a panel of width w."""
    cast = cast or {}
    fs = panel_font(w)
    inner = w - 2 * PAD
    staged = staged_offsets(panel.get("staging"), cast, inner, clamp(k * w, 150, 520 * k))
    captions, talk = [], []
    for s in panel.get("speech", []):
        kind = s.get("kind", "say")
        if kind == "caption":
            captions.append(wrap(s["text"], inner - 16, fs))
        else:
            shown = s["text"] if "staging" in panel else f'{s["speaker"].replace("_", " ").title()}: {s["text"]}'
            if kind == "think":
                shown = f"\u201c{shown}\u201d"
            talk.append((s, wrap(shown, speech_room(panel, s, inner, fs), fs)))
    scene_nat = clamp(k * w, 150, 520 * k)
    near = [(s, li) for s, li in talk if speaker_key(s) in staged]
    far = [(s, li) for s, li in talk if speaker_key(s) not in staged]
    # Speech sits just above its speaker's head; the scene only needs extra headroom when the head is too low.
    # Lines in different frames of a strip sit side by side, so only the lines of one frame (or all of them, with no frames) stack.
    stacks = {}
    for s, li in near:
        stacks[s.get("cell")] = stacks.get(s.get("cell"), 0) + block_h(li, fs) + SPEECH_GAP
    need = max(stacks.values(), default=0)
    free = min((staged[speaker_key(s)] for s, _ in near), default=0)
    extra = max(0.0, need - free)
    talk_h = extra + sum(block_h(li, fs) + 22 for _, li in far)
    # Heads sit roughly in proportion to the scene's height, so a shorter scene lowers the room for speech.
    shrink_ok = float("inf") if not near else (0.0 if extra > 0 else 2.0 * (free - need))
    cap_h = sum(block_h(c, fs) + 16 + 6 for c in captions)  # the captions sit under the picture, each with a 6 px gap above it
    return {"fs": fs, "captions": captions, "talk": talk, "cap_h": cap_h, "talk_h": talk_h,
            "scene_nat": scene_nat, "nat_h": PAD + cap_h + talk_h + scene_nat + PAD, "shrink_ok": shrink_ok}


BACKDROP = {"desk", "seaice", "iceshelf", "mixedlayer", "skyline", "livingroom", "stage"}  # props a figure stands in front of: speech may cross them


_INK = {}


def ink_box(svg):
    """The box (x0, y0, x1, y1) that the drawing in an SVG fragment covers, from its paths, circles, ellipses, rectangles and text; None if it draws nothing.
    A prop's declared box is only where it is placed: many props draw well inside it, and speech may use the empty part."""
    xs, ys = [], []
    for d in re.findall(r'<path d="([^"]+)"', svg):
        n = [float(v) for v in re.findall(r"-?\d+\.?\d*", d)]
        xs += n[0::2]
        ys += n[1::2]
    for cx, cy, rx, ry in re.findall(r'<(?:circle|ellipse) cx="([-\d.]+)" cy="([-\d.]+)" r[x]?="([-\d.]+)"(?: ry="([-\d.]+)")?', svg):
        ry = ry or rx
        xs += [float(cx) - float(rx), float(cx) + float(rx)]
        ys += [float(cy) - float(ry), float(cy) + float(ry)]
    for x, y, fs, anchor, body in re.findall(r'<text x="([-\d.]+)" y="([-\d.]+)" font-size="([\d.]+)" text-anchor="(\w+)"[^>]*>(.*?)</text>', svg):
        rows = re.findall(r">([^<]*)</tspan>", body)
        wd = max((len(r) for r in rows), default=0) * float(fs) * CHAR_W
        x = float(x)
        x0 = x - wd / 2 if anchor == "middle" else (x - wd if anchor == "end" else x)
        xs += [x0, x0 + wd]
        ys += [float(y), float(y) + len(rows) * float(fs) * 1.2]
    return (min(xs), min(ys), max(xs), max(ys)) if xs and ys else None


def speech_obstacles(st, x, y, w, h, fs):
    """Boxes (x0, y0, x1, y1), in the staging box's own coordinates, of what the props in it draw: where a speech line must not go.

    Backdrops (a desk, sea ice, a skyline) are left out, and so are the characters: speech is placed above its own speaker's head and two speakers
    are stacked apart from each other already. Both halves of a split screen are searched."""
    out = []
    for p in (st or {}).get("props", []):
        k = p["kind"]
        if k in BACKDROP:
            continue
        px, py = x + p.get("x", 0) * w, y + p.get("y", 0) * h
        if k == "arrow":
            qx, qy = x + p.get("x2", 0) * w, y + p.get("y2", 0) * h
            out.append((min(px, qx) - 4, min(py, qy) - 4, max(px, qx) + 4, max(py, qy) + 4))
            continue
        pw, ph = p.get("w", 0.3) * w, p.get("h", 0.3) * h
        if k == "label":
            size = {"small": 0.8, "large": 1.3}.get(p.get("size"), 1.0)
            tw = len(p.get("label", "")) * fs * size * CHAR_W
            out.append((px - tw / 2, py - fs * size * 0.5, px + tw / 2, py + fs * size * 0.7))
            continue
        box = (px, py, px + pw, py + ph)
        if k in EXTRA or k == "bars":  # these draw inside their box: measure what they draw
            key = (json.dumps(p, sort_keys=True, default=str), round(px, 1), round(py, 1), round(pw, 1), round(ph, 1), round(fs, 1))
            if key not in _INK:
                svg = _bars(Pen(0), px, py, pw, ph, p, fs) if k == "bars" else extra_prop(Pen(0), px, py, pw, ph, p, fs)
                _INK[key] = ink_box(svg) or box
            box = _INK[key]
        elif k not in ("board", "paper", "picture"):  # a box grows to hold its words
            box = (px, py, px + pw, py + max(ph, block_h(wrap(p.get("label", ""), pw - 10, fs), fs) + 12))
        out.append(box)
    if (st or {}).get("split"):
        for cell, sub in zip(split_cells(st, x, y, w, h, fs), st["split"]):
            out += speech_obstacles(sub, *cell["sub"], fs * 0.8)
    return out


MIN_SPEECH_W = 110  # the narrowest gap a speech line is wrapped into: about a dozen characters


def clear_of_props(lines, head_x, bottom, obstacles, left, right, fs):
    """Move a speech block off the props it would touch. Returns (lines, centre x).

    The free run of space beside the speaker, between the nearest prop on each side and the panel's edges, is found at the block's height.
    If the block fits in it, it is slid into it; if not, it is wrapped again to the width of the gap, which makes it taller, so the gap is found
    again at the new height. A speaker standing in front of a prop, or a gap too narrow to read in, leaves the block as it was."""
    margin = 8
    text_ = " ".join(lines)
    start = lines
    for _ in range(4):
        tw = max(len(li) for li in lines) * fs * CHAR_W
        top = bottom - block_h(lines, fs)
        lo, hi = left, right
        for x0, y0, x1, y1 in obstacles:
            if y1 <= top - 2 or y0 >= bottom + 2:
                continue  # not at this height
            if x0 <= head_x <= x1:
                return start, clamp(head_x, left + tw / 2, right - tw / 2)  # the speaker stands in front of it
            if x1 < head_x:
                lo = max(lo, x1 + margin)
            else:
                hi = min(hi, x0 - margin)
        if hi - lo >= tw:
            return lines, clamp(head_x, lo + tw / 2, hi - tw / 2)
        if hi - lo < MIN_SPEECH_W:
            break
        lines = wrap(text_, hi - lo, fs)
    tw = max(len(li) for li in start) * fs * CHAR_W
    return start, clamp(head_x, left + tw / 2, right - tw / 2)


def speech_layout(talk, heads, staging, scene_y, scene_h, w, fs):
    """Where each speech block goes: above its speaker's head, off the props beside it, and stacked clear of any block it would touch.
    One dict per block: speech, lines, head (None if the speaker is not on stage), cx, top, bottom, tw."""
    obstacles = speech_obstacles(staging, PAD, scene_y, w - 2 * PAD, scene_h, fs) if staging else []
    placed, out = [], []
    for s, lines in talk:
        head = heads.get(speaker_key(s))
        if not head:
            out.append({"speech": s, "lines": lines, "head": None, "cx": w / 2, "top": 0.0, "bottom": 0.0, "tw": 0.0})
            continue
        bottom = head[1] - SPEECH_GAP
        left, right = cell_box(staging, s.get("cell"), PAD, scene_y, w - 2 * PAD, scene_h, fs) or (PAD, w - PAD)  # a line in a strip stays in its frame
        lines, cx = clear_of_props(lines, head[0], bottom, obstacles, left, right, fs)
        bh = block_h(lines, fs)
        tw = max(len(li) for li in lines) * fs * CHAR_W
        top = bottom - bh
        for x0, x1, y0, y1 in placed:  # two speakers close together: stack rather than overlap
            if cx - tw / 2 < x1 and cx + tw / 2 > x0 and top < y1 and bottom > y0:
                top = y0 - 6 - bh
                bottom = top + bh
        placed.append((cx - tw / 2, cx + tw / 2, top, bottom))
        out.append({"speech": s, "lines": lines, "head": head, "cx": cx, "top": top, "bottom": bottom, "tw": tw})
    return out


def draw_panel(panel, plan, w, h, cast):
    fs, pid = plan["fs"], panel["id"]
    pen = Pen(pid)
    scene_h = h - plan["nat_h"] + plan["scene_nat"]
    o = []
    if panel.get("frame", "outlined") == "outlined":
        o.append(pen.rect(0, 0, w, h, 2.8))
    talk_top = PAD  # the picture comes first and the paper's words below it: a reader who likes the cartoon goes on to read the fact
    scene_y = talk_top + plan["talk_h"]
    if "staging" in panel and plan["talk"]:
        # The room for speech is estimated before the scene is drawn; the drawn head can sit higher (a close shot, a short panel), which
        # would put its speech line above the panel. Measure the real heads with a throwaway pen and push the scene down until clear.
        for _ in range(4):
            _, probe = stage(Pen(pid), PAD, scene_y, w - 2 * PAD, scene_h, panel["staging"], cast, fs)
            blocks = speech_layout(plan["talk"], probe, panel["staging"], scene_y, scene_h, w, fs)
            lack = max((talk_top - b["top"] for b in blocks), default=0)
            if lack <= 0.5 or scene_h - lack < 60:
                break
            scene_y += lack
            scene_h -= lack
    y = scene_y + scene_h + 6
    for lines in plan["captions"]:  # under the picture
        bh = block_h(lines, fs) + 16
        o.append(f'<rect x="{PAD}" y="{y:.1f}" width="{w - 2 * PAD:.1f}" height="{bh:.1f}" fill="{SOFT}"/>')
        o.append(text(PAD + 8, y + 7, lines, fs, wrap_w=w - 2 * PAD - 16))
        y += bh + 6
    heads = {}
    if "staging" in panel:
        svg, heads = stage(pen, PAD, scene_y, w - 2 * PAD, scene_h, panel["staging"], cast, fs)
        # A close shot is cropped at the shoulders: crop at the picture's own foot, or the figure runs over the caption under it.
        # Only the bottom is cut; props and heads may still reach up into the speech room above.
        sid = "scene-" + pid.replace(".", "-")
        o.append(f'<clipPath id="{sid}"><rect x="-4" y="-4" width="{w + 8:.1f}" height="{scene_y + scene_h + 4:.1f}"/></clipPath>'
                 f'<g clip-path="url(#{sid})">{svg}</g>')
    else:
        lines = wrap(panel["scene"], w - 2 * PAD - 12, fs * 0.9)
        o.append(text(w / 2, scene_y + scene_h / 2 - block_h(lines, fs * 0.9) / 2, lines, fs * 0.9, anchor="middle", fill=MID))
    ty = talk_top
    blocks = speech_layout(plan["talk"], heads, panel.get("staging"), scene_y, scene_h, w, fs)
    for b in blocks:
        s, lines, head = b["speech"], b["lines"], b["head"]
        if not head:  # nobody to point at: stack the text at the top of the scene
            o.append(text(w / 2, ty, lines, fs, anchor="middle"))
            ty += block_h(lines, fs) + 22
            continue
        o.append(text(b["cx"], b["top"], lines, fs, anchor="middle", halo=True, wrap_w=speech_room(panel, s, w - 2 * PAD, fs)))
        dash = "3 5" if s.get("kind") == "think" else None
        start = clamp(head[0], b["cx"] - b["tw"] / 2 + 8, b["cx"] + b["tw"] / 2 - 8)  # the point of the text's lower edge nearest the speaker
        o.append(pen.line((start, b["bottom"] + 3), (head[0], head[1] - 8), 2.0, dash=dash))
    cid = "clip-" + pid.replace(".", "-")
    alt = esc(panel["scene"])
    alt_attr = escape(str(panel["scene"]), quote=True)
    return (f'<g id="panel-{pid}" role="img" aria-label="{alt_attr}"><title>{alt}</title>'
            f'<rect class="qa-box" x="0" y="0" width="{w:.1f}" height="{h:.1f}" fill="none" stroke="none"/>'  # the panel's true box, for visual_qa
            f'<clipPath id="{cid}"><rect x="-4" y="-4" width="{w + 8:.1f}" height="{h + 8:.1f}"/></clipPath>'
            f'<g clip-path="url(#{cid})">{"".join(o)}</g></g>')


# ---------------------------------------------------------------- pages
def row_geometry(row, usable):
    net = usable - GUTTER * (len(row) - 1)
    return [net * u / 12 for _, u in row]


def build_items(doc, cast, k=0.55):
    """The flow of the comic: header, beat labels, rows, colophon, each with its height."""
    meta = doc["meta"]
    srcs = sources_of(meta)
    src = srcs[0]
    usable = PAGE_W - 2 * MARGIN
    items = []
    title_lines = wrap(meta["title"], usable, 46)
    if len(srcs) > 1:
        sub = wrap(f"Drawn from {len(srcs)} sources: " + "; ".join(f'{_short_authors(s)} ({s["year"]})' for s in srcs), usable, 17)
    else:
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
    lic_urls = [_licence_url(s["licence"]) for s in srcs]
    if len(srcs) > 1:
        cites = " ".join(f'“{s["title"]}” by {_short_authors(s)} ({s["year"]})'
                         + (f', doi {s["doi"]}' if s.get("doi") else "") + f'. Licence: {s["licence"]}.' for s in srcs)
        note = ("Drawn from these sources: " + cites + " Condensed into a comic with invented characters and scenes using the "
                "science-comic-pipeline; the sources' authors did not write or endorse this document. ")
    else:
        note = (f'Adapted from “{src["title"]}” by {", ".join(src["authors"])} ({src["year"]})'
                + (f', doi {src["doi"]}' if src.get("doi") else "")
                + f'. Licence: {src["licence"]}. '
                "Condensed into a comic with invented characters and scenes using the science-comic-pipeline; "
                "the paper's authors did not write or endorse this document. ")
    note += "The pictures are simple cartoons: animals and apparatus are stand-ins and not to scale."
    if doc["meta"].get("gallery"):
        note = "A catalogue of the bodies and props the xkcd renderer can draw (science-comic-pipeline). The animals and apparatus are generic cartoon shapes, not accurate or to scale."
    if doc["meta"].get("private"):
        note += " PRIVATE: not for sharing."
    elif not all(lic_urls) and not doc["meta"].get("gallery"):  # no Creative Commons deed to link to: say plainly that it is not an open licence
        note += (" Some of these sources are not under an open licence: keep this comic private and do not publish it."
                 if len(srcs) > 1 else " This paper is not under an open licence: keep this comic private and do not publish it.")
    colo = wrap(note, usable, 15)
    links = []
    if doc["meta"].get("more") and not doc["meta"].get("private"):
        links.append((f'{doc["meta"]["more"]["text"]}: {doc["meta"]["more"]["url"]}', doc["meta"]["more"]["url"]))
    if not doc["meta"].get("gallery"):
        for s in srcs:
            paper = s.get("url") or (f'https://doi.org/{s["doi"]}' if s.get("doi") else "")
            if paper:
                links.append((f"Read the original paper: {paper}" if len(srcs) == 1 else f"{_short_authors(s)} ({s['year']}): {paper}", paper))
        for u in dict.fromkeys(u for u in lic_urls if u):
            links.append((f"Licence terms: {u}", u))

    def draw_colophon(y, c=colo, ls=links):
        """The footer in the caption grey. The pipeline's name and the lines below are links (clickable in a browser
        and in the PDF), underlined but not heavier than the text around them."""
        def inline(line):
            return esc(line).replace(PIPELINE_NAME, f'<a href="{PIPELINE_URL}" target="_blank"><tspan style="text-decoration:underline" font-weight="normal">{PIPELINE_NAME}</tspan></a>')
        spans = "".join(f'<tspan x="{MARGIN:.1f}" dy="{(15 if i == 0 else 18):.1f}">{inline(t)}</tspan>' for i, t in enumerate(c))
        out = [f'<text x="{MARGIN:.1f}" y="{y + 6:.1f}" font-size="15" font-weight="normal" fill="{MID}">{spans}</text>']
        ly = y + 6 + block_h(c, 15) + 4
        for label, href in ls:
            lines = link_lines(label)
            out.append(f'<a href="{esc(href)}" target="_blank">'
                       + text(MARGIN, ly, lines, 15, fill=MID).replace("<text ", '<text style="text-decoration:underline" ', 1) + "</a>")
            ly += len(lines) * 15 * 1.3
        return "".join(out)

    def link_lines(label):
        """A link's lines. A long address has no spaces to wrap at, so it is broken after a slash."""
        per = max(4, int(usable / (15 * CHAR_W)))
        lines = []
        for ln in wrap(label, usable, 15):
            while len(ln) > per:
                cut = ln.rfind("/", 0, per) + 1 or per
                lines.append(ln[:cut])
                ln = ln[cut:]
            lines.append(ln)
        return lines

    items.append({"kind": "colophon", "h": block_h(colo, 15) + sum(len(link_lines(l)) for l, _ in links) * 15 * 1.3 + 16, "draw": draw_colophon})
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
    chars += [c for p, _ in row for sub in (p.get("staging") or {}).get("split", []) for c in sub.get("characters", [])]
    props += [pr for p, _ in row for sub in (p.get("staging") or {}).get("split", []) for pr in sub.get("props", [])]
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
        stamp = " · PRIVATE: not for sharing" if doc["meta"].get("private") else ""
        foot = text(PAGE_W / 2, PAGE_H - MARGIN - 8, [f'{doc["meta"]["title"]} · page {n} of {len(pages)}{stamp}'], 14, anchor="middle", fill=MID)
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


def sources_of(meta):
    """The source records of a comic: the one `source`, or the list `sources` of a comic drawn from several papers."""
    return list(meta["sources"]) if meta.get("sources") else [meta["source"]]


def _short_authors(s):
    """'Craig & Killick', 'Beard et al.': the surnames' list kept short for a subtitle."""
    names = [a.split(",")[0].strip() if "," in a else a.split()[-1] for a in s["authors"]]
    return names[0] if len(names) == 1 else (f"{names[0]} & {names[1]}" if len(names) == 2 else f"{names[0]} et al.")


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
