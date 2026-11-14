"""Animal characters for the xkcd renderer: krill, penguin, whale, salp, copepod, fish, worm, jellyfish, urchin, seal, seabird,
moss, bacterium, seastar, dinoflagellate, squid and amphipod.

Each function draws one animal facing right with its feet (or tail, or belly) on `base`, and returns
(svg, (head_x, head_top_y)) like a stick figure does, so speech lines can point at it. Left-facing is
done by mirroring around the centre. `s` is the usual figure scale; at s = 1 a penguin is about 100 units
tall, a whale about 250 long, a krill about 70 long and a salp about 110 long, so give a krill a larger `scale` in the staging.
The copepod, fish, worm, jellyfish, urchin, seal, seabird, moss, bacterium, seastar and dinoflagellate are generic cartoon shapes, not anatomy: they say "an animal of this kind", and a
caption carries any claim about the real one. Real copepods are a millimetre or two long; the picture is not to scale.

They stay black and white like the rest of the renderer: ink outlines, white fills, and the light grey
SOFT for shading, so they sit comfortably next to the stick figures and props.
"""
import math

from draw import INK, MID, PAPER, SOFT, clamp

KRILL = {"shell": PAPER, "abdomen": SOFT, "line": INK, "dot": PAPER, "eye": INK}
WHALE = {"back": SOFT, "belly": PAPER, "fin": SOFT, "line": INK, "water": INK}
PENGUIN = {"bill": PAPER, "line": INK}


def _mirror(svg, cx, facing):
    if facing == "left":
        return f'<g transform="translate({cx:.1f} 0) scale(-1 1) translate({-cx:.1f} 0)">{svg}</g>'
    return svg


def _blob(pen, cx, cy, rx, ry, rot, w, fill, color, k=14):
    """A slightly wobbly oval, tilted by `rot` radians, with a coloured outline."""
    c, s = math.cos(rot), math.sin(rot)
    pts = []
    for i in range(k):
        a = math.tau * i / k
        x, y = rx * (1 + pen.n(0.015)) * math.cos(a), ry * (1 + pen.n(0.015)) * math.sin(a)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    return pen.stroke(pts, w, closed=True, fill=fill, color=color)


def _dot(x, y, r, fill):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{fill}"/>'


def _eye(pen, x, y, r, face, w, color=INK, white=PAPER):
    """A round eye with a highlight. The face changes the lid or brow: flat lid (deadpan), wide ring
    (surprised), slanted brow (worry), a plain eye otherwise."""
    o = [_dot(x, y, r, color)]
    if face == "surprised":
        o = [_dot(x, y, r * 1.25, white), pen.stroke([(x + r * 1.25 * math.cos(a), y + r * 1.25 * math.sin(a))
                                                      for a in [i * math.tau / 10 for i in range(10)]], w * 0.6, closed=True, color=color),
             _dot(x, y, r * 0.6, color)]
    else:
        o.append(_dot(x + r * 0.35, y - r * 0.35, r * 0.32, white))
    if face == "deadpan":
        o.append(pen.line((x - r * 1.3, y - r * 0.25), (x + r * 1.3, y - r * 0.25), w * 0.9, amp=0.1, color=color))
    elif face == "worry":
        o.append(pen.line((x - r * 1.2, y - r * 1.5), (x + r * 1.3, y - r * 2.3), w * 0.8, amp=0.1, color=color))
    return "".join(o)


def krill(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A krill in the shape of a children's-book shrimp: a big oval carapace with a big dark eye and one long
    antenna, a row of overlapping round abdomen segments that shrink toward a three-lobed tail fan."""
    K = KRILL
    u = 0.55 * s
    w = clamp(2.0 * s, 1.5, 2.6)

    def P(x, y):  # `x`, `y` are in a drawing 130 wide with the head on the left; this flips it to face right
        return (cx - (x - 35) * u, base + y * u)

    o = []
    for dy, rot in ((-9, 0.5), (0, 0.0), (9, -0.5)):  # the tail fan, three leaf-shaped lobes
        px, py = P(76, -26 + dy * 0.9)
        o.append(_blob(pen, px, py, 11 * u, 4.6 * u, rot, w, K["shell"], K["line"]))
    for x, r in ((61, 7.5), (52.5, 9), (43, 10.5), (32, 12)):  # the abdomen, tail end first so the nearer ones overlap it
        px, py = P(x, -26 + (38 - x) * 0.05)
        o.append(_blob(pen, px, py, r * u, r * u * 1.2, 0, w, K["abdomen"], K["line"]))
    for x in (-16, -8, 0, 8):  # legs
        a, b = P(x, -14), P(x - 3, -2)
        o.append(pen.line(a, b, w * 0.8, amp=0.2, color=K["line"]))
    px, py = P(0, -30)
    o.append(_blob(pen, px, py, 30 * u, 17.5 * u, -0.1, w, K["shell"], K["line"]))
    for x, y in ((-6, -15), (6, -13), (22, -12.5)):  # light organs along the underside
        dx, dy = P(x, y)
        o.append(pen.stroke([(dx + r, dy) for r in (1.8 * u + 0.4, 0, -1.8 * u - 0.4)] + [(dx, dy - 1.8 * u - 0.4)], 1.2, closed=True, fill=MID, color=MID))
    ax, ay = P(-24, -44)  # the antennae: two long thin curves, both sweeping forward, one above the other and of equal length
    o.append(pen.stroke([(ax, ay), P(-34, -58), P(-48, -68), P(-66, -66)], w * 0.8, color=K["line"]))
    o.append(pen.stroke([P(-28, -40), P(-42, -52), P(-58, -57), P(-74, -50)], w * 0.7, color=K["line"]))
    ex, ey = P(-16, -33)
    o.append(_eye(pen, ex, ey, 6.4 * u + 1.0, face, w, color=K["eye"]))
    if face in ("smile", "worry"):  # krill have no real mouth, but a comic one is needed to smile or fret
        mx, my = P(-27, -23)
        o.append(pen.stroke([(mx, my), P(-20, -19 + (3 if face == "smile" else -3)), P(-12, -21)], w * 0.7, color=K["line"]))
    return _mirror("".join(o), cx, facing), (cx + 30 * u, base - 44 * u)


def penguin(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A round, upright penguin: black back and head, white belly, white-ringed eyes, orange bill and feet."""
    Pn = PENGUIN
    w = clamp(2.3 * s, 1.5, 3.0)
    top = base - 98 * s
    body = [(cx - 2 * s, top), (cx + 17 * s, top + 8 * s), (cx + 26 * s, top + 34 * s), (cx + 27 * s, base - 30 * s),
            (cx + 18 * s, base - 8 * s), (cx, base - 2 * s), (cx - 18 * s, base - 8 * s), (cx - 27 * s, base - 30 * s),
            (cx - 26 * s, top + 34 * s), (cx - 18 * s, top + 8 * s)]
    o = [pen.stroke([(cx + side * (3 + dx) * s, base - 2 * s + dy * s) for dx, dy in ((-8, -1), (-12, 1), (-2, 4), (11, 4), (13, 0), (7, -2))]
                    , w * 0.8, closed=True, fill=Pn["bill"], color=Pn["line"]) for side in (-1, 1)]
    reach = {"up": -38, "shrug": 6}.get(pose, 30)  # where the flipper tips end, relative to the shoulder
    for side in (-1, 1):  # flippers: black leaf shapes hanging from the shoulders
        sx = cx + side * 25 * s
        tip = (cx + side * 41 * s, top + (40 + reach) * s)
        o.append(pen.stroke([(sx, top + 30 * s), (cx + side * 38 * s, top + (34 + reach * 0.5) * s), tip,
                             (sx + side * 6 * s, top + (46 + max(reach, 0) * 0.35) * s)], w, closed=True, fill=INK))
    o.append(pen.stroke(body, w, closed=True, fill=INK))
    o.append(pen.stroke([(cx + 4 * s, top + 36 * s), (cx + 19 * s, top + 52 * s), (cx + 20 * s, base - 28 * s), (cx + 8 * s, base - 10 * s),
                         (cx - 10 * s, base - 10 * s), (cx - 20 * s, base - 28 * s), (cx - 19 * s, top + 52 * s), (cx - 6 * s, top + 36 * s)],
                        w * 0.6, closed=True, fill=PAPER, color=INK))
    for ex in (cx + 2 * s, cx + 14 * s):  # white-ringed eyes: the head is black, so the rings are what read
        o.append(pen.stroke([(ex + 5.2 * s * math.cos(a), top + 17 * s + 5.2 * s * math.sin(a)) for a in [i * math.tau / 10 for i in range(10)]],
                            w * 0.5, closed=True, fill=PAPER, color=INK))
        o.append(_dot(ex + 1 * s, top + 17.5 * s, 2.2 * s, INK))
    if face == "surprised":
        o += [pen.stroke([(ex + 6.5 * s * math.cos(a), top + 17 * s + 6.5 * s * math.sin(a)) for a in [i * math.tau / 10 for i in range(10)]],
                         w * 0.5, closed=True, color=PAPER) for ex in (cx + 2 * s, cx + 14 * s)]
    beak = [(cx + 15 * s, top + 22 * s), (cx + 33 * s, top + 27 * s), (cx + 15 * s, top + 34 * s)]
    o.append(pen.stroke(beak, w * 0.8, closed=True, fill=Pn["bill"], color=Pn["line"]))
    if face == "smile":
        o.append(pen.stroke([(cx + 15 * s, top + 33 * s), (cx + 24 * s, top + 38 * s), (cx + 32 * s, top + 30 * s)], w * 0.7, color=Pn["line"]))
    elif face == "worry":
        o.append(pen.line((cx - 1 * s, top + 7 * s), (cx + 16 * s, top + 11 * s), w * 0.9, amp=0.2, color=PAPER))
    elif face == "deadpan":
        o.append(pen.line((cx - 1 * s, top + 14 * s), (cx + 16 * s, top + 14 * s), w * 0.9, amp=0.2, color=INK))
    return _mirror("".join(o), cx, facing), (cx + 4 * s, top - 4 * s)


def whale(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A cartoon whale: blunt head, pale throat with grooves, a flipper, a tail that curls up into flukes, and a spout."""
    Wh = WHALE
    w = clamp(2.2 * s, 1.5, 3.0)

    def P(x, y):
        return (cx + x * s, base + y * s)

    body = [P(*p) for p in ((106, -30), (100, -52), (72, -70), (30, -76), (-12, -70), (-52, -58), (-88, -50), (-112, -58),
                            (-112, -46), (-90, -36), (-54, -26), (-14, -12), (30, -8), (72, -10), (100, -18))]
    belly = [P(*p) for p in ((101, -22), (72, -13), (30, -11), (-14, -15), (-48, -27), (-18, -32), (30, -28), (72, -27))]
    o = []
    for lobe in (((-104, -58), (-116, -80), (-140, -98), (-134, -70), (-114, -54)),  # flukes: two leaf lobes at the tail's end
                 ((-104, -50), (-114, -34), (-142, -22), (-138, -46), (-114, -52))):
        o.append(pen.stroke([P(*p) for p in lobe], w, closed=True, fill=Wh["fin"], color=Wh["line"]))
    o.append(pen.stroke(body, w, closed=True, fill=Wh["back"], color=Wh["line"]))
    o.append(pen.stroke(belly, 0.1, closed=True, fill=Wh["belly"], color=Wh["belly"]))
    o.append(pen.stroke(body, w, closed=True, color=Wh["line"]))
    o += [pen.line(P(24 + 9 * i, -14 + i * 0.6), P(52 + 8 * i, -21 + i * 0.4), w * 0.6, amp=0.3, color=Wh["line"]) for i in range(4)]  # throat grooves
    o.append(pen.stroke([P(34, -26), P(12, -9), P(-4, 0), P(28, -12)], w * 0.9, closed=True, fill=Wh["fin"], color=Wh["line"]))  # flipper
    bend = {"smile": -6, "worry": 5}.get(face, 0)
    o.append(pen.stroke([P(104, -32), P(84, -30 - bend), P(62, -33 - bend * 1.5)], w * 0.8, color=Wh["line"]))  # the mouth
    o.append(_eye(pen, *P(74, -44), 3.6 * s + 0.4, face, w, color=Wh["line"], white=PAPER))
    jet = []  # the spout: a fountain of two curves and some drops
    for side in (-1, 1):
        jet.append(pen.stroke([P(46, -74), P(46 + side * 4, -96), P(46 + side * 15, -108), P(46 + side * 20, -96)], w * 0.7, color=Wh["water"]))
    jet += [_dot(*P(46 + dx, -112 - dy), 2.2 * s, Wh["water"]) for dx, dy in ((-6, 0), (6, 2), (0, 8))]
    o += jet
    return _mirror("".join(o), cx, facing), (cx + 70 * s, base - 82 * s)


def salp(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A solitary salp: a see-through barrel with muscle hoops, an open mouth at the front, a smaller
    opening at the back and a dark gut. (A salp has no eyes; the dot is the cartoon's, so it can have a face.)"""
    w = clamp(2.2 * s, 1.5, 3.0)

    def P(x, y):
        return (cx + x * s, base + y * s)

    body = [P(*p) for p in ((-50, -52), (-20, -60), (20, -60), (48, -54), (54, -38), (48, -22), (20, -16), (-20, -16), (-50, -24), (-56, -38))]
    o = [pen.line(P(-60, -42), P(-76, -46), w * 0.6, amp=0.4, color=MID), pen.line(P(-60, -34), P(-77, -32), w * 0.6, amp=0.4, color=MID),
         pen.stroke(body, w, closed=True, fill=PAPER, color=INK)]
    for x in (-36, -18, 0, 18, 36):  # the muscle hoops
        o.append(pen.stroke([P(x, -58 + abs(x) * 0.05), P(x + 3, -38), P(x, -18 - abs(x) * 0.05)], w * 0.55, color=MID))
    o.append(_blob(pen, cx - 55 * s, base - 38 * s, 4.5 * s, 12 * s, 0, w * 0.8, SOFT, INK))  # the atrial opening, at the back
    o.append(_blob(pen, cx + 53 * s, base - 38 * s, 6.5 * s, 16 * s, 0, w, PAPER, INK))  # the mouth, open at the front
    o.append(_blob(pen, cx + 51 * s, base - 38 * s, 3 * s, 9 * s, 0, w * 0.5, INK, INK))
    o.append(_blob(pen, cx - 6 * s, base - 28 * s, 9 * s, 5.5 * s, 0.15, w * 0.8, INK, INK))  # the gut, a dark knot
    o.append(_eye(pen, *P(34, -47), 3.4 * s + 0.4, face, w))
    if face in ("smile", "worry"):
        b = 3 if face == "smile" else -3
        o.append(pen.stroke([P(24, -30), P(34, -30 + b * 2), P(44, -30)], w * 0.7, color=INK))
    return _mirror("".join(o), cx, facing), (cx + 30 * s, base - 66 * s)


def _curve(p0, p1, p2, n=14):
    """Points along a quadratic Bezier curve from p0 to p2, bent towards p1."""
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]))
    return out


def _tube(pen, pts, w0, w1, width, fill=PAPER, color=INK):
    """A tapering tube along a centre line (a horn, a spine): an outline `w0` wide at the start and `w1` at the end."""
    n = len(pts)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d
        hw = (w0 + (w1 - w0) * i / (n - 1)) / 2
        left.append((x + nx * hw, y + ny * hw))
        right.append((x - nx * hw, y - ny * hw))
    return pen.stroke(left + right[::-1], width, closed=True, fill=fill, color=color)


def copepod(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A calanoid copepod seen from above, the classic plankton-net picture: a long oval body, a slim jointed tail
    ending in a fan of bristles, short swimming legs by the head and two very long, hairy antennae swept out to the
    sides. Drawn lying along the page with the head on the right. (A generic cartoon shape, not anatomy.)"""
    w = clamp(2.1 * s, 1.5, 2.8)
    cy = -44

    def P(x, y):
        return (cx + x * s, base + y * s)

    o = []
    for k in range(-3, 4):  # the fan of bristles at the tail
        a = k * 0.13
        o.append(pen.line(P(-50, cy), P(-50 - 30 * math.cos(a), cy + 30 * math.sin(a)), 1.4, amp=0.1, color=INK))
    for sgn in (-1, 1):  # the two tail lobes
        o.append(_blob(pen, *P(-49, cy + sgn * 3), 5 * s, 2.4 * s, 0, w * 0.8, PAPER, INK, k=8))
    for x, rx, ry in ((-42, 5.5, 4), (-32, 6.5, 5.2), (-21, 8, 6.6)):  # the tail segments, widening towards the body
        o.append(_blob(pen, *P(x, cy), rx * s, ry * s, 0, w, PAPER, INK, k=10))
    for sgn in (-1, 1):  # swimming legs, a few short feathered strokes each side
        for x in (6, 14, 22):
            o.append(pen.line(P(x, cy + sgn * 11), P(x - 4, cy + sgn * 19), w * 0.7, amp=0.2, color=INK))
    o.append(_blob(pen, *P(8, cy), 31 * s, 12.5 * s, 0, w, SOFT, INK, k=16))  # the body
    for x in (-8, 4, 16):  # body segments
        o.append(pen.stroke([P(x, cy - 10.5), P(x + 2, cy), P(x, cy + 10.5)], 1.0, color=MID))
    for sgn in (-1, 1):  # the long antennae, with a fringe of fine hairs
        pts = _curve(P(36, cy + sgn * 5), P(48, cy + sgn * 30), P(26, cy + sgn * 58), 14)
        o.append(pen.stroke(pts, w * 0.9, color=INK))
        for i in range(2, 14, 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1] if i + 1 < len(pts) else pts[i]
            d = math.hypot(x1 - x0, y1 - y0) or 1
            nx, ny = -(y1 - y0) / d, (x1 - x0) / d
            for side in (1, -1):
                o.append(pen.line((x0, y0), (x0 + side * nx * 5 * s, y0 + side * ny * 5 * s), 1.0, amp=0.05, color=MID))
    for sgn in (-1, 1):  # the eyes: two spots at the head
        ex, ey = P(34, cy + sgn * 4)
        o.append(_eye(pen, ex, ey, 2.4 * s + 0.4, face, w))
    return _mirror("".join(o), cx, facing), (cx + 34 * s, base - 92 * s)


def fish(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A plain bony fish: a pointed oval body, a forked tail, a back fin and a belly fin, a gill line and a big eye."""
    w = clamp(2.2 * s, 1.5, 3.0)

    def P(x, y):
        return (cx + x * s, base + y * s)

    o = [pen.stroke([P(-44, -34), P(-72, -56), P(-66, -34), P(-72, -12), P(-44, -30)], w, closed=True, fill=SOFT, color=INK)]  # the tail
    o.append(pen.stroke([P(-16, -54), P(-2, -72), P(14, -70), P(18, -52)], w, closed=True, fill=SOFT, color=INK))  # the back fin
    o.append(pen.stroke([P(-6, -16), P(-14, -4), P(6, -8)], w * 0.9, closed=True, fill=SOFT, color=INK))  # the belly fin
    body = [P(*p) for p in ((-48, -32), (-30, -50), (0, -58), (32, -52), (54, -38), (58, -32), (52, -26), (30, -14), (0, -10), (-30, -18))]
    o.append(pen.stroke(body, w, closed=True, fill=PAPER, color=INK))
    o.append(pen.stroke([P(30, -50), P(24, -34), P(30, -16)], w * 0.7, color=MID))  # the gill cover
    for x, y in ((-24, -38), (-12, -30), (-26, -26), (-6, -42)):  # scales, a few marks
        o.append(pen.stroke([P(x, y), P(x + 4, y - 3), P(x + 8, y)], 1.1, color=MID))
    o.append(pen.stroke([P(-2, -30), P(14, -32), P(26, -26)], w * 0.5, color=MID))  # the side line
    o.append(_eye(pen, *P(42, -40), 4.2 * s + 0.6, face, w))
    mouth = 2 if face == "smile" else (-2 if face == "worry" else 0)
    o.append(pen.stroke([P(58, -32), P(50, -29 + mouth), P(45, -27 + mouth)], w * 0.7, color=INK))
    return _mirror("".join(o), cx, facing), (cx + 36 * s, base - 62 * s)


def worm(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A bristle worm (a polychaete): a wavy row of segments, each with a pair of bristles, and a head with two feelers."""
    w = clamp(2.0 * s, 1.5, 2.8)
    n = 15

    def P(x, y):
        return (cx + x * s, base + y * s)

    path = []
    for i in range(n):
        t = i / (n - 1)  # 0 at the tail, 1 at the head
        path.append((-66 + 126 * t, -20 - 9 * math.sin(t * math.tau * 1.15)))
    o = []
    for i, (x, y) in enumerate(path):
        r = 4.4 + 4.2 * (i / (n - 1))
        for sign in (-1, 1):  # bristles, two small strokes per segment
            o.append(pen.line(P(x, y + sign * r * 0.9), P(x - 3, y + sign * (r + 6.5)), 1.1, amp=0.1, color=MID))
    for i, (x, y) in enumerate(path):  # the segments, tail first so the nearer ones overlap
        r = 4.4 + 4.2 * (i / (n - 1))
        o.append(_blob(pen, *P(x, y), r * 0.8 * s, r * s, 0, w * 0.85, SOFT if i % 2 else PAPER, INK, k=10))
    hx, hy = path[-1]
    o.append(_blob(pen, *P(hx + 6, hy), 9 * s, 8.5 * s, 0, w, PAPER, INK))
    o.append(pen.stroke([P(hx + 11, hy - 6), P(hx + 20, hy - 13), P(hx + 26, hy - 11)], w * 0.7, color=INK))  # the two feelers
    o.append(pen.stroke([P(hx + 12, hy + 3), P(hx + 21, hy + 8), P(hx + 27, hy + 5)], w * 0.7, color=INK))
    o.append(_eye(pen, *P(hx + 5, hy - 2), 2.8 * s + 0.5, face, w))
    if face in ("smile", "worry"):
        b = 2 if face == "smile" else -2
        o.append(pen.stroke([P(hx + 3, hy + 5), P(hx + 8, hy + 5 + b), P(hx + 13, hy + 4)], w * 0.6, color=INK))
    return _mirror("".join(o), cx, facing), (cx + (hx + 4) * s, base + (hy - 12) * s)


def jellyfish(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A jellyfish: a domed bell with a scalloped rim, four wavy oral arms and a fringe of thin tentacles hanging to `base`. It has no face, so `face` is ignored."""
    w = clamp(2.2 * s, 1.5, 3.0)

    def P(x, y):
        return (cx + x * s, base + y * s)

    o = []
    for x in (-26, -14, -3, 8, 19, 29):  # the fringe of tentacles, thin and wavy
        o.append(pen.stroke([P(x, -54), P(x + 4, -42), P(x - 4, -28), P(x + 3, -14), P(x - 2, -2)], 1.2, color=MID))
    for x in (-16, -5, 6, 17):  # the oral arms, thicker and shorter
        o.append(pen.stroke([P(x, -56), P(x + 5, -44), P(x - 3, -32), P(x + 4, -22)], w * 0.8, color=INK))
    top = [P(*p) for p in ((-42, -56), (-40, -76), (-26, -96), (0, -104), (26, -96), (40, -76), (42, -56))]
    scallops = [P(36, -54), P(28, -50), P(20, -55), P(10, -50), P(0, -55), P(-10, -50), P(-20, -55), P(-28, -50), P(-36, -54)]
    o.append(pen.stroke(top + scallops, w, closed=True, fill=PAPER, color=INK))
    for x in (-24, -8, 8, 24):  # radial canals under the skin
        o.append(pen.stroke([P(x * 0.3, -60), P(x * 0.8, -78), P(x, -92)], 1.1, color=MID))
    return _mirror("".join(o), cx, facing), (cx + 4 * s, base - 108 * s)


def urchin(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A sea urchin: a round shell with a halo of spines, shorter underneath where it rests. It has no face, so `face` is ignored."""
    w = clamp(2.0 * s, 1.5, 2.8)
    cxu, cyu, r = cx, base - 26 * s, 22 * s

    o = []
    for i in range(26):
        a = math.tau * i / 26
        low = math.sin(a) > 0.55  # the spines that touch the ground are stubby
        ln = (7 if low else 20 + 6 * (i % 2)) * s
        o.append(pen.line((cxu + r * 0.9 * math.cos(a), cyu + r * 0.9 * math.sin(a)), (cxu + (r + ln) * math.cos(a), cyu + (r + ln) * math.sin(a)), w * 0.8, amp=0.2, color=INK))
    o.append(_blob(pen, cxu, cyu, r, r * 0.92, 0, w, PAPER, INK, k=16))
    for a in (-2.2, -1.5, -0.8, 0.0, 0.9, 2.0, 2.9):  # the pattern of plates, a few ticks
        o.append(pen.stroke([(cxu + r * 0.55 * math.cos(a), cyu + r * 0.5 * math.sin(a)), (cxu + r * 0.8 * math.cos(a + 0.12), cyu + r * 0.75 * math.sin(a + 0.12))], 1.0, color=MID))
    return _mirror("".join(o), cx, facing), (cx, base - 62 * s)


def seal(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A seal lying on its belly: a plump torpedo body, a small head with whiskers at the front, one front flipper
    and the two back flippers together at the tail. (A generic cartoon shape; no particular species.)"""
    w = clamp(2.2 * s, 1.5, 3.0)

    def P(x, y):
        return (cx + x * s, base + y * s)

    tail = pen.stroke([P(-50, -22), P(-72, -34), P(-76, -22), P(-72, -10), P(-50, -16)], w, closed=True, fill=SOFT, color=INK)
    body = [P(*q) for q in ((-52, -18), (-46, -40), (-20, -50), (14, -48), (40, -42), (56, -36), (54, -24), (40, -10), (6, -4), (-30, -6))]
    o = [tail, pen.stroke(body, w, closed=True, fill=PAPER, color=INK)]
    o.append(pen.stroke([P(14, -20), P(24, -8), P(34, -10), P(30, -22)], w * 0.8, closed=True, fill=SOFT, color=INK))  # the front flipper
    o.append(_blob(pen, *P(54, -40), 14 * s, 11.5 * s, 0.1, w, PAPER, INK))  # the head
    o.append(_dot(*P(66, -42), 3.0 * s + 0.4, INK))  # the nose
    for dy in (-3, 2):  # whiskers
        o.append(pen.line(P(62, -37 + dy), P(76, -39 + dy * 2), 1.1, amp=0.1, color=MID))
    o.append(_eye(pen, *P(53, -45), 2.8 * s + 0.5, face, w))
    if face in ("smile", "worry"):
        b = 2.5 if face == "smile" else -2.5
        o.append(pen.stroke([P(54, -32), P(60, -32 + b), P(65, -33)], w * 0.6, color=INK))
    return _mirror("".join(o), cx, facing), (cx + 50 * s, base - 56 * s)


def seabird(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A seabird standing, in the manner of a petrel or skua: an oval body, a long folded wing, a hooked beak and thin
    legs. (A generic cartoon shape; no particular species.)"""
    w = clamp(2.1 * s, 1.5, 2.8)

    def P(x, y):
        return (cx + x * s, base + y * s)

    o = [pen.line(P(-4, -26), P(-6, -2), w * 0.8, amp=0.2), pen.line(P(8, -26), P(10, -2), w * 0.8, amp=0.2),
         pen.stroke([P(-12, -2), P(-6, -2), P(0, 0)], w * 0.7), pen.stroke([P(6, -2), P(10, -2), P(16, 0)], w * 0.7)]
    o.append(pen.poly([P(-18, -54), P(-60, -47), P(-57, -37), P(-16, -33)], w, fill=SOFT, jit=0.25))  # the tail: a tapering feather, its root under the body
    o.append(_blob(pen, *P(0, -46), 30 * s, 22 * s, -0.25, w, PAPER, INK))  # the body
    o.append(pen.stroke([P(-22, -52), P(8, -62), P(30, -46), P(8, -34), P(-24, -44)], w * 0.9, closed=True, fill=SOFT, color=INK))  # the folded wing
    o.append(_blob(pen, *P(26, -74), 11 * s, 10 * s, 0, w, PAPER, INK))  # the head
    o.append(pen.stroke([P(34, -77), P(46, -76), P(44, -70), P(36, -71)], w * 0.8, closed=True, fill=SOFT, color=INK))  # the beak
    o.append(_eye(pen, *P(28, -77), 2.6 * s + 0.5, face, w))
    if face in ("smile", "worry"):
        b = 2 if face == "smile" else -2
        o.append(pen.stroke([P(30, -70), P(35, -70 + b), P(40, -71)], w * 0.5, color=INK))
    return _mirror("".join(o), cx, facing), (cx + 24 * s, base - 88 * s)


def moss(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A cushion of moss on a rock: a low dome with a fuzzy edge, stippled all over, and a few tall stalks tipped with spore
    capsules. A plant has no face, so `face` is ignored."""
    w = clamp(2.0 * s, 1.5, 2.6)

    def P(x, y):
        return (cx + x * s, base + y * s)

    o = [_blob(pen, *P(0, -7), 50 * s, 8.5 * s, 0, w, SOFT, INK, k=14)]  # the rock
    rx, ry, cyc = 42, 34, -14
    dome = [P(rx * math.cos(a), cyc + ry * math.sin(a)) for a in [math.pi + math.pi * k / 12 for k in range(13)]]
    o.append(pen.stroke(dome, w, closed=True, fill=PAPER, color=INK))
    for k in range(1, 26):  # the fuzzy edge: short outward hairs all round the dome
        a = math.pi + math.pi * k / 26
        x0, y0 = rx * math.cos(a), cyc + ry * math.sin(a)
        o.append(pen.line(P(x0, y0), P(x0 * 1.1 + 0.2 * (k % 3), y0 * 1.0 - 5 - (k % 3)), 1.1, amp=0.05, color=INK))
    for row, (yy, xs) in enumerate(((-20, range(-30, 31, 10)), (-30, range(-22, 23, 11)), (-38, range(-12, 13, 12)), (-12, range(-34, 35, 9)))):  # stipple
        for x in xs:
            o.append(_dot(*P(x + (3 if row % 2 else 0), yy), 0.9 * s + 0.4, MID))
            o.append(pen.line(P(x + 2, yy + 4), P(x + 2, yy + 8), 1.0, amp=0.05, color=MID))
    for x, h in ((-18, 20), (4, 26), (24, 18)):  # stalks with spore capsules
        top = (x - 2, cyc - ry * math.sqrt(max(0.0, 1 - (x / rx) ** 2)) - h)
        o.append(pen.stroke([P(x, cyc - ry * math.sqrt(max(0.0, 1 - (x / rx) ** 2)) + 4), P(x - 2, top[1] + h * 0.5), P(*top)], 1.5, color=INK))
        o.append(_blob(pen, *P(top[0], top[1] - 3), 2.6 * s, 4.2 * s, 0.2, w * 0.7, SOFT, INK, k=8))
    return _mirror("".join(o), cx, facing), (cx, base - 62 * s)


def bacterium(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A rod-shaped bacterium: a capsule with a wavy tail (a flagellum) and a few short hairs, with the cartoon's own eye.
    (Real bacteria have no eyes and are far smaller than anything else in a panel.)"""
    w = clamp(2.1 * s, 1.5, 2.8)

    def P(x, y):
        return (cx + x * s, base + y * s)

    o = [pen.stroke([P(-32, -22), P(-46, -12), P(-58, -26), P(-70, -16)], w * 0.8, color=INK)]  # the flagellum
    for x in (-12, 4, 18):  # short hairs
        o.append(pen.line(P(x, -42), P(x - 2, -50), 1.0, amp=0.1, color=MID))
        o.append(pen.line(P(x, -2), P(x - 2, 6), 1.0, amp=0.1, color=MID))
    cap = [P(-34, -30), P(-36, -40), P(-28, -44), P(0, -44), P(28, -44), P(38, -40), P(40, -22), P(36, -6), P(28, -2), P(0, -2), P(-28, -2), P(-36, -8), P(-36, -20)]
    o.append(pen.stroke(cap, w, closed=True, fill=PAPER, color=INK))
    o.append(_blob(pen, *P(-6, -23), 10 * s, 6 * s, 0.2, w * 0.6, SOFT, MID))  # the nucleoid, a smudge
    o.append(_eye(pen, *P(22, -26), 3.2 * s + 0.5, face, w))
    if face in ("smile", "worry"):
        b = 2.5 if face == "smile" else -2.5
        o.append(pen.stroke([P(18, -14), P(24, -14 + b), P(30, -15)], w * 0.6, color=INK))
    return _mirror("".join(o), cx, facing), (cx + 4 * s, base - 50 * s)


def seastar(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A sea star: five tapering arms round a centre, dotted with small bumps, lying flat (drawn from the side and slightly above).
    It has no face, so `face` is ignored."""
    w = clamp(2.1 * s, 1.5, 2.8)
    ccx, ccy = cx, base - 30 * s
    pts = []
    for i in range(10):
        a = -math.pi / 2 + math.tau * i / 10
        r = (42 if i % 2 == 0 else 15) * s
        pts.append((ccx + r * math.cos(a), ccy + r * 0.72 * math.sin(a)))
    o = [pen.stroke(pts, w, closed=True, fill=PAPER, color=INK)]
    for i in range(5):  # the groove down each arm, and a row of bumps
        a = -math.pi / 2 + math.tau * i / 5
        for k, f in enumerate((0.25, 0.5, 0.75)):
            o.append(_dot(ccx + 42 * s * f * math.cos(a), ccy + 42 * s * f * 0.72 * math.sin(a), 1.8 * s + 0.4, MID))
        o.append(pen.line((ccx, ccy), (ccx + 38 * s * math.cos(a), ccy + 38 * s * 0.72 * math.sin(a)), 1.0, amp=0.1, color=MID))
    return _mirror("".join(o), cx, facing), (cx, base - 48 * s)


def dinoflagellate(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A horned dinoflagellate in the manner of Ceratium: a small angular cell with one long straight horn and two curved
    ones, a groove across the cell and a few plates. (A generic cartoon shape. It has no face, so `face` is ignored.)"""
    w = clamp(2.1 * s, 1.5, 2.8)
    cyd = -46

    def P(x, y):
        return (cx + x * s, base + y * s)

    o = []
    o.append(_tube(pen, [P(*q) for q in _curve((-6, cyd + 2), (-44, cyd - 2), (-84, cyd - 12), 12)], 7 * s, 3.2 * s, w * 0.9, fill=PAPER))  # the long straight horn
    o.append(_tube(pen, [P(*q) for q in _curve((8, cyd - 12), (24, cyd - 50), (-38, cyd - 42), 14)], 7 * s, 3.2 * s, w * 0.9, fill=PAPER))  # the curved horn, up and over
    o.append(_tube(pen, [P(*q) for q in _curve((12, cyd + 12), (22, cyd + 40), (-10, cyd + 42), 12)], 7 * s, 3.2 * s, w * 0.9, fill=PAPER))  # the curved horn, down
    for q in _curve((-6, cyd + 2), (-44, cyd - 2), (-84, cyd - 12), 8)[1:-1]:  # fine lines along the long horn
        o.append(_dot(*P(q[0], q[1]), 0.9, MID))
    cell = [P(*q) for q in ((-15, cyd - 3), (-8, cyd - 17), (8, cyd - 20), (19, cyd - 8), (17, cyd + 8), (8, cyd + 17), (-8, cyd + 14), (-16, cyd + 4))]
    o.append(pen.stroke(cell, w, closed=True, fill=SOFT, color=INK))
    o.append(pen.stroke([P(-15, cyd - 3), P(0, cyd + 1), P(18, cyd - 1)], w * 0.7, color=MID))  # the groove across the cell
    for x, y in ((-4, cyd - 10), (6, cyd - 9), (8, cyd + 8), (-6, cyd + 8)):  # plates and the cell's contents
        o.append(pen.line(P(x, y), P(x + 3, y + 4), 1.0, amp=0.05, color=MID))
    return _mirror("".join(o), cx, facing), (cx - 4 * s, base - 100 * s)


def squid(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A squid swimming to the right: a long tapering mantle with two triangular fins at its tail, a head with a big eye, a fan
    of short arms and two longer feeding tentacles. (A generic cartoon shape, not any one species.)"""
    w = clamp(2.1 * s, 1.5, 2.8)

    def P(x, y):
        return (cx + x * s, base + y * s)

    o = []
    for dy in (-6, 6):  # the two long tentacles, each ending in a small club
        pts = [P(34, -32 + dy * 0.4), P(54, -34 + dy), P(76, -30 + dy * 1.4), P(94, -33 + dy)]
        o.append(pen.stroke(pts, w * 0.7))
        o.append(_blob(pen, *P(96, -33 + dy), 4 * s, 2.6 * s, 0, w * 0.6, PAPER, INK, k=8))
    for k, dy in enumerate((-12, -6, 0, 6, 12)):  # the shorter arms
        o.append(pen.stroke([P(30, -30 + dy * 0.5), P(44, -30 + dy * 1.1 + (2 if k % 2 else -2)), P(58, -29 + dy * 1.5)], w * 0.8))
    o.append(pen.poly([P(-64, -30), P(-50, -50), P(-40, -42), P(-46, -30), P(-40, -18), P(-50, -10)], w, fill=SOFT, jit=0.2))  # the fins
    mantle = [P(-70, -30), P(-52, -42), P(-24, -46), P(6, -44), P(24, -38), P(24, -22), P(6, -16), P(-24, -14), P(-52, -18)]
    o.append(pen.stroke(mantle, w, closed=True, fill=PAPER))
    for x in (-40, -22, -4):  # a few spots on the mantle
        o.append(_dot(*P(x, -34 + (3 if x % 2 else -2)), 1.4 * s + 0.4, MID))
    o.append(_blob(pen, *P(26, -30), 11 * s, 10 * s, 0, w, PAPER, INK))  # the head
    o.append(_eye(pen, *P(29, -33), 5.2 * s + 0.8, face, w))
    return _mirror("".join(o), cx, facing), (cx + 22 * s, base - 52 * s)


def _smooth(pts, per=5):
    """A denser version of a path through `pts` (Catmull-Rom), so an outline offset from it stays smooth."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(per):
            t = k / per
            out.append(tuple(0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * t + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * t * t + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * t ** 3) for d in (0, 1)))
    out.append(pts[-1])
    return out


def amphipod(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """An amphipod, after the plump, sideways-flattened kind seen in plankton photographs: a deep, strongly arched back of broad
    overlapping plates that curls under at the tail, a large dark eye at the front, stout legs hanging from the middle,
    feathery tail appendages sweeping back and down, and long antennae trailing from the face. A generic cartoon shape."""
    w = clamp(2.1 * s, 1.5, 2.8)

    def P(x, y):
        return (cx + x * s, base + y * s)

    spine0 = [(46, -36), (40, -50), (26, -62), (6, -67), (-14, -62), (-32, -48), (-44, -30), (-50, -12)]  # head to tail, over the top
    widths0 = [28, 36, 42, 46, 43, 36, 26, 13]
    spine = [P(*q) for q in _smooth(spine0, 4)]
    n = len(spine)
    hw = []
    for k in range(n):  # half-width along the body, interpolated from the few set above
        f = k * (len(widths0) - 1) / (n - 1)
        i0 = min(int(f), len(widths0) - 2)
        hw.append((widths0[i0] + (widths0[i0 + 1] - widths0[i0]) * (f - i0)) / 2 * s)
    dorsal, ventral = [], []
    for k, (x, y) in enumerate(spine):
        a, b = spine[max(k - 1, 0)], spine[min(k + 1, n - 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy) or 1
        nx, ny = -dy / d, dx / d  # the normal that points up and out along the back
        dorsal.append((x + nx * hw[k], y + ny * hw[k]))
        ventral.append((x - nx * hw[k], y - ny * hw[k]))
    o = []
    for k in (11, 15, 19, 23):  # the stout walking legs, hanging from the belly and angled back
        if k >= n:
            continue
        vx, vy = ventral[k]
        knee, foot = (vx - 6 * s, vy + 13 * s), (vx - 13 * s, vy + 25 * s)
        o.append(pen.stroke([(vx, vy), knee, foot], w * 1.1))
        for dx in (-3.5, 0, 3.5):  # the bristly foot
            o.append(pen.line(foot, (foot[0] + (dx - 3) * s, foot[1] + 7 * s), 1.1, amp=0.05, color=MID))
    for tx, ty, ex, ey in ((-50, -12, -62, 8), (-48, -9, -54, 12), (-52, -14, -72, 2)):  # the feathery tail appendages
        o.append(pen.stroke([P(tx, ty), P((tx + ex) / 2 - 3, (ty + ey) / 2 + 2), P(ex, ey)], w * 0.8))
        for f in (0.45, 0.7, 0.95):
            mx, my = tx + (ex - tx) * f, ty + (ey - ty) * f
            o.append(pen.line(P(mx, my), P(mx - 4, my + 3), 0.9, amp=0.05, color=MID))
    for a, c in ((P(52, -30), [P(62, -14), P(64, 6), P(57, 21)]), (P(47, -28), [P(54, -10), P(50, 6), P(43, 17)])):  # long antennae
        o.append(pen.stroke([a] + c, w * 0.7))
    o.append(pen.stroke([P(54, -42), P(64, -41), P(72, -34)], w * 0.6))  # a short feeler
    o.append(pen.stroke(dorsal + ventral[::-1], w, closed=True, fill=PAPER))  # the body
    belly = [(vx + (dx_ - vx) * 0.4, vy + (dy_ - vy) * 0.4) for (vx, vy), (dx_, dy_) in zip(ventral, dorsal)]
    o.append(pen.stroke(belly[3:-3] + ventral[3:-3][::-1], 0.1, closed=True, fill=SOFT, color=SOFT))  # a pale band along the belly
    for k in range(7, n - 4, 2):  # the broad plates: curved bands across the back
        ax, ay = dorsal[k]
        bx, by = ventral[k]
        mx, my = (ax + bx) / 2 + 3 * s, (ay + by) / 2
        o.append(pen.stroke([(ax, ay), (mx, my), (bx, by)], w * 0.55, color=MID if k % 4 else INK))
    ex, ey = P(43, -40)  # the large dark eye
    o.append(_blob(pen, ex, ey, 7.5 * s, 10 * s, 0.25, w * 0.8, INK, INK, k=12))
    o.append(_dot(ex + 2.5 * s, ey - 3.5 * s, 2.2 * s + 0.4, PAPER))
    return _mirror("".join(o), cx, facing), (cx + 38 * s, base - 82 * s)


ANIMALS = {"krill": krill, "penguin": penguin, "whale": whale, "salp": salp, "copepod": copepod, "fish": fish,
           "worm": worm, "jellyfish": jellyfish, "urchin": urchin, "seal": seal, "seabird": seabird, "moss": moss,
           "bacterium": bacterium, "seastar": seastar, "dinoflagellate": dinoflagellate, "squid": squid, "amphipod": amphipod}
