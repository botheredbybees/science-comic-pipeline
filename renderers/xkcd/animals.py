"""Animal characters for the xkcd renderer: krill, penguin and whale.

Each function draws one animal facing right with its feet (or tail, or belly) on `base`, and returns
(svg, (head_x, head_top_y)) like a stick figure does, so speech lines can point at it. Left-facing is
done by mirroring around the centre. `s` is the usual figure scale; at s = 1 a penguin is about 100 units
tall, a whale about 220 long and a krill about 70 long, so give a krill a larger `scale` in the staging.
"""
import math

from draw import INK, PAPER, clamp


def _mirror(svg, cx, facing):
    if facing == "left":
        return f'<g transform="translate({cx:.1f} 0) scale(-1 1) translate({-cx:.1f} 0)">{svg}</g>'
    return svg


def _eye(pen, x, y, r, face, w):
    """An eye in the animal's expression: a dot, a flat line (deadpan) or a ring (surprised)."""
    if face == "deadpan":
        return pen.line((x - r, y), (x + r, y), w, amp=0.2)
    if face == "surprised":
        return pen.ellipse(x, y, r * 1.2, r * 1.3, w * 0.7)
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{INK}"/>'


def krill(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A krill: one smooth, curved, tapering body with a banded abdomen, a big dark eye, antennae and a tail fan."""
    w = clamp(2.2 * s, 1.5, 3.0)

    def P(x, y):
        return (cx + x * s, base + y * s)

    top = [P(34, -22), P(22, -34), P(2, -36), P(-17, -31), P(-30, -20), P(-37, -7)]
    under = [P(-30, -3), P(-22, -14), P(-8, -21), P(10, -22), P(27, -15)]
    o = []
    o += [pen.line(P(-30 + 2 * i, -12 + 4 * i), P(-39 - 3 * i, -3 + 10 * i - 12), w * 0.7, amp=0.2) for i in range(0)]
    for dy in (-12, -3, 6):  # the tail fan
        o.append(pen.line(P(-37, -6), P(-50, dy), w * 0.8, amp=0.3))
    for x in (5, 12, 19, 25):  # thoracic legs under the carapace
        o.append(pen.line(P(x, -20), P(x - 4, -8), w * 0.7, amp=0.3))
    for x, y in ((-6, -19), (-14, -16), (-21, -11)):  # swimming legs under the abdomen
        o.append(pen.line(P(x, y), P(x - 2, y + 7), w * 0.6, amp=0.2))
    o.append(pen.stroke(top + under, w, closed=True, fill=PAPER))
    for (tx, ty), (bx, by) in zip((P(-5, -35), P(-13, -32), P(-21, -27), P(-27, -21)), (P(-4, -22), P(-11, -20), P(-17, -15), P(-24, -9))):
        o.append(pen.line((tx, ty + 1 * s), (bx, by - 1 * s), w * 0.6, amp=0.2))  # the abdomen's bands
    o.append(pen.line(P(12, -35), P(11, -22), w * 0.7, amp=0.2))  # the carapace's edge
    ex, ey = P(24, -27)
    o.append(_eye(pen, ex, ey, 3.6 * s, face, w))
    o += [pen.line(P(34, -23), P(62, -42), w * 0.6, amp=0.3), pen.line(P(34, -21), P(66, -26), w * 0.6, amp=0.3)]
    return _mirror("".join(o), cx, facing), (cx + 30 * s, base - 50 * s)


def penguin(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    w = clamp(2.3 * s, 1.5, 3.0)
    top = base - 98 * s
    body = [(cx, top), (cx + 17 * s, top + 10 * s), (cx + 23 * s, top + 38 * s), (cx + 22 * s, base - 14 * s),
            (cx + 10 * s, base - 4 * s), (cx, base - 2 * s), (cx - 10 * s, base - 4 * s), (cx - 22 * s, base - 14 * s),
            (cx - 23 * s, top + 38 * s), (cx - 17 * s, top + 10 * s)]
    o = [pen.ellipse(cx - 9 * s, base, 10 * s, 3.4 * s, w * 0.8, fill=PAPER),
         pen.ellipse(cx + 9 * s, base, 10 * s, 3.4 * s, w * 0.8, fill=PAPER)]
    reach = {"up": -34, "shrug": 6}.get(pose, 26)  # where the flipper tips end, relative to the shoulder
    for side in (-1, 1):
        sx = cx + side * 22 * s
        tip = (cx + side * 36 * s, top + (38 + reach) * s)
        o.append(pen.stroke([(sx, top + 30 * s), tip, (sx - side * 1 * s, top + (40 + max(reach, 0) * 0.3) * s)],
                            w, closed=True, fill=INK))
    o.append(pen.stroke(body, w, closed=True, fill=INK))
    o.append(pen.ellipse(cx + 3 * s, top + 60 * s, 14 * s, 27 * s, w * 0.7, fill=PAPER))
    for ex in (cx + 2 * s, cx + 13 * s):  # white eyes with pupils, because the head is black
        o.append(pen.ellipse(ex, top + 16 * s, 4.2 * s, 4.2 * s, w * 0.6, fill=PAPER))
        o.append(_eye(pen, ex + 1 * s, top + 16 * s, 1.7 * s, "neutral" if face != "surprised" else "neutral", w))
    beak = [(cx + 14 * s, top + 20 * s), (cx + 31 * s, top + 25 * s), (cx + 14 * s, top + 30 * s)]
    o.append(pen.stroke(beak, w * 0.8, closed=True, fill=PAPER))
    if face == "smile":
        o.append(pen.stroke([(cx + 15 * s, top + 29 * s), (cx + 22 * s, top + 33 * s), (cx + 29 * s, top + 27 * s)], w * 0.7))
    elif face == "worry":
        o.append(pen.line((cx + 5 * s, top + 8 * s), (cx + 15 * s, top + 11 * s), w * 0.9, amp=0.2, color=PAPER))
    return _mirror("".join(o), cx, facing), (cx + 4 * s, top - 4 * s)


def whale(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    w = clamp(2.2 * s, 1.5, 3.0)
    body = [(cx + 105 * s, base - 34 * s), (cx + 90 * s, base - 52 * s), (cx + 55 * s, base - 64 * s),
            (cx + 10 * s, base - 66 * s), (cx - 40 * s, base - 57 * s), (cx - 84 * s, base - 44 * s),
            (cx - 112 * s, base - 64 * s), (cx - 104 * s, base - 44 * s), (cx - 112 * s, base - 26 * s),
            (cx - 84 * s, base - 38 * s), (cx - 45 * s, base - 24 * s), (cx - 5 * s, base - 10 * s),
            (cx + 40 * s, base - 8 * s), (cx + 85 * s, base - 14 * s), (cx + 104 * s, base - 27 * s)]
    o = [pen.stroke(body, w, closed=True, fill=PAPER)]
    o += [pen.line((cx + (28 + 6 * i) * s, base - (13 - i * 1.2) * s), (cx + (66 + 4 * i) * s, base - (19 - i * 1.6) * s), w * 0.6, amp=0.3)
          for i in range(4)]  # throat grooves
    o.append(pen.stroke([(cx + 28 * s, base - 20 * s), (cx + 10 * s, base - 1 * s), (cx + 32 * s, base - 11 * s)], w * 0.9))  # flipper
    o.append(_eye(pen, cx + 80 * s, base - 36 * s, 2.6 * s, face, w))
    curve = {"smile": -5, "worry": 5}.get(face, 0)
    o.append(pen.stroke([(cx + 103 * s, base - 31 * s), (cx + 82 * s, base - (29 - curve) * s), (cx + 58 * s, base - 28 * s)], w * 0.8))
    for dx, dy in ((-7, -22), (0, -26), (7, -22)):  # the spout
        o.append(pen.line((cx + 50 * s, base - 66 * s), (cx + (50 + dx) * s, base - (66 - dy) * s), w * 0.7, amp=0.3))
    return _mirror("".join(o), cx, facing), (cx + 52 * s, base - 96 * s)


ANIMALS = {"krill": krill, "penguin": penguin, "whale": whale}
