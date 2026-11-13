"""Animal characters for the xkcd renderer: krill, penguin, whale, salp, copepod, fish, worm, jellyfish and urchin.

Each function draws one animal facing right with its feet (or tail, or belly) on `base`, and returns
(svg, (head_x, head_top_y)) like a stick figure does, so speech lines can point at it. Left-facing is
done by mirroring around the centre. `s` is the usual figure scale; at s = 1 a penguin is about 100 units
tall, a whale about 250 long, a krill about 70 long and a salp about 110 long, so give a krill a larger `scale` in the staging.
The copepod, fish, worm, jellyfish and urchin are generic cartoon shapes, not anatomy: they say "an animal of this kind", and a
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
        px, py = P(82, -26 + dy * 0.9)
        o.append(_blob(pen, px, py, 11 * u, 4.6 * u, rot, w, K["shell"], K["line"]))
    for x, r in ((67, 7.5), (58.5, 9), (49, 10.5), (38, 12)):  # the abdomen, tail end first so the nearer ones overlap it
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
    ax, ay = P(-24, -44)  # the antenna: a long thin curve up and forward
    o.append(pen.stroke([(ax, ay), P(-30, -60), P(-31, -76), P(-36, -88)], w * 0.8, color=K["line"]))
    ex, ey = P(-16, -33)
    o.append(_eye(pen, ex, ey, 4.4 * u + 0.8, face, w, color=K["eye"]))
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


def copepod(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A calanoid copepod: an oval head-and-body, a slim jointed tail ending in two bristles, and one pair of very long
    antennae. (A generic cartoon shape, not anatomy.)"""
    w = clamp(2.1 * s, 1.5, 2.8)

    def P(x, y):
        return (cx + x * s, base + y * s)

    o = [pen.line(P(-56, -31), P(-72, -40), w * 0.7, amp=0.3), pen.line(P(-56, -29), P(-73, -22), w * 0.7, amp=0.3),
         pen.line(P(-58, -31), P(-66, -48), w * 0.4, amp=0.2, color=MID), pen.line(P(-58, -29), P(-67, -14), w * 0.4, amp=0.2, color=MID)]
    for x, rx, ry, fill in ((-48, 6, 4.5, SOFT), (-36, 7.5, 6, SOFT), (-22, 9, 8, PAPER)):  # the tail segments, narrowest last
        o.append(_blob(pen, *P(x, -30), rx * s, ry * s, 0, w, fill, INK))
    for x in (-14, -4, 6, 16):  # swimming legs
        o.append(pen.line(P(x, -17), P(x - 5, -4), w * 0.7, amp=0.2, color=INK))
    o.append(_blob(pen, *P(8, -30), 29 * s, 15.5 * s, 0, w, PAPER, INK))
    o.append(pen.stroke([P(30, -30), P(33, -38), P(31, -44)], w * 0.6, color=MID))  # the head's edge
    o.append(pen.stroke([P(26, -41), P(38, -58), P(47, -82), P(44, -104)], w * 0.8, color=INK))  # the long antennae
    o.append(pen.stroke([P(30, -38), P(44, -50), P(58, -66), P(66, -84)], w * 0.6, color=MID))
    o.append(_eye(pen, *P(26, -33), 3.4 * s + 0.6, face, w))
    if face in ("smile", "worry"):
        b = 3 if face == "smile" else -3
        o.append(pen.stroke([P(25, -22), P(31, -22 + b), P(37, -23)], w * 0.7, color=INK))
    return _mirror("".join(o), cx, facing), (cx + 20 * s, base - 46 * s)


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
    """A jellyfish: a domed bell with a scalloped rim, four wavy oral arms and a fringe of thin tentacles hanging to `base`."""
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
    o.append(_eye(pen, *P(12, -76), 3.8 * s + 0.6, face, w))
    if face in ("smile", "worry"):
        b = 3 if face == "smile" else -3
        o.append(pen.stroke([P(2, -66), P(12, -66 + b), P(22, -67)], w * 0.7, color=INK))
    return _mirror("".join(o), cx, facing), (cx + 4 * s, base - 108 * s)


def urchin(pen, cx, base, s, pose="stand", face="neutral", facing="right", holding=None, app=None):
    """A sea urchin: a round shell with a halo of spines, shorter underneath where it rests, a face on the front."""
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
    o.append(_eye(pen, cxu + 6 * s, cyu - 4 * s, 3.4 * s + 0.6, face, w))
    b = 3 if face == "smile" else (-3 if face == "worry" else 0)
    o.append(pen.stroke([(cxu - 2 * s, cyu + 7 * s), (cxu + 8 * s, cyu + 7 * s + b * s), (cxu + 17 * s, cyu + 6 * s)], w * 0.7, color=INK))
    return _mirror("".join(o), cx, facing), (cx, base - 62 * s)


ANIMALS = {"krill": krill, "penguin": penguin, "whale": whale, "salp": salp, "copepod": copepod, "fish": fish,
           "worm": worm, "jellyfish": jellyfish, "urchin": urchin}
