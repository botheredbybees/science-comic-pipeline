"""Facial expressions for the stick figures: eyes, brows and a mouth.

The five original faces (neutral, smile, worry, deadpan, surprised) are still drawn by `render._face`, unchanged, so that
comics made before these existed render exactly as they did. Everything else is drawn here from a small table: each face
names an eye shape, a brow shape and a mouth shape. A figure faces right, so its far eye is the left one and its near eye the
right one; the renderer flips the whole figure for `facing: left`.

The expressions follow what faces really do, as writers and researchers describe them: surprise opens the eyes and lifts the
brows, anger draws the brows together and down, sadness lifts their inner ends, scepticism lifts one brow, a real smile
crinkles the eyes shut, disgust narrows the eyes and wrinkles the mouth.
"""
import math

from draw import INK, MID, PAPER

# The four faces still drawn by render._face, unchanged, so that comics made before the others existed render as they did.
# (`surprised` is one of the original five, but a stick figure now draws it with the bigger look below: wide eyes, high brows, a
# dropped jaw. Animals still draw it with their own eye and mouth.)
LEGACY = ("neutral", "smile", "worry", "deadpan")

# Animal bodies draw only the original five faces (the four above and `surprised`); a new face stands in for the nearest of them there.
ANIMAL_NATIVE = LEGACY + ("surprised",)
ANIMAL_FACE = {
    "laugh": "smile", "content": "smile", "wink": "smile", "smirk": "smile",
    "smug": "deadpan", "sceptical": "deadpan", "squint": "deadpan", "stare": "deadpan", "eyeroll": "deadpan",
    "sleepy": "deadpan", "determined": "deadpan", "puzzled": "deadpan",
    "sad": "worry", "tearful": "worry", "angry": "worry", "disgust": "worry", "plead": "worry",
}

# name: (far eye, near eye, brows, mouth)
FACES = {
    "laugh": ("arc_up", "arc_up", "none", "laugh"),
    "content": ("arc_down", "arc_down", "none", "smile"),
    "wink": ("dot", "chev_near", "none", "smile"),
    "smirk": ("dot", "dot", "one_up", "smirk"),
    "smug": ("lid", "lid", "one_up", "smirk"),
    "sceptical": ("dot", "dot", "one_up", "skew"),
    "squint": ("chev_far", "chev_near", "frown", "flat"),
    "stare": ("wide_pin", "wide_pin", "none", "flat"),
    "eyeroll": ("up", "up", "raised", "skew"),
    "sleepy": ("arc_down", "arc_down", "none", "yawn"),
    "sad": ("dot", "dot", "sad", "worry"),
    "tearful": ("shine", "shine", "sad", "tremble"),
    "angry": ("dot", "dot", "angry", "tight"),
    "determined": ("dot", "dot", "set", "flat"),
    "disgust": ("slit", "slit", "angry", "wavy"),
    "puzzled": ("dot", "dot", "puzzled", "wavy"),
    "plead": ("shine", "shine", "plead", "pout"),
    "surprised": ("wide", "wide", "high", "gape"),
}
NEW = tuple(FACES)
ALL = LEGACY + NEW
SHOWN = ALL  # what the gallery and the docs list

# Brows as (far-outer, far-inner, near-inner, near-outer) vertical offsets in s (positive is down), plus an overall lift.
BROWS = {
    "none": None,
    "raised": ((-0.4, -0.8, -0.8, -0.4), -2.0),
    "high": ((-0.6, -1.2, -1.2, -0.6), -3.4),
    "sad": ((0.9, -1.6, -1.6, 0.9), -0.2),
    "plead": ((1.0, -2.4, -2.4, 1.0), -1.4),
    "angry": ((-0.8, 1.7, 1.7, -0.8), 0.4),
    "frown": ((-0.4, 1.0, 1.0, -0.4), 0.6),
    "set": ((-0.2, 1.0, 1.0, -0.2), 0.2),
    "one_up": ((0.2, 0.2, -0.6, -1.2), 0.0),  # the near brow lifts, the far one stays level
    "puzzled": ((0.4, 1.4, -1.4, -2.2), -0.4),
}
BROW_ONE_UP_LIFT = 2.2  # extra lift for the raised brow of `one_up`


def _eye(pen, kind, x, ey, s, w):
    if kind == "arc_up":  # an eye shut in a smile: a hump
        return [pen.stroke([(x - 3 * s, ey + 1.2 * s), (x, ey - 2.4 * s), (x + 3 * s, ey + 1.2 * s)], w * 0.8)]
    if kind == "arc_down":  # a relaxed closed lid: a dip
        return [pen.stroke([(x - 3 * s, ey - 0.8 * s), (x, ey + 2.2 * s), (x + 3 * s, ey - 0.8 * s)], w * 0.8)]
    if kind in ("chev_far", "chev_near"):  # squeezed eyes as chevrons that point at each other: > <
        d = 1 if kind == "chev_far" else -1
        return [pen.line((x - d * 2.6 * s, ey - 2.4 * s), (x + d * 1.6 * s, ey), w * 0.85, amp=0.1),
                pen.line((x - d * 2.6 * s, ey + 2.4 * s), (x + d * 1.6 * s, ey), w * 0.85, amp=0.1)]
    if kind == "slit":  # narrowed: a thin slanted slit
        return [pen.line((x - 3.2 * s, ey - 0.6 * s), (x + 3.2 * s, ey + 0.4 * s), w * 0.9, amp=0.15)]
    if kind == "lid":  # half open: the lower half of the eye under a flat lid
        pts = [(x - 2.7 * s, ey - 0.9 * s), (x - 2 * s, ey + 1.3 * s), (x, ey + 2.1 * s), (x + 2 * s, ey + 1.3 * s), (x + 2.7 * s, ey - 0.9 * s)]
        return [pen.stroke(pts, w * 0.4, closed=True, fill=INK), pen.line((x - 3.4 * s, ey - 0.9 * s), (x + 3.4 * s, ey - 0.9 * s), w * 0.8, amp=0.1)]
    if kind == "wide":  # startled: a big ring with the pupil in it
        return [pen.ellipse(x, ey, 3.5 * s, 3.9 * s, w * 0.6), f'<circle cx="{x:.1f}" cy="{ey:.1f}" r="{1.2 * s:.1f}" fill="{INK}"/>']
    if kind == "wide_pin":  # a fixed stare: a big ring with a pin-prick pupil
        return [pen.ellipse(x, ey, 3.3 * s, 3.6 * s, w * 0.6), f'<circle cx="{x:.1f}" cy="{ey:.1f}" r="{0.7 * s:.1f}" fill="{INK}"/>']
    if kind == "up":  # eyes rolled up: a ring with the pupil at the top
        return [pen.ellipse(x, ey, 3 * s, 3.2 * s, w * 0.6), f'<circle cx="{x + 0.4 * s:.1f}" cy="{ey - 1.7 * s:.1f}" r="{1.3 * s:.1f}" fill="{INK}"/>']
    if kind == "shine":  # glossy, glistening eyes: a big dark eye with a bright highlight
        return [f'<circle cx="{x:.1f}" cy="{ey:.1f}" r="{2.7 * s:.1f}" fill="{INK}"/>',
                f'<circle cx="{x + 0.9 * s:.1f}" cy="{ey - 0.9 * s:.1f}" r="{0.9 * s:.1f}" fill="{PAPER}"/>']
    return [f'<circle cx="{x:.1f}" cy="{ey:.1f}" r="{1.7 * s:.1f}" fill="{INK}"/>']  # a plain dot


def _brows(pen, style, ex, ey, s, w, glasses, cx, cy):
    """Thin brows over the eyes, each end kept inside the outline of the head. The hair is drawn smaller than it used to be, so
    there is a strip of forehead for them to sit on and they need no outline."""
    spec = BROWS[style]
    if not spec:
        return []
    (fo, fi, ni, no), lift = spec
    by = ey - (3.8 + (3.2 if glasses else 0)) * s + lift * 0.7 * s
    nl = -BROW_ONE_UP_LIFT * s * (0.4 if style == "puzzled" else 1) if style in ("one_up", "puzzled") else 0.0
    brows = [[(ex[0] - 2.8 * s, by + fo * s), (ex[0] + 2.6 * s, by + fi * s)],
             [(ex[1] - 2.6 * s, by + ni * s + nl), (ex[1] + 2.8 * s, by + no * s + nl)]]

    def inside(p):
        dy = (p[1] - cy) / s
        lim = math.sqrt(max(0.0, 225 - dy * dy)) - 2.2
        return (cx + max(-lim, min(lim, (p[0] - cx) / s)) * s, p[1])
    return [pen.line(inside(a), inside(b), w * 0.55, amp=0.12) for a, b in brows]


def _mouth(pen, kind, mx, cy, s, w):
    if kind == "flat":
        return [pen.stroke([(mx - 5 * s, cy + 7.5 * s), (mx + 5 * s, cy + 7.5 * s)], w * 0.8)]
    if kind == "smile":
        return [pen.stroke([(mx - 6 * s, cy + 5 * s), (mx, cy + 10.5 * s), (mx + 6 * s, cy + 5 * s)], w * 0.8)]
    if kind == "worry":
        return [pen.stroke([(mx - 6 * s, cy + 10 * s), (mx, cy + 5.5 * s), (mx + 6 * s, cy + 10 * s)], w * 0.8)]
    if kind == "laugh":  # open wide, with a tongue
        pts = [(mx - 7 * s, cy + 4.5 * s), (mx - 5.5 * s, cy + 10.5 * s), (mx, cy + 14 * s), (mx + 5.5 * s, cy + 10.5 * s), (mx + 7 * s, cy + 4.5 * s)]
        return [pen.stroke(pts, w * 0.8, closed=True, fill=INK), pen.ellipse(mx, cy + 12.2 * s, 3.4 * s, 1.5 * s, w * 0.3, fill=MID)]
    if kind == "smirk":  # one corner up
        return [pen.stroke([(mx - 5 * s, cy + 8.4 * s), (mx + 1 * s, cy + 8.8 * s), (mx + 6.5 * s, cy + 5.2 * s)], w * 0.8)]
    if kind == "skew":  # a flat mouth tilted to one side
        return [pen.stroke([(mx - 5 * s, cy + 8.4 * s), (mx + 5 * s, cy + 6.2 * s)], w * 0.8)]
    if kind == "tight":  # lips pressed together, the corners pulled down
        return [pen.stroke([(mx - 5.2 * s, cy + 9.8 * s), (mx - 3.4 * s, cy + 8 * s), (mx + 3.4 * s, cy + 8 * s), (mx + 5.2 * s, cy + 9.8 * s)], w * 0.8)]
    if kind == "wavy":  # a queasy or puzzled wobble
        return [pen.stroke([(mx - 6 * s, cy + 7.6 * s), (mx - 3 * s, cy + 9.4 * s), (mx, cy + 6.8 * s), (mx + 3 * s, cy + 9.4 * s), (mx + 6 * s, cy + 7.2 * s)], w * 0.8)]
    if kind == "tremble":  # a trembling lip: a wobbling frown
        return [pen.stroke([(mx - 6 * s, cy + 10.4 * s), (mx - 3 * s, cy + 7 * s), (mx, cy + 9.4 * s), (mx + 3 * s, cy + 7 * s), (mx + 6 * s, cy + 10.4 * s)], w * 0.8)]
    if kind == "pout":  # a small downturned mouth
        return [pen.stroke([(mx - 3.4 * s, cy + 9.2 * s), (mx, cy + 7 * s), (mx + 3.4 * s, cy + 9.2 * s)], w * 0.8)]
    if kind == "yawn":  # a small open mouth
        return [pen.ellipse(mx, cy + 9 * s, 2.2 * s, 3 * s, w * 0.7, fill=PAPER)]
    if kind == "gape":  # jaw dropped
        return [pen.ellipse(mx, cy + 9.4 * s, 3.4 * s, 4.8 * s, w * 0.7, fill=PAPER)]
    return [pen.stroke([(mx - 5 * s, cy + 7 * s), (mx + 5 * s, cy + 7 * s)], w * 0.8)]


def draw_face(pen, cx, cy, s, face, w, glasses=False):
    """Eyes, brows and a mouth for one of FACES; the same placement as render._face (cx, cy is the head's centre)."""
    far, near, brows, mouth = FACES[face]
    ex, ey = (cx - 1 * s, cx + 8.5 * s), cy - 3 * s
    o = _eye(pen, far, ex[0], ey, s, w) + _eye(pen, near, ex[1], ey, s, w)
    if glasses:
        o += [pen.ellipse(x, ey, 4.8 * s, 4.8 * s, w * 0.7) for x in ex]
        o.append(pen.line((ex[0] + 4.8 * s, ey), (ex[1] - 4.8 * s, ey), w * 0.7, amp=0.1))
    o += _brows(pen, brows, ex, ey, s, w, glasses, cx, cy)
    o += _mouth(pen, mouth, cx + 4 * s, cy, s, w)
    return o
