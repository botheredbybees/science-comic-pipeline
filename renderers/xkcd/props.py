"""Props for charts, diagrams and objects, drawn in the xkcd style.

Each function takes a Pen, the box (x, y, w, h) in page units, the prop's spec and the font size,
and returns SVG. Positions inside a spec (`at`, `to`, `points`, `x`, `y`) are fractions 0 to 1 of
the prop's box (y runs up in `plot`, as on a chart).
"""
import math

from draw import CHAR_W, INK, MID, PAPER, SOFT, block_h, clamp, text, wrap

EXTRA = {"stake", "emsled", "fieldcamp", "molecule", "iceberg", "mixedlayer", "seaice", "iceshelf", "map", "currents", "desk", "phone", "bowl", "bongo", "trawl", "rmt", "ctd", "satellite", "radar", "radarscreen", "icecore", "massspec", "helicopter", "drone", "aquarium", "freezer", "tag", "scatter", "boxplot", "modelgrid", "sequence", "tree", "clusters", "network", "database", "filter", "tubes", "sequencer", "cpr", "echosounder", "venn", "axis", "plot", "pie", "flow", "steps", "stack", "ship", "bottle", "jar", "flash", "cups", "laptop", "microscope", "teapot", "net", "thermometer"}


def _dot(x, y, r=5):
    return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{INK}"/>'


def axis(pen, x, y, w, h, p, fs):
    """A horizontal axis with ticks, marks and bars (a timeline, a scale of values)."""
    items, fsb = p.get("items", []), max(11.0, fs * 0.93)
    ay = y + h * 0.62
    o = [pen.arrow((x, ay), (x + w, ay), 2.2, head=8)]
    if p.get("title"):
        o.append(text(x + w / 2, y, [p["title"]], fsb, anchor="middle"))
    slot = w / max(len(items), 1) * 1.3
    def fit(cx, lines):
        """Shift a label's centre so it stays inside the box."""
        half = max((len(li) for li in lines), default=0) * fsb * CHAR_W / 2
        return clamp(cx, x + half, x + w - half)

    for it in items:
        px = x + clamp(it.get("at", 0), 0, 1) * w
        lines = wrap(it.get("label", ""), max(slot, 80), fsb)
        lift = it.get("row", 0) * (block_h(lines, fsb, 1.1) + 6)
        if it.get("to") is not None:
            x2 = x + clamp(it["to"], 0, 1) * w
            by = ay - 24 - it.get("row", 0) * 22
            o.append(pen.rect(px, by, max(x2 - px, 4), 16, 2, fill=PAPER if it.get("style") == "hollow" else INK, over=1))
            o.append(text(fit((px + x2) / 2, lines), by - 4 - block_h(lines, fsb, 1.1), lines, fsb, anchor="middle", lh=1.1))
        elif it.get("style") == "mark":
            top = ay - 20 - block_h(lines, fsb, 1.1) - lift
            o.append(_dot(px, ay - 10))
            if lift:
                o.append(pen.line((px, ay - 14), (px, top + block_h(lines, fsb, 1.1) + 2), 1.2, amp=0.3, color=MID))
            o.append(text(fit(px, lines), top, lines, fsb, anchor="middle", lh=1.1))
        else:
            o += [pen.line((px, ay - 6), (px, ay + 6), 2.0, amp=0.2), text(fit(px, lines), ay + 9 + lift, lines, fsb, anchor="middle", lh=1.1)]
    return "".join(o)


def plot(pen, x, y, w, h, p, fs):
    """Axes with one or more curves and labelled notes. Points are [x, y] fractions, y up."""
    fsb = max(11.0, fs * 0.93)
    xl, yl, title = p.get("x_label", ""), p.get("y_label", ""), p.get("title", "")
    left, right = x + (fsb * 1.7 if yl else 8), x + w - 6
    top, bottom = y + (fsb * 1.4 if title else 6), y + h - (fsb * 1.7 if xl else 8)
    o = [pen.line((left, top), (left, bottom), 2.2), pen.line((left, bottom), (right, bottom), 2.2)]
    if title:
        o.append(text((left + right) / 2, y, [title], fsb, anchor="middle"))
    if xl:
        o.append(text((left + right) / 2, bottom + 4, [xl], fsb, anchor="middle"))
    if yl:
        cx, cy = x + fsb * 0.6, (top + bottom) / 2
        o.append(f'<g transform="rotate(-90 {cx:.1f} {cy:.1f})">{text(cx, cy - fsb * 0.6, [yl], fsb, anchor="middle")}</g>')
    for ser in p.get("series", []):
        pts = [(left + px * (right - left), bottom - py * (bottom - top)) for px, py in ser["points"]]
        dash = {"dashed": "7 6", "dotted": "2 5"}.get(ser.get("style"))
        o.append(pen.stroke(pts, 2.4, dash=dash))
    for n in p.get("notes", []):
        o.append(text(left + n["x"] * (right - left), bottom - n["y"] * (bottom - top) - fsb * 1.4, wrap(n["label"], 150, fsb), fsb, anchor="middle", lh=1.1))
    return "".join(o)


def pie(pen, x, y, w, h, p, fs):
    items, fsb = p.get("items", []), max(11.0, fs * 0.93)
    r = min(h * 0.4, w * 0.22)
    cx, cy = x + w * 0.5, y + h * 0.5
    total = sum(i["value"] for i in items) or 1
    o = [pen.ellipse(cx, cy, r, r, 2.4, fill=PAPER)]
    ang = -math.pi / 2
    for i, it in enumerate(items):
        mid = ang + math.tau * it["value"] / total / 2
        o.append(pen.line((cx, cy), (cx + r * math.cos(ang), cy + r * math.sin(ang)), 2.0, amp=0.4))
        lx, ly = cx + (r + 10) * math.cos(mid), cy + (r + 10) * math.sin(mid)
        side = "start" if math.cos(mid) >= 0 else "end"
        o.append(text(lx + (4 if side == "start" else -4), ly - fsb * 0.6, wrap(it.get("label", ""), max(w * 0.34, 110), fsb), fsb, anchor=side, lh=1.1))
        ang += math.tau * it["value"] / total
    return "".join(o)


def flow(pen, x, y, w, h, p, fs):
    """Boxes joined by arrows, left to right (or top to bottom in a tall box)."""
    items, fsb = p.get("items", []), max(11.0, fs * 0.93)
    n = max(len(items), 1)
    horizontal = w >= h * 0.9
    gap = 28
    if horizontal:
        bw, bh = (w - gap * (n - 1)) / n, clamp(h * 0.6, 40, 110)
        boxes = [(x + i * (bw + gap), y + (h - bh) / 2) for i in range(n)]
    else:
        bw, bh = w, (h - gap * (n - 1)) / n
        boxes = [(x, y + i * (bh + gap)) for i in range(n)]
    o = []
    for i, (it, (bx, by)) in enumerate(zip(items, boxes)):
        o.append(pen.rect(bx, by, bw, bh, 2.2, fill=PAPER, over=1))
        lines = wrap(it.get("label", ""), bw - 10, fsb)
        o.append(text(bx + bw / 2, by + bh / 2 - block_h(lines, fsb, 1.1) / 2, lines, fsb, anchor="middle", lh=1.1))
        if i:
            px, py = boxes[i - 1]
            o.append(pen.arrow((px + bw, py + bh / 2), (bx, by + bh / 2), 2.0, head=8) if horizontal
                     else pen.arrow((px + bw / 2, py + bh), (bx + bw / 2, by), 2.0, head=8))
    return "".join(o)


def steps(pen, x, y, w, h, p, fs):
    """A staircase of levels, rising left to right, each with a label and a caption."""
    items, fsb = p.get("items", []), max(11.0, fs * 0.93)
    n = max(len(items), 1)
    sw = w / n
    o = []
    for i, it in enumerate(items):
        sh = h * (0.4 + 0.6 * (i + 1) / n)
        sx, sy = x + i * sw, y + h - sh
        o.append(pen.rect(sx, sy, sw, sh, 2.4, fill=PAPER, over=0))
        lab = wrap(it.get("label", ""), sw - 8, fs) or [""]
        o.append(text(sx + sw / 2, sy + 6, lab, fs, anchor="middle", weight="bold"))
        if it.get("caption"):
            o.append(text(sx + sw / 2, sy + 10 + len(lab) * fs * 1.2 + 4, wrap(it["caption"], sw - 12, fsb), fsb, anchor="middle", lh=1.1))
    return "".join(o)


def stack(pen, x, y, w, h, p, fs):
    """A column of stacked segments, bottom to top, each labelled at the right."""
    items, fsb = p.get("items", []), max(11.0, fs * 0.93)
    total = sum(i["value"] for i in items) or 1
    cw = w * 0.34
    yy = y + h
    o = []
    for k, it in enumerate(items):
        sh = h * it["value"] / total
        fill = {"solid": INK, "hollow": PAPER}.get(it.get("style"), SOFT if k % 2 == 0 else PAPER)
        o.append(pen.rect(x, yy - sh, cw, sh, 2.2, fill=fill, over=0))
        lines = wrap(it.get("label", ""), w - cw - 24, fsb)
        o.append(pen.line((x + cw, yy - sh / 2), (x + cw + 14, yy - sh / 2), 1.6, amp=0.3))
        o.append(text(x + cw + 18, yy - sh / 2 - block_h(lines, fsb, 1.1) / 2, lines, fsb, lh=1.1))
        yy -= sh
    return "".join(o)


def ship(pen, x, y, w, h, p, fs):
    """A research icebreaker in side view, drawn after the RSV Nuyina: a raked bow, a pale upper hull over a dark grey underbody,
    a bridge tower with two radomes, two louvred funnels, a crane at each end of the deck, two lifeboats and rescue-boat bays
    in the hull. A stylised line drawing, not to scale; it keeps its proportions in any box."""
    (fx, fy, fw, fh), lines, fsb = _labelled_fit(x, y, w, h, 3.3, p.get("label"), fs)
    big = fw > 220  # fine detail is dropped when the ship is small

    def N(px, py):  # a point in the reference drawing (1500 wide, 455 tall) to the box
        return (fx + (px - 250) / 1500 * fw, fy + (py - 345) / 455 * fh)

    def R(px0, py0, px1, py1, sw=2.0, fill=PAPER):
        (a, b), (c, d) = N(px0, py0), N(px1, py1)
        return pen.rect(a, b, c - a, d - b, sw, fill=fill, over=0.6)

    sw = clamp(fw / 110, 1.6, 2.6)
    hull = [N(*q) for q in ((252, 588), (1745, 585), (1745, 690), (1700, 745), (1685, 795), (430, 795), (430, 745), (300, 715), (262, 690), (256, 640))]
    under = [N(*q) for q in ((262, 690), (1745, 690), (1700, 745), (1685, 795), (430, 795), (430, 745), (300, 715))]
    o = [pen.poly(hull, sw, fill=SOFT, jit=0.25), pen.poly(under, sw, fill=MID, jit=0.2)]
    o.append(pen.poly([N(*q) for q in ((360, 572), (440, 580), (450, 590), (362, 586))], sw * 0.8, fill=MID, jit=0.1))  # the raised bow edge
    o.append(pen.line(N(278, 585), N(278, 445), sw * 0.9, amp=0.2))  # the foremast
    # the long deckhouse, the funnel casing, and the bridge tower with its sloped front and wings
    o += [R(668, 522, 1385, 584, sw), R(1005, 462, 1150, 525, sw)]
    o.append(pen.poly([N(*q) for q in ((745, 525), (742, 484), (766, 470), (862, 470), (962, 490), (966, 525))], sw, fill=PAPER, jit=0.15))
    o.append(R(752, 480, 858, 500, sw * 0.8, fill=SOFT))  # the bridge windows
    if big:
        for xx in range(766, 858, 18):
            o.append(pen.line(N(xx, 480), N(xx, 500), 1.0, amp=0.05, color=INK))
    o.append(R(792, 396, 834, 470, sw * 0.9))  # the radar mast
    for cx_, cy_, r_ in ((806, 360, 18), (792, 436, 15)):  # the two radomes
        (cx, cy) = N(cx_, cy_)
        o.append(pen.ellipse(cx, cy, r_ / 1500 * fw * 1.15, r_ / 455 * fh * 0.9, sw * 0.9, fill=PAPER))
    for a, b in ((1025, 1062), (1088, 1128)):  # the two funnels, dark and louvred
        o.append(R(a, 410, b, 462, sw, fill=INK))
        if big:
            for yy in (422, 434, 446):
                o.append(pen.line(N(a + 4, yy), N(b - 4, yy), 1.0, amp=0.05, color=PAPER))
    # the foredeck crane: a pedestal, a long boom and a truss under it
    o.append(R(682, 505, 734, 583, sw))
    o.append(pen.poly([N(*q) for q in ((476, 498), (734, 494), (734, 514), (476, 512))], sw * 0.9, fill=PAPER, jit=0.1))
    o.append(pen.poly([N(*q) for q in ((482, 512), (606, 548), (690, 516))], sw * 0.8, fill="none", jit=0.1))
    # the aft crane: its pedestal, boom and a blue cover
    o.append(R(1330, 468, 1384, 524, sw))
    o.append(pen.poly([N(*q) for q in ((1214, 482), (1384, 462), (1384, 478), (1214, 496))], sw * 0.9, fill=PAPER, jit=0.1))
    o.append(R(1232, 494, 1352, 516, sw * 0.8, fill=SOFT))
    for a, b in ((932, 1010), (1030, 1126)):  # the two orange lifeboats, as pods under the bridge
        o.append(pen.stroke([N(a, 562), N(a + 6, 542), N(b - 10, 540), N(b, 556), N(b - 4, 566)], sw * 0.9, closed=True, fill=SOFT))
    for a, b in ((1145, 1250), (1262, 1365)):  # rescue-boat bays in the hull, each with a small boat
        o.append(R(a, 592, b, 638, sw * 0.9))
        if big:
            o.append(pen.poly([N(a + 12, 622), N(b - 12, 622), N(b - 22, 634), N(a + 22, 634)], 1.4, fill=SOFT, jit=0.1))
    o.append(R(1600, 592, 1740, 638, sw * 0.9))
    o.append(R(1430, 592, 1505, 638, sw * 0.9, fill=INK))
    if big:
        for xx in range(790, 1120, 33):  # hull windows
            o.append(pen.rect(*N(xx, 616), 8 / 1500 * fw * 1.6, 8 / 455 * fh * 1.2, 1.0, fill=MID, over=0))
        for cxn in (485, 512, 540, 1497, 1526, 1555):  # thruster and sonar windows low on the hull
            cx, cy = N(cxn, 777)
            o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{max(2.0, fw * 0.006):.1f}" fill="{PAPER}" stroke="{PAPER}" stroke-width="1"/>')
        o.append(pen.stroke([N(1668, 745), N(1700, 735), N(1706, 795), N(1672, 795)], sw * 0.8, closed=True, fill=MID, color=INK))  # the rudder skeg
    if lines:
        o.append(text(fx + fw / 2, fy + fh + 6, lines, fsb, anchor="middle", lh=1.1))
    return "".join(o)


def _labelled_fit(x, y, w, h, ratio, label, fs):
    """Fit an object of width/height `ratio` into the box, leaving room under it for its label; return the fitted
    box and the lines of the label, so the label never crosses the object or leaves the box."""
    fsb = max(11.0, fs * 0.93)
    lines = wrap(label, max(w, 60) * 1.2, fsb) if label else []
    room = len(lines) * fsb * 1.1 + 6 if lines else 0
    fx, fy, fw, fh = _fit(x, y, w, max(h - room, h * 0.4), ratio)
    return (fx, fy, fw, fh), lines, fsb


def bottle(pen, x, y, w, h, p, fs):
    (x, y, w, h), lines, fsb = _labelled_fit(x, y, w, h, 0.55, p.get("label"), fs)
    nw = w * 0.34
    pts = [(x + w / 2 - nw / 2, y), (x + w / 2 - nw / 2, y + h * 0.3), (x, y + h * 0.45), (x, y + h), (x + w, y + h),
           (x + w, y + h * 0.45), (x + w / 2 + nw / 2, y + h * 0.3), (x + w / 2 + nw / 2, y)]
    o = [pen.stroke(pts, 2.4, closed=True, fill=PAPER), pen.line((x + w / 2 - nw / 2 - 3, y), (x + w / 2 + nw / 2 + 3, y), 2.4)]
    o.append(pen.line((x + 4, y + h * 0.7), (x + w - 4, y + h * 0.7), 1.4, amp=0.6, color=MID))
    if lines:
        o.append(text(x + w / 2, y + h + 6, lines, fsb, anchor="middle", lh=1.1))
    return "".join(o)


def jar(pen, x, y, w, h, p, fs):
    (x, y, w, h), lines, fsb = _labelled_fit(x, y, w, h, 0.8, p.get("label"), fs)
    o = [pen.rect(x, y + h * 0.12, w, h * 0.88, 2.4, over=1), pen.rect(x + w * 0.1, y, w * 0.8, h * 0.12, 2.4, fill=PAPER, over=1)]
    o.append(pen.stroke([(x + w * 0.15, y + h * 0.3), (x + w * 0.15, y + h * 0.6)], 1.6, color=MID))
    if lines:
        o.append(text(x + w / 2, y + h + 6, lines, fsb, anchor="middle", lh=1.1))
    return "".join(o)


def flash(pen, x, y, w, h, p, fs):
    cx, cy, r = x + w / 2, y + h / 2, min(w, h) / 2
    o = []
    for i in range(12):
        a = math.tau * i / 12
        r1, r2 = r * (0.35 if i % 2 else 0.45), r * (0.85 if i % 2 else 1.0)
        o.append(pen.line((cx + r1 * math.cos(a), cy + r1 * math.sin(a)), (cx + r2 * math.cos(a), cy + r2 * math.sin(a)), 2.4, amp=0.5))
    if p.get("label"):
        o.append(text(cx, cy - fs * 0.6, [p["label"]], fs, anchor="middle", weight="bold"))
    return "".join(o)


def _rounded(x, y, w, h, r, k=5):
    """The points of a rounded rectangle, for a stroke that has soft corners."""
    pts = []
    for cx, cy, a0 in ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180)):
        for i in range(k + 1):
            a = math.radians(a0 + 90 * i / k)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def desk(pen, x, y, w, h, p, fs):
    """A desk: a thick top on a three-drawer unit and a leg, with a lamp and a stack of papers on it."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.5, p, fs)
    top = y + h * 0.42
    o = [pen.rect(x + w * 0.04, top + h * 0.06, w * 0.3, h * 0.5, 2.4, fill=PAPER, over=0.5)]  # the drawer unit
    for i in range(3):
        yy = top + h * (0.06 + 0.5 * i / 3)
        o.append(pen.line((x + w * 0.04, yy), (x + w * 0.34, yy), 2.0, amp=0.2))
        o.append(pen.rect(x + w * 0.15, yy + h * 0.06, w * 0.08, h * 0.025, 1.6, fill=MID, over=0))
    o.append(pen.line((x + w * 0.92, top + h * 0.06), (x + w * 0.92, y + h * 0.98), 3.0, amp=0.2))  # the leg
    o.append(pen.line((x + w * 0.34, top + h * 0.26), (x + w * 0.92, top + h * 0.26), 1.4, amp=0.2, color=MID))  # the modesty rail
    o.append(pen.rect(x, top, w, h * 0.06, 2.8, fill=SOFT, over=0.6))  # the top
    # the lamp: a base, a jointed arm and a shade, with a few rays
    bx = x + w * 0.1
    o.append(pen.ellipse(bx, top - 2, w * 0.045, h * 0.012, 2.2, fill=INK))
    o.append(pen.stroke([(bx, top - 2), (bx + w * 0.05, y + h * 0.2), (bx + w * 0.17, y + h * 0.08)], 2.2))
    o.append(pen.stroke([(bx + w * 0.13, y + h * 0.04), (bx + w * 0.25, y + h * 0.12), (bx + w * 0.17, y + h * 0.18), (bx + w * 0.1, y + h * 0.1)], 2.0, closed=True, fill=PAPER))
    for dx in (0.0, 0.05, 0.1):
        o.append(pen.line((bx + w * (0.13 + dx), y + h * 0.17), (bx + w * (0.13 + dx * 1.6), y + h * 0.3), 1.0, amp=0.05, color=MID))
    for i, (dx, wd) in enumerate(((0.52, 0.3), (0.55, 0.26), (0.5, 0.28))):  # a stack of papers
        o.append(pen.rect(x + w * dx, top - h * (0.035 * (i + 1)), w * wd, h * 0.035, 1.6, fill=PAPER if i % 2 == 0 else SOFT, over=0.3))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def phone(pen, x, y, w, h, p, fs):
    """A smartphone: a rounded body, a screen with a status bar and a grid of app icons, a camera dot and a home bar."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.56, p, fs)
    r = w * 0.14
    o = [pen.stroke(_rounded(x, y, w, h, r), 2.8, closed=True, fill=PAPER)]
    sx, sy, sw_, sh = x + w * 0.09, y + h * 0.09, w * 0.82, h * 0.8
    o.append(pen.stroke(_rounded(sx, sy, sw_, sh, r * 0.5, k=3), 1.6, closed=True, fill=SOFT))
    o.append(pen.line((sx + sw_ * 0.08, sy + sh * 0.05), (sx + sw_ * 0.45, sy + sh * 0.05), 1.2, amp=0.05, color=MID))  # the status bar
    o.append(pen.line((sx + sw_ * 0.7, sy + sh * 0.05), (sx + sw_ * 0.92, sy + sh * 0.05), 1.2, amp=0.05, color=MID))
    for row in range(4):
        for col in range(3):
            ix, iy = sx + sw_ * (0.12 + col * 0.3), sy + sh * (0.14 + row * 0.2)
            o.append(pen.stroke(_rounded(ix, iy, sw_ * 0.22, sh * 0.13, sw_ * 0.05, k=2), 1.4, closed=True, fill=PAPER if (row + col) % 2 == 0 else MID))
    o.append(pen.line((x + w * 0.36, y + h * 0.935), (x + w * 0.64, y + h * 0.935), 2.0, amp=0.05))  # the home bar
    o.append(_dot(x + w * 0.5, y + h * 0.045, max(1.8, w * 0.02)))  # the camera
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def bowl(pen, x, y, w, h, p, fs):
    """A bowl: a wide rim, a curved body on a small foot, and a heap of dark pieces showing above the rim. `label` under it."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.6, p, fs)
    cx, rim, ry = x + w / 2, y + h * 0.36, h * 0.1
    o = []
    lumps = ((-0.18, 0.0, 0.07), (-0.04, -0.07, 0.075), (0.1, -0.02, 0.07), (0.2, 0.03, 0.055), (-0.28, 0.04, 0.05))
    for dx, dy, r in lumps:  # the contents, heaped above the rim
        o.append(f'<ellipse cx="{cx + dx * w + pen.n(1):.1f}" cy="{rim + dy * h - h * 0.05 + pen.n(1):.1f}" rx="{r * w:.1f}" ry="{r * w * 0.8:.1f}" fill="{INK}"/>')
    body = [(cx + (w / 2) * math.cos(t) * (1 - 0.3 * math.sin(t)), rim + h * 0.5 * math.sin(t)) for t in [math.pi * k / 16 for k in range(17)]]
    o.append(pen.stroke(body[::-1] + [(x, rim)], 2.6, closed=True, fill=PAPER))
    o.append(pen.rect(cx - w * 0.15, y + h * 0.84, w * 0.3, h * 0.07, 2.2, fill=SOFT, over=0.3))  # the foot
    o.append(pen.ellipse(cx, rim, w / 2, ry, 2.6, fill="none"))  # the rim
    o.append(pen.stroke([(x + w * 0.16, rim + h * 0.18), (x + w * 0.24, rim + h * 0.3)], 1.4, color=MID))  # a highlight
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def cups(pen, x, y, w, h, p, fs):
    """A row of cups with handles, each filled to its `value` (0 to 1), so a quantity can be shown as how full it is. Each
    item's `label` goes under its cup."""
    items = p.get("items", [])
    n = max(len(items), 1)
    fsb = max(11.0, fs * 0.93)
    room = fsb * 1.4 if any(it.get("label") for it in items) else 0
    cw = min(w / n * 0.62, (h - room) * 0.8)
    ch = min(h - room, cw * 1.25)  # a cup keeps its proportions in any box
    gap = (w - cw * n) / (n + 1)
    o = []
    for i, it in enumerate(items):
        cx = x + gap + i * (cw + gap)
        bot = y + h - room
        top = bot - ch
        ry = cw * 0.1
        lvl = clamp(it.get("value", 0), 0, 1)
        body = [(cx, top), (cx + cw * 0.14, bot), (cx + cw * 0.86, bot), (cx + cw, top)]
        o.append(pen.stroke([(cx + cw, top + ch * 0.2), (cx + cw * 1.28, top + ch * 0.22), (cx + cw * 1.28, top + ch * 0.58), (cx + cw * 0.92, top + ch * 0.62)], 2.4))  # the handle
        o.append(pen.stroke(body, 2.4, closed=True, fill=PAPER))
        if lvl:
            ty = bot - (bot - top) * lvl
            f = (ty - top) / (bot - top)  # how far down the cup the surface is, 0 at the rim
            xl, xr = cx + cw * 0.14 * f + 1.5, cx + cw - cw * 0.14 * f - 1.5
            o.append(pen.stroke([(xl, ty), (cx + cw * 0.14 + 1.5, bot - 1.5), (cx + cw * 0.86 - 1.5, bot - 1.5), (xr, ty)], 1.0, closed=True, fill=SOFT, color=MID))
            o.append(pen.ellipse((xl + xr) / 2, ty, (xr - xl) / 2, ry * 0.8, 1.4, fill=PAPER))
        o.append(pen.ellipse(cx + cw / 2, top, cw / 2, ry, 2.4, fill="none"))
        if it.get("label"):
            o.append(text(cx + cw / 2, bot + 6, [it["label"]], fsb, anchor="middle"))
    return "".join(o)


def _fit(x, y, w, h, ratio):
    """The largest box of width/height `ratio` that fits in the given one, centred, so the object keeps its shape."""
    bw, bh = (w, w / ratio) if w / h < ratio else (h * ratio, h)
    return x + (w - bw) / 2, y + (h - bh), bw, bh


def laptop(pen, x, y, w, h, p, fs):
    x, y, w, h = _fit(x, y, w, h, 1.5)
    o = [pen.rect(x + w * 0.14, y, w * 0.72, h * 0.62, 2.4, fill=PAPER, over=1),
         pen.poly([(x + w * 0.04, y + h * 0.66), (x + w * 0.96, y + h * 0.66), (x + w, y + h * 0.78), (x, y + h * 0.78)], 2.4, fill=SOFT, jit=0.4),
         f'<circle cx="{x + w / 2:.1f}" cy="{y + h * 0.31:.1f}" r="{min(w, h) * 0.06:.1f}" fill="{INK}"/>']
    if p.get("label"):
        o.append(text(x + w / 2, y + h * 0.84, [p["label"]], max(11.0, fs * 0.93), anchor="middle"))
    return "".join(o)


def microscope(pen, x, y, w, h, p, fs):
    ox, oy, ow, oh = x, y, w, h
    x, y, w, h = _fit(x, y, w, h, 0.8)
    o = [pen.rect(x + w * 0.1, y + h * 0.92, w * 0.62, h * 0.08, 2.4, fill=INK, over=0),
         pen.stroke([(x + w * 0.62, y + h * 0.92), (x + w * 0.88, y + h * 0.72), (x + w * 0.84, y + h * 0.32), (x + w * 0.6, y + h * 0.14)], 3.4),
         pen.stroke([(x + w * 0.36, y + h * 0.04), (x + w * 0.58, y + h * 0.1), (x + w * 0.46, y + h * 0.46), (x + w * 0.26, y + h * 0.4)], 2.4, closed=True, fill=PAPER),
         pen.line((x + w * 0.31, y + h * 0.42), (x + w * 0.29, y + h * 0.54), 3.0, amp=0.1),
         pen.line((x + w * 0.12, y + h * 0.66), (x + w * 0.66, y + h * 0.66), 2.6, amp=0.3),
         pen.rect(x + w * 0.2, y + h * 0.62, w * 0.2, h * 0.04, 1.4, fill=PAPER, over=0)]
    if p.get("label"):
        o.append(text(x + w * 0.45, oy + oh + 4, [p["label"]], max(11.0, fs * 0.93), anchor="middle"))
    return "".join(o)


def teapot(pen, x, y, w, h, p, fs):
    x, y, w, h = _fit(x, y, w, h, 1.3)
    cx = x + w * 0.5
    o = [pen.stroke([(x + w * 0.78, y + h * 0.5), (x + w * 0.98, y + h * 0.34), (x + w * 0.96, y + h * 0.3), (x + w * 0.74, y + h * 0.42)], 2.2, closed=True, fill=PAPER),
         pen.stroke([(x + w * 0.2, y + h * 0.45), (x + w * 0.02, y + h * 0.5), (x + w * 0.04, y + h * 0.75), (x + w * 0.2, y + h * 0.78)], 2.4),
         pen.ellipse(cx, y + h * 0.62, w * 0.34, h * 0.3, 2.4, fill=PAPER),
         pen.line((cx - w * 0.2, y + h * 0.33), (cx + w * 0.2, y + h * 0.33), 2.4, amp=0.2),
         pen.stroke([(cx - w * 0.14, y + h * 0.33), (cx, y + h * 0.22), (cx + w * 0.14, y + h * 0.33)], 2.2, fill=PAPER),
         f'<circle cx="{cx:.1f}" cy="{y + h * 0.19:.1f}" r="{w * 0.03:.1f}" fill="{INK}"/>']
    o += [pen.stroke([(x + w * (0.9 + dx), y + h * 0.26), (x + w * (0.88 + dx), y + h * 0.17), (x + w * (0.93 + dx), y + h * 0.1), (x + w * (0.91 + dx), y)], 1.4)
          for dx in (-0.02, 0.04)]
    if p.get("label"):
        o.append(text(cx, y + h + 4, [p["label"]], max(11.0, fs * 0.93), anchor="middle"))
    return "".join(o)


def net(pen, x, y, w, h, p, fs):
    """A plankton net hung to be hauled up: a towing line, a bridle to the ring, a cone of mesh and a collecting bottle."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.55, p, fs)
    cx = x + w / 2
    ry0, rx, ry = y + h * 0.24, w * 0.42, h * 0.045
    end = y + h * 0.82
    o = [pen.line((cx, y), (cx, y + h * 0.08), 2.0, amp=0.1)]
    for sgn in (-1, 1):  # the bridle
        o.append(pen.line((cx, y + h * 0.08), (cx + sgn * rx, ry0), 1.4, amp=0.15))
    o.append(pen.poly([(cx - rx, ry0), (cx + rx, ry0), (cx + w * 0.07, end), (cx - w * 0.07, end)], 2.2, fill=PAPER, jit=0.2))
    for t in (0.22, 0.42, 0.62, 0.82):  # rings of mesh
        half = rx + (w * 0.07 - rx) * t
        yy = ry0 + (end - ry0) * t
        o.append(pen.stroke([(cx - half, yy), (cx, yy + ry * 0.8), (cx + half, yy)], 1.0, color=MID))
    for f in (-0.55, 0.0, 0.55):
        o.append(pen.line((cx + f * rx, ry0), (cx + f * w * 0.07, end), 0.9, amp=0.15, color=MID))
    o.append(pen.ellipse(cx, ry0, rx, ry, 2.6, fill="none"))
    o.append(pen.rect(cx - w * 0.09, end, w * 0.18, h * 0.04, 2.2, fill=SOFT, over=0))
    o.append(pen.rect(cx - w * 0.075, end + h * 0.04, w * 0.15, h * 0.12, 2.2, fill=PAPER, over=0))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def _cod_end(pen, x, y, w, h):
    """A cod end: the bucket or bag at the closed end of a net, lying along the tow (to the right)."""
    return pen.rect(x, y - h / 2, w, h, 2.0, fill=SOFT, over=0.6)


def bongo(pen, x, y, w, h, p, fs):
    """A bongo net being towed: a pair of mouth rings side by side, a bridle up to the tow cable, and two cones of mesh
    trailing to cod ends, with a weight hanging below. (One ring is drawn behind the other.)"""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.0, p, fs)
    o = [pen.line((x, y), (x + w * 0.12, y + h * 0.2), 1.8, amp=0.2, color=MID), _dot(x + w * 0.12, y + h * 0.2, 3.5)]
    for k, (cy, ryy, lt) in enumerate(((y + h * 0.3, h * 0.15, 0.7), (y + h * 0.64, h * 0.15, 1.0))):
        mx = x + w * (0.3 if k == 0 else 0.26)
        end = x + w * (0.8 if k == 0 else 0.84)
        for sgn in (-1, 1):  # the bridle to each ring
            o.append(pen.line((x + w * 0.12, y + h * 0.2), (mx, cy + sgn * ryy), 1.0, amp=0.15, color=MID))
        o.append(pen.poly([(mx, cy - ryy), (end, cy - ryy * 0.28), (end, cy + ryy * 0.28), (mx, cy + ryy)], 2.0, fill=PAPER if k else SOFT, jit=0.2))
        for t in (0.3, 0.55, 0.8):
            xx = mx + (end - mx) * t
            half = ryy * (1 - 0.72 * t)
            o.append(pen.line((xx, cy - half), (xx, cy + half), 0.9, amp=0.1, color=MID))
        o.append(pen.ellipse(mx, cy, w * 0.025, ryy, 2.4, fill=PAPER if k else SOFT))
        o.append(_cod_end(pen, end, cy, w * 0.1, ryy * 0.56))
    o.append(pen.stroke([(x + w * 0.12, y + h * 0.2), (x + w * 0.12, y + h * 0.84)], 1.0, color=MID))
    o.append(pen.stroke([(x + w * 0.12, y + h * 0.84), (x + w * 0.09, y + h * 0.97), (x + w * 0.15, y + h * 0.97)], 2.0, closed=True, fill=INK))  # the weight
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def trawl(pen, x, y, w, h, p, fs):
    """A midwater trawl being towed: two trawl doors on warps from the ship, a wide mouth with floats along the top
    and weights along the bottom, a funnel of mesh narrowing to a cod end."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.5, p, fs)
    cy, mx, my = y + h * 0.5, x + w * 0.28, h * 0.36
    end = x + w * 0.82
    o = []
    for yy in (y + h * 0.1, y + h * 0.9):  # the warps to the doors
        o.append(pen.line((x, cy), (x + w * 0.17, yy), 1.4, amp=0.2, color=MID))
    for yy in (y + h * 0.1, y + h * 0.9):  # the trawl doors
        o.append(pen.poly([(x + w * 0.16, yy - h * 0.1), (x + w * 0.21, yy - h * 0.1), (x + w * 0.21, yy + h * 0.1), (x + w * 0.16, yy + h * 0.1)], 2.2, fill=SOFT, jit=0.1))
        o.append(pen.line((x + w * 0.21, yy), (mx, cy + (-1 if yy < cy else 1) * my), 1.2, amp=0.15))  # the sweep to the mouth
    o.append(pen.poly([(mx, cy - my), (end, cy - h * 0.07), (end, cy + h * 0.07), (mx, cy + my)], 2.2, fill=PAPER, jit=0.25))
    for t in (0.2, 0.4, 0.6, 0.8):  # mesh
        xx = mx + (end - mx) * t
        half = my + (h * 0.07 - my) * t
        o.append(pen.line((xx, cy - half), (xx, cy + half), 0.9, amp=0.1, color=MID))
    for t in (-0.5, 0.0, 0.5):
        o.append(pen.line((mx, cy + t * my), (end, cy + t * h * 0.07), 0.9, amp=0.1, color=MID))
    o.append(pen.ellipse(mx, cy, w * 0.025, my, 2.4, fill="none"))
    for t in (0.1, 0.28, 0.46, 0.64):  # floats along the headline
        fx = mx + (end - mx) * t
        fy = cy - my + (my - h * 0.07) * t
        o.append(f'<circle cx="{fx:.1f}" cy="{fy - h * 0.035:.1f}" r="{max(2.5, w * 0.012):.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>')
    for t in (0.1, 0.28, 0.46, 0.64):  # weights along the footrope
        fx = mx + (end - mx) * t
        fy = cy + my - (my - h * 0.07) * t
        o.append(f'<circle cx="{fx:.1f}" cy="{fy + h * 0.035:.1f}" r="{max(2.5, w * 0.01):.1f}" fill="{INK}"/>')
    o.append(_cod_end(pen, end, cy, w * 0.12, h * 0.15))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def rmt(pen, x, y, w, h, p, fs):
    """A rectangular midwater trawl (RMT): a stiff rectangular frame with a second, smaller one above it, a net behind each
    ending in a cod end, a bridle to the tow cable and a weight below. Schematic."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.0, p, fs)
    big = (x + w * 0.22, y + h * 0.36, w * 0.13, h * 0.5)
    small = (x + w * 0.22, y + h * 0.08, w * 0.1, h * 0.22)
    o = [pen.line((x, y), (x + w * 0.2, y + h * 0.26), 1.8, amp=0.2, color=MID)]
    for (fx, fy, fw, fh), end, k in ((big, x + w * 0.86, 0.12), (small, x + w * 0.62, 0.1)):
        o.append(pen.poly([(fx + fw, fy), (end, fy + fh / 2 - fh * k), (end, fy + fh / 2 + fh * k), (fx + fw, fy + fh)], 2.0, fill=PAPER, jit=0.2))
        for t in (0.3, 0.55, 0.8):
            xx = fx + fw + (end - fx - fw) * t
            half = fh / 2 * (1 - (1 - k * 2) * t)
            o.append(pen.line((xx, fy + fh / 2 - half), (xx, fy + fh / 2 + half), 0.9, amp=0.1, color=MID))
        o.append(_cod_end(pen, end, fy + fh / 2, w * 0.08, fh * k * 2.4))
    for fx, fy, fw, fh in (big, small):
        o.append(pen.rect(fx, fy, fw, fh, 3.0, fill="none", over=0.6))
        o.append(pen.rect(fx + fw * 0.18, fy + fh * 0.12, fw * 0.64, fh * 0.76, 1.2, fill=PAPER, over=0.2))
    o.append(pen.stroke([(x + w * 0.2, y + h * 0.8), (x + w * 0.16, y + h * 0.97), (x + w * 0.24, y + h * 0.97)], 2.0, closed=True, fill=INK))  # the depressor weight
    o.append(pen.line((x + w * 0.2, y + h * 0.26), (x + w * 0.2, y + h * 0.8), 1.2, amp=0.1))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def ctd(pen, x, y, w, h, p, fs):
    """A CTD rosette: a lifting bail and cable, a ring of water-sampling bottles (each a stout cylinder with dark end caps and a
    band at the neck) round a frame, the CTD sensor package low in the middle, and three feet."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.8, p, fs)
    cx = x + w / 2
    top, bot = y + h * 0.2, y + h * 0.78
    rx, ry = w * 0.46, h * 0.055
    o = [pen.line((cx, y), (cx, top - h * 0.08), 2.0, amp=0.1),
         pen.stroke([(cx - w * 0.12, top - h * 0.02), (cx, top - h * 0.1), (cx + w * 0.12, top - h * 0.02)], 2.2)]
    for dx in (-0.85, 0.0, 0.85):  # the feet
        o.append(pen.line((cx + dx * rx * 0.85, bot), (cx + dx * rx * 0.95, y + h * 0.96), 2.6, amp=0.1))
    bw = w * 0.17
    angles = [0.35 + math.tau * k / 6 for k in range(6)]
    for a in sorted(angles, key=lambda a: math.sin(a)):  # back bottles first, so the front ones overlap them
        bx = cx + rx * 0.82 * math.cos(a)
        front = math.sin(a) >= 0
        o.append(pen.rect(bx - bw / 2, top, bw, bot - top, 2.6 if front else 1.8, fill=PAPER if front else SOFT, over=0.5))
        o.append(pen.line((bx - bw * 0.28, top + h * 0.06), (bx - bw * 0.28, bot - h * 0.06), 1.2, amp=0.1, color=MID))  # a highlight down the side
        o.append(pen.rect(bx - bw * 0.58, top - h * 0.025, bw * 1.16, h * 0.05, 1.8, fill=INK, over=0))  # the end caps
        o.append(pen.rect(bx - bw * 0.58, bot - h * 0.025, bw * 1.16, h * 0.05, 1.8, fill=INK, over=0))
        o.append(pen.line((bx - bw * 0.5, top + h * 0.12), (bx + bw * 0.5, top + h * 0.12), 1.4, amp=0.05))  # the band at the neck
    o.append(pen.rect(cx - w * 0.075, bot - h * 0.27, w * 0.15, h * 0.35, 2.4, fill=INK, over=0))  # the CTD sensor package
    o.append(pen.line((cx - w * 0.03, bot + h * 0.08), (cx - w * 0.03, bot + h * 0.14), 1.6, amp=0.05))
    o.append(pen.line((cx + w * 0.03, bot + h * 0.08), (cx + w * 0.03, bot + h * 0.14), 1.6, amp=0.05))
    o.append(pen.ellipse(cx, top, rx, ry, 3.0, fill="none"))
    o.append(pen.ellipse(cx, bot, rx, ry, 3.0, fill="none"))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def thermometer(pen, x, y, w, h, p, fs):
    x, y, w, h = _fit(x, y, w, h, 0.28)
    cx, bulb = x + w * 0.5, min(w * 0.42, h * 0.14)
    tube = w * 0.14
    o = [pen.stroke([(cx - tube, y + h - bulb * 1.5), (cx - tube, y + h * 0.1), (cx, y + h * 0.04), (cx + tube, y + h * 0.1), (cx + tube, y + h - bulb * 1.5)], 2.4),
         pen.ellipse(cx, y + h - bulb, bulb, bulb, 2.4, fill=INK, jit=0.01),
         pen.line((cx, y + h * 0.4), (cx, y + h - bulb), 3.6, amp=0.1)]
    o += [pen.line((cx + tube, y + h * (0.12 + 0.1 * i)), (cx + tube + w * 0.14, y + h * (0.12 + 0.1 * i)), 1.4, amp=0.1) for i in range(6)]
    if p.get("label"):
        o.append(text(cx, y + h + 4, [p["label"]], max(11.0, fs * 0.93), anchor="middle"))
    return "".join(o)


# ---------------------------------------------------------------- schematic science props
# Generic pictures of common equipment and analytical steps. They are schematic: nothing about their
# shape, count or size means anything, so a caption carries every claim and the prop's `label` or the panel says
# "schematic". None of them draws a number.

def _under(x, y, w, h, ratio, p, fs):
    """Fit an object of width/height `ratio` into the box with room under it for the prop's label; return the
    fitted box, the label lines and their font size (so a label never crosses the object or leaves the box)."""
    (fx, fy, fw, fh), lines, fsb = _labelled_fit(x, y, w, h, ratio, p.get("label"), fs)
    return fx, fy, fw, fh, lines, fsb


def _caption(o, x, y, w, h, lines, fsb):
    if lines:
        o.append(text(x + w / 2, y + h + 6, lines, fsb, anchor="middle", lh=1.1))


def sequence(pen, x, y, w, h, p, fs):
    """A strip of DNA letters (four grey tones for the four bases) with one stretch bracketed and labelled, as the
    marker gene is in a metabarcoding paper. The pattern is fixed and means nothing."""
    x, y, w, h = _fit(x, y, w, h, 3.2)
    n, cell = 22, w / 22
    tones = [PAPER, SOFT, MID, INK]
    pattern = [0, 2, 3, 1, 1, 0, 3, 2, 0, 1, 3, 3, 2, 0, 1, 2, 3, 0, 0, 1, 2, 3]
    top, ch = y + h * 0.5, h * 0.42
    o = []
    for i in range(n):
        o.append(pen.rect(x + i * cell, top, cell, ch, 1.6, fill=tones[pattern[i]], over=0))
    a, b = 6, 14
    bx1, bx2 = x + a * cell, x + b * cell
    o.append(pen.stroke([(bx1, top - 6), (bx1, top - 14), (bx2, top - 14), (bx2, top - 6)], 2.2))
    if p.get("label"):
        o.append(text((bx1 + bx2) / 2, top - 18 - max(11.0, fs * 0.93) * 1.2, wrap(p["label"], w * 0.9, max(11.0, fs * 0.93)), max(11.0, fs * 0.93), anchor="middle", lh=1.1))
    return "".join(o)


def tree(pen, x, y, w, h, p, fs):
    """A branching tree (a phylogeny, drawn as a cladogram): tips on the right, optionally named by `items`."""
    items = p.get("items", [])
    n = clamp(len(items) or 6, 3, 9)
    fsb = max(11.0, fs * 0.93)
    names = [it.get("label", "") for it in items][:n] + [""] * (n - len(items))
    label_w = max((len(t) for t in names), default=0) * fsb * CHAR_W
    tx = x + w - min(label_w + 8, w * 0.45)
    x0, top, span = x + 4, y + 6, (h - 12)
    step = span / max(n - 1, 1)
    o = []

    def build(lo, hi):
        """Returns (x, y, height) of the node covering tips lo..hi-1, drawing its branches."""
        if hi - lo == 1:
            return tx, top + lo * step, 0
        mid = (lo + hi) // 2
        l, r = build(lo, mid), build(mid, hi)
        ht = max(l[2], r[2]) + 1
        nx = tx - ht * (tx - x0) / (ceil_log + 1)
        for c in (l, r):
            o.append(pen.line((nx, c[1]), (c[0], c[1]), 2.0, amp=0.3))
        o.append(pen.line((nx, l[1]), (nx, r[1]), 2.0, amp=0.3))
        return nx, (l[1] + r[1]) / 2, ht

    ceil_log = max(1, math.ceil(math.log2(n)))
    rx, ry, _ = build(0, n)
    o.append(pen.line((x0, ry), (rx, ry), 2.0, amp=0.3))
    for i, t in enumerate(names):
        if t:
            o.append(text(tx + 6, top + i * step - fsb * 0.6, [t], fsb))
    return "".join(o)


def clusters(pen, x, y, w, h, p, fs):
    """Groups of dots on two axes: sequences clustered into units, or samples in an ordination. The dots are
    schematic (their number and places mean nothing); each `items` entry is one group, named by its `label`."""
    items = p.get("items", [])
    k = clamp(len(items) or 3, 1, 4)
    fsb = max(11.0, fs * 0.93)
    x, y, w, h = x + 4, y + 4, w - 8, h - 8
    o = [pen.arrow((x, y + h), (x, y), 1.8, head=7), pen.arrow((x, y + h), (x + w, y + h), 1.8, head=7)]
    centres = [(0.28, 0.66), (0.7, 0.3), (0.62, 0.74), (0.3, 0.26)][:k]
    offs = [(0, 0), (0.07, -0.05), (-0.06, 0.06), (0.05, 0.07), (-0.07, -0.04), (0.0, 0.11), (-0.02, -0.1), (0.1, 0.01)]
    r = max(3.5, min(w, h) * 0.035)
    for ci, (cx, cy) in enumerate(centres):
        px, py = x + 10 + cx * (w - 20), y + 10 + cy * (h - 20)
        o.append(f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{w * 0.15:.1f}" ry="{h * 0.16:.1f}" fill="none" stroke="{MID}" stroke-width="1.4" stroke-dasharray="4 4"/>')
        for dx, dy in offs:
            dxp, dyp = px + dx * w * 1.0, py + dy * h * 1.0
            if ci % 3 == 0:
                o.append(_dot(dxp, dyp, r))
            elif ci % 3 == 1:
                o.append(f'<circle cx="{dxp:.1f}" cy="{dyp:.1f}" r="{r:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="1.6"/>')
            else:
                o.append(f'<circle cx="{dxp:.1f}" cy="{dyp:.1f}" r="{r:.1f}" fill="{MID}" stroke="{INK}" stroke-width="1.2"/>')
        if ci < len(items) and items[ci].get("label"):
            o.append(text(px, py + h * 0.17, wrap(items[ci]["label"], w * 0.3, fsb), fsb, anchor="middle", lh=1.1))
    if p.get("label"):
        o.append(text(x + w, y + h + 3, [p["label"]], fsb, anchor="end"))
    return "".join(o)


def network(pen, x, y, w, h, p, fs):
    """A small neural network: layers of nodes joined by thin lines, input on the left and output on the right.
    The node counts are fixed and mean nothing; `items` may name the input (first) and output (last)."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.5, p, fs)
    layers = [3, 4, 4, 2]
    gx = w / (len(layers) - 1)
    pos = []
    for li, n in enumerate(layers):
        col = [(x + li * gx, y + h * (0.12 + 0.76 * (j + 0.5) / n)) for j in range(n)]
        pos.append(col)
    o = []
    for a, b in zip(pos, pos[1:]):
        for (x1, y1) in a:
            for (x2, y2) in b:
                o.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{MID}" stroke-width="0.9"/>')
    for col in pos:
        for (px, py) in col:
            o.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{min(w, h) * 0.05:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>')
    items = p.get("items", [])
    if items and items[0].get("label"):
        o.append(text(x, y + h + 2, [items[0]["label"]], fsb, anchor="middle"))
    if len(items) > 1 and items[-1].get("label"):
        o.append(text(x + w, y + h + 2, [items[-1]["label"]], fsb, anchor="middle"))
    _caption(o, x, y + (fsb * 1.1 if items else 0), w, h, lines, fsb)
    return "".join(o)


def database(pen, x, y, w, h, p, fs):
    """A reference library: a card-catalogue cabinet with its top drawer pulled open to show a row of record cards, each
    marked with a short strip of DNA-letter cells; two closed drawers below. The cards mean nothing."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.85, p, fs)
    tones = [PAPER, SOFT, MID, INK]
    o = [pen.rect(x + w * 0.04, y + h * 0.1, w * 0.92, h * 0.34, 2.4, fill=INK, over=0.5)]  # the open drawer's inside
    for i in range(7):  # the cards standing in it
        cx = x + w * (0.09 + i * 0.125)
        top = y + h * (0.04 + (0.015 if i % 2 else 0.0))
        o.append(pen.rect(cx, top, w * 0.1, h * 0.38, 1.8, fill=PAPER, over=0.4))
        for k in range(3):
            o.append(pen.rect(cx + w * 0.012 + k * w * 0.026, top + h * 0.035, w * 0.024, h * 0.03, 0.9, fill=tones[(i + k) % 4], over=0))
        o.append(pen.line((cx + w * 0.012, top + h * 0.1), (cx + w * 0.088, top + h * 0.1), 0.9, amp=0.05, color=MID))
    drawers = ((0.42, 0.18, True), (0.6, 0.19, False), (0.79, 0.19, False))
    for top, hh, open_ in drawers:
        o.append(pen.rect(x, y + h * top, w, h * hh, 2.6, fill=SOFT if open_ else PAPER, over=0.6))
        o.append(pen.rect(x + w * 0.4, y + h * (top + hh * 0.18), w * 0.2, h * hh * 0.18, 1.8, fill=PAPER, over=0.2))  # the label plate
        o.append(pen.rect(x + w * 0.38, y + h * (top + hh * 0.56), w * 0.24, h * hh * 0.16, 1.8, fill=MID, over=0))  # the handle
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def filter_rig(pen, x, y, w, h, p, fs):
    """Water filtration: a sample bottle, a tube to a filter housing, then a pump. (How eDNA is caught on a filter.)"""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.2, p, fs)
    o = [pen.stroke([(x + w * 0.04, y + h * 0.4), (x + w * 0.04, y + h * 0.94), (x + w * 0.2, y + h * 0.94), (x + w * 0.2, y + h * 0.4), (x + w * 0.16, y + h * 0.3),
                     (x + w * 0.16, y + h * 0.2), (x + w * 0.08, y + h * 0.2), (x + w * 0.08, y + h * 0.3)], 2.4, closed=True, fill=PAPER),
         pen.line((x + w * 0.05, y + h * 0.7), (x + w * 0.19, y + h * 0.7), 1.4, amp=0.4, color=MID),
         pen.stroke([(x + w * 0.12, y + h * 0.2), (x + w * 0.12, y + h * 0.08), (x + w * 0.42, y + h * 0.08), (x + w * 0.42, y + h * 0.42)], 2.0),
         pen.rect(x + w * 0.35, y + h * 0.42, w * 0.14, h * 0.3, 2.4, fill=SOFT, over=1),
         pen.line((x + w * 0.35, y + h * 0.57), (x + w * 0.49, y + h * 0.57), 1.6, amp=0.2),
         pen.stroke([(x + w * 0.42, y + h * 0.72), (x + w * 0.42, y + h * 0.9), (x + w * 0.66, y + h * 0.9)], 2.0),
         pen.rect(x + w * 0.66, y + h * 0.62, w * 0.28, h * 0.36, 2.6, fill=PAPER, over=1),
         pen.ellipse(x + w * 0.8, y + h * 0.8, w * 0.07, h * 0.12, 2.0, fill=PAPER),
         pen.arrow((x + w * 0.8, y + h * 0.74), (x + w * 0.8, y + h * 0.7), 1.6, head=4)]
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def tubes(pen, x, y, w, h, p, fs):
    """A rack of sample tubes with caps: extraction, PCR, or stored samples. The fill levels mean nothing."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.7, p, fs)
    o = [pen.rect(x, y + h * 0.72, w, h * 0.18, 2.4, fill=SOFT, over=1)]
    levels = [0.5, 0.35, 0.6, 0.4, 0.55, 0.3]
    n = 6
    tw = w / n
    for i in range(n):
        tx = x + i * tw + tw * 0.2
        o.append(pen.stroke([(tx, y + h * 0.18), (tx, y + h * 0.78), (tx + tw * 0.3, y + h * 0.9), (tx + tw * 0.6, y + h * 0.78), (tx + tw * 0.6, y + h * 0.18)], 2.2, closed=True, fill=PAPER))
        lv = y + h * (0.78 - 0.5 * levels[i])
        o.append(pen.stroke([(tx + 1, lv), (tx + 1, y + h * 0.78), (tx + tw * 0.3, y + h * 0.88), (tx + tw * 0.6 - 1, y + h * 0.78), (tx + tw * 0.6 - 1, lv)], 1.0, closed=True, fill=SOFT, color=MID))
        o.append(pen.rect(tx - 2, y + h * 0.08, tw * 0.6 + 4, h * 0.1, 2.0, fill=MID if i % 2 else INK, over=0))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def sequencer(pen, x, y, w, h, p, fs):
    """A benchtop DNA sequencer: a box with a small screen, a loading slot and a status light."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.3, p, fs)
    o = [pen.poly([(x, y + h * 0.2), (x + w * 0.9, y + h * 0.2), (x + w, y + h * 0.08), (x + w * 0.1, y + h * 0.08)], 2.4, fill=SOFT, jit=0.3),
         pen.rect(x, y + h * 0.2, w * 0.9, h * 0.8, 2.6, fill=PAPER, over=1),
         pen.poly([(x + w * 0.9, y + h * 0.2), (x + w, y + h * 0.08), (x + w, y + h * 0.88), (x + w * 0.9, y + h)], 2.4, fill=SOFT, jit=0.3),
         pen.rect(x + w * 0.1, y + h * 0.3, w * 0.34, h * 0.28, 2.0, fill=SOFT, over=1),
         pen.rect(x + w * 0.1, y + h * 0.7, w * 0.5, h * 0.1, 2.0, fill=INK, over=0),
         f'<circle cx="{x + w * 0.72:.1f}" cy="{y + h * 0.36:.1f}" r="{min(w, h) * 0.04:.1f}" fill="{INK}"/>',
         pen.line((x + w * 0.15, y + h * 0.4), (x + w * 0.38, y + h * 0.4), 1.4, amp=0.3, color=MID),
         pen.line((x + w * 0.15, y + h * 0.48), (x + w * 0.3, y + h * 0.48), 1.4, amp=0.3, color=MID)]
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def cpr(pen, x, y, w, h, p, fs):
    """A towed plankton recorder, schematic: a torpedo-shaped body with an open funnel at the front, a tail with fins
    and a line to the ship. (A generic drawing, not the real instrument.)"""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.6, p, fs)
    cy = y + h * 0.55
    o = [pen.stroke([(x, y + h * 0.05), (x + w * 0.2, cy - h * 0.1)], 1.8, color=MID),
         pen.stroke([(x + w * 0.16, cy - h * 0.28), (x + w * 0.62, cy - h * 0.3), (x + w * 0.9, cy - h * 0.12), (x + w * 0.9, cy + h * 0.12),
                     (x + w * 0.62, cy + h * 0.3), (x + w * 0.16, cy + h * 0.28), (x + w * 0.1, cy)], 2.6, closed=True, fill=PAPER),
         pen.stroke([(x + w * 0.16, cy - h * 0.28), (x + w * 0.1, cy), (x + w * 0.16, cy + h * 0.28)], 2.6, fill=SOFT),
         pen.stroke([(x + w * 0.9, cy - h * 0.12), (x + w * 0.99, cy - h * 0.34), (x + w * 0.95, cy - h * 0.02)], 2.2, closed=True, fill=SOFT),
         pen.stroke([(x + w * 0.9, cy + h * 0.12), (x + w * 0.99, cy + h * 0.34), (x + w * 0.95, cy + h * 0.02)], 2.2, closed=True, fill=SOFT),
         pen.line((x + w * 0.3, cy), (x + w * 0.6, cy), 1.4, amp=0.3, color=MID),
         pen.line((x + w * 0.3, cy - h * 0.12), (x + w * 0.6, cy - h * 0.12), 1.4, amp=0.3, color=MID),
         pen.line((x + w * 0.3, cy + h * 0.12), (x + w * 0.6, cy + h * 0.12), 1.4, amp=0.3, color=MID)]
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def echosounder(pen, x, y, w, h, p, fs):
    """An echosounder, schematic: a bit of hull at the top, a cone of sound below it with echo arcs, and a few dots
    for what it sees. The dots and arcs mean nothing in number or place."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.1, p, fs)
    cx = x + w / 2
    o = [pen.stroke([(x + w * 0.1, y + h * 0.04), (x + w * 0.9, y + h * 0.04), (x + w * 0.78, y + h * 0.16), (x + w * 0.22, y + h * 0.16)], 2.4, closed=True, fill=SOFT),
         pen.line((cx, y + h * 0.16), (x + w * 0.04, y + h * 0.98), 1.8, amp=0.4, dash="5 4"),
         pen.line((cx, y + h * 0.16), (x + w * 0.96, y + h * 0.98), 1.8, amp=0.4, dash="5 4")]
    for f, rw in ((0.3, 0.13), (0.5, 0.26), (0.7, 0.38)):  # echo arcs
        yy = y + h * (0.16 + f * 0.82)
        o.append(pen.stroke([(cx - w * rw, yy), (cx, yy + h * 0.05), (cx + w * rw, yy)], 1.4, color=MID))
    for dx, dy in ((-0.1, 0.5), (0.08, 0.42), (0.16, 0.66), (-0.2, 0.72), (0.0, 0.8)):
        o.append(_dot(cx + dx * w, y + h * dy, max(3, min(w, h) * 0.022)))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def venn(pen, x, y, w, h, p, fs):
    """Two overlapping circles (what two methods share and what only one finds). `items` names the two circles;
    `label` names the overlap. The sizes are schematic and mean nothing."""
    items = p.get("items", [])
    fsb = max(11.0, fs * 0.93)
    x, y, w, h = _fit(x, y, w, h, 1.7)
    r = h * 0.48
    c1, c2 = (x + w * 0.35, y + h / 2), (x + w * 0.65, y + h / 2)
    o = [pen.ellipse(c1[0], c1[1], r, r, 2.4, fill="none"), pen.ellipse(c2[0], c2[1], r, r, 2.4, fill="none")]
    for c, idx, anchor_x in ((c1, 0, x + w * 0.21), (c2, 1, x + w * 0.79)):
        if idx < len(items) and items[idx].get("label"):
            o.append(text(anchor_x, y + h / 2 - fsb * 0.6, wrap(items[idx]["label"], w * 0.22, fsb), fsb, anchor="middle", lh=1.1))
    if p.get("label"):
        o.append(text(x + w / 2, y + h / 2 - fsb * 0.6, wrap(p["label"], w * 0.2, fsb), fsb, anchor="middle", lh=1.1))
    return "".join(o)


def satellite(pen, x, y, w, h, p, fs):
    """A satellite with two solar panels and a dish, and a cone down to a footprint on the ground: remote sensing, schematic."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.4, p, fs)
    sx, sy = x + w * 0.36, y + h * 0.2
    o = [pen.line((sx, sy + h * 0.08), (x + w * 0.1, y + h * 0.9), 1.6, amp=0.4, dash="5 4"),
         pen.line((sx, sy + h * 0.08), (x + w * 0.62, y + h * 0.9), 1.6, amp=0.4, dash="5 4"),
         pen.stroke([(x + w * 0.04, y + h * 0.9), (x + w * 0.36, y + h * 0.99), (x + w * 0.7, y + h * 0.9)], 2.4, color=INK),
         pen.rect(sx - w * 0.07, sy - h * 0.1, w * 0.14, h * 0.2, 2.4, fill=PAPER, over=1)]
    for dx in (-1, 1):  # the two solar panels, with their cell lines
        px = sx + dx * w * 0.07 + (w * 0.05 if dx > 0 else -w * 0.22)
        o.append(pen.rect(px, sy - h * 0.06, w * 0.17, h * 0.12, 2.2, fill=SOFT, over=1))
        for k in (1, 2):
            o.append(pen.line((px + w * 0.17 * k / 3, sy - h * 0.06), (px + w * 0.17 * k / 3, sy + h * 0.06), 1.0, amp=0.1, color=MID))
    o.append(pen.stroke([(sx, sy + h * 0.1), (sx, sy + h * 0.16), (sx - w * 0.04, sy + h * 0.21), (sx + w * 0.04, sy + h * 0.21)], 1.8, closed=True, fill=PAPER))  # the dish
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def radar(pen, x, y, w, h, p, fs):
    """A radar dish: a tilted parabolic dish on a tripod, with a feed horn held out on struts and arcs of signal
    leaving it. Schematic."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.15, p, fs)
    th = -0.72  # the dish looks up and to the right
    d = (math.cos(th), math.sin(th))
    pp = (-d[1], d[0])
    cx, cy = x + w * 0.34, y + h * 0.46
    a, b = w * 0.24, w * 0.085
    rim = [(cx + a * math.cos(t) * pp[0] + b * math.sin(t) * d[0], cy + a * math.cos(t) * pp[1] + b * math.sin(t) * d[1]) for t in [math.tau * k / 24 for k in range(24)]]
    e1, e2 = (cx + a * pp[0], cy + a * pp[1]), (cx - a * pp[0], cy - a * pp[1])
    ctrl = (cx - d[0] * w * 0.4, cy - d[1] * w * 0.4)
    bowl = [((1 - t) ** 2 * e1[0] + 2 * (1 - t) * t * ctrl[0] + t * t * e2[0], (1 - t) ** 2 * e1[1] + 2 * (1 - t) * t * ctrl[1] + t * t * e2[1]) for t in [k / 12 for k in range(13)]]
    mid = bowl[6]
    base_y = y + h * 0.95
    o = [pen.line((mid[0], mid[1]), (x + w * 0.34, base_y), 3.2, amp=0.3),
         pen.line((x + w * 0.34, y + h * 0.72), (x + w * 0.16, base_y), 2.4, amp=0.3), pen.line((x + w * 0.34, y + h * 0.72), (x + w * 0.52, base_y), 2.4, amp=0.3),
         pen.stroke(bowl, 2.6, closed=True, fill=SOFT), pen.stroke(rim, 2.6, closed=True, fill=PAPER),
         pen.ellipse(cx, cy, a * 0.62, b * 0.62, 1.2, fill="none")]
    tip = (cx + d[0] * w * 0.3, cy + d[1] * w * 0.3)
    for sgn in (-1, 1):  # the feed horn's struts
        o.append(pen.line((cx + sgn * a * 0.8 * pp[0], cy + sgn * a * 0.8 * pp[1]), tip, 1.4, amp=0.1))
    o.append(pen.stroke([(tip[0] - pp[0] * w * 0.025, tip[1] - pp[1] * w * 0.025), (tip[0] + pp[0] * w * 0.025, tip[1] + pp[1] * w * 0.025), (tip[0] + d[0] * w * 0.05, tip[1] + d[1] * w * 0.05)], 1.8, closed=True, fill=INK))
    for r in (0.16, 0.28, 0.4):  # the signal
        pts = [(tip[0] + w * r * math.cos(th + t), tip[1] + w * r * math.sin(th + t)) for t in [k * 0.09 for k in range(-4, 5)]]
        o.append(pen.stroke(pts, 1.8, color=MID))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def radarscreen(pen, x, y, w, h, p, fs):
    """A radar display: a round screen with range rings, a sweep and a few blips. The blips mean nothing."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.0, p, fs)
    r = min(w, h) / 2
    cx, cy = x + w / 2, y + h / 2
    o = [pen.stroke([(cx + r * (1 + pen.n(0.006)) * math.cos(t), cy + r * (1 + pen.n(0.006)) * math.sin(t)) for t in [math.tau * k / 40 for k in range(40)]], 2.8, closed=True, fill=PAPER)]
    for f in (0.34, 0.67):
        o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r * f:.1f}" fill="none" stroke="{MID}" stroke-width="1.3"/>')
    o.append(pen.line((cx - r, cy), (cx + r, cy), 1.2, amp=0.1, color=MID))
    o.append(pen.line((cx, cy - r), (cx, cy + r), 1.2, amp=0.1, color=MID))
    a0, a1 = -1.2, -0.45  # the sweep, a wedge from the centre
    wedge = [(cx, cy)] + [(cx + r * 0.95 * math.cos(a), cy + r * 0.95 * math.sin(a)) for a in [a0 + (a1 - a0) * k / 8 for k in range(9)]]
    o.append(pen.stroke(wedge, 1.6, closed=True, fill=SOFT, color=MID))
    o.append(pen.line((cx, cy), (cx + r * 0.95 * math.cos(a1), cy + r * 0.95 * math.sin(a1)), 2.4, amp=0.1))
    for fx, fy in ((0.42, -0.5), (-0.4, 0.3), (0.2, 0.55), (-0.15, -0.62)):  # the blips
        o.append(_dot(cx + fx * r, cy + fy * r, max(2.5, r * 0.05)))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def icecore(pen, x, y, w, h, p, fs):
    """An ice core: one regular cylinder with straight sides, a flat top, two cuts across it where it was divided into
    sections, and faint layer lines. The layers mean nothing."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.3, p, fs)
    ry = w * 0.16
    top, bot = y + ry, y + h - ry

    def front(yy, k=16, inset=0.0):  # the front half of an ellipse at height yy
        return [(x + w / 2 + (w / 2 - inset) * math.cos(a), yy + ry * math.sin(a)) for a in [math.pi * i / k for i in range(k + 1)]]

    belly = front(bot)
    o = [pen.stroke([(x, top)] + belly[::-1] + [(x + w, top)], 2.6, closed=True, fill=PAPER)]
    for f in (0.1, 0.19, 0.27, 0.44, 0.52, 0.6, 0.78, 0.86):  # the faint layers
        o.append(pen.stroke(front(top + (bot - top) * f, inset=2), 1.0, color=MID))
    for f in (0.34, 0.68):  # where the core was cut into sections
        o.append(pen.stroke(front(top + (bot - top) * f), 2.4, color=INK))
    o.append(pen.ellipse(x + w / 2, top, w / 2, ry, 2.6, fill=SOFT))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def massspec(pen, x, y, w, h, p, fs):
    """A mass spectrometer or chromatograph: a bench instrument with a long column along the front, a small screen and a
    few peaks drawn on it (the peaks mean nothing)."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.8, p, fs)
    o = [pen.rect(x, y + h * 0.1, w * 0.62, h * 0.8, 2.6, fill=PAPER, over=1),
         pen.rect(x + w * 0.05, y + h * 0.18, w * 0.3, h * 0.36, 2.0, fill=SOFT, over=1),
         pen.rect(x + w * 0.62, y + h * 0.34, w * 0.38, h * 0.5, 2.6, fill=PAPER, over=1),
         pen.stroke([(x + w * 0.62, y + h * 0.5), (x + w * 0.5, y + h * 0.5), (x + w * 0.46, y + h * 0.7), (x + w * 0.2, y + h * 0.7)], 2.0),
         f'<circle cx="{x + w * 0.5:.1f}" cy="{y + h * 0.26:.1f}" r="{min(w, h) * 0.035:.1f}" fill="{INK}"/>']
    for i, hgt in enumerate((0.2, 0.5, 0.3, 0.8, 0.4)):  # peaks on the screen
        px = x + w * (0.08 + 0.05 * i)
        o.append(pen.line((px, y + h * 0.5), (px, y + h * (0.5 - 0.28 * hgt)), 2.2, amp=0.1))
    o.append(pen.line((x + w * 0.68, y + h * 0.5), (x + w * 0.94, y + h * 0.5), 1.4, amp=0.3, color=MID))
    o.append(pen.line((x + w * 0.68, y + h * 0.62), (x + w * 0.86, y + h * 0.62), 1.4, amp=0.3, color=MID))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def helicopter(pen, x, y, w, h, p, fs):
    """A helicopter: a bubble cockpit, a tail boom with a small rotor, a main rotor above and skids below."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.0, p, fs)
    cx = x + w * 0.38
    o = [pen.line((x + w * 0.04, y + h * 0.1), (x + w * 0.74, y + h * 0.1), 3.0, amp=0.5),
         pen.line((cx, y + h * 0.1), (cx, y + h * 0.26), 2.4, amp=0.2),
         pen.stroke([(x + w * 0.62, y + h * 0.5), (x + w * 0.98, y + h * 0.38), (x + w * 0.98, y + h * 0.46), (x + w * 0.64, y + h * 0.62)], 2.2, closed=True, fill=SOFT),
         pen.stroke([(x + w * 0.98, y + h * 0.3), (x + w * 0.98, y + h * 0.52)], 2.4),
         pen.stroke([(x + w * 0.12, y + h * 0.56), (x + w * 0.16, y + h * 0.34), (x + w * 0.34, y + h * 0.26), (x + w * 0.58, y + h * 0.3), (x + w * 0.66, y + h * 0.5), (x + w * 0.54, y + h * 0.7), (x + w * 0.22, y + h * 0.7)], 2.6, closed=True, fill=PAPER),
         pen.stroke([(x + w * 0.16, y + h * 0.56), (x + w * 0.2, y + h * 0.38), (x + w * 0.32, y + h * 0.34), (x + w * 0.34, y + h * 0.56)], 1.8, closed=True, fill=SOFT),
         pen.line((x + w * 0.2, y + h * 0.84), (x + w * 0.62, y + h * 0.84), 2.6, amp=0.3),
         pen.line((x + w * 0.3, y + h * 0.7), (x + w * 0.3, y + h * 0.84), 2.0, amp=0.1),
         pen.line((x + w * 0.52, y + h * 0.7), (x + w * 0.52, y + h * 0.84), 2.0, amp=0.1)]
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def drone(pen, x, y, w, h, p, fs):
    """A quadcopter drone: a body, four arms with rotor discs and a small camera underneath."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.6, p, fs)
    cx, cy = x + w / 2, y + h * 0.5
    o = []
    for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        ex, ey = cx + dx * w * 0.36, cy + dy * h * 0.2
        o.append(pen.line((cx, cy), (ex, ey), 2.4, amp=0.2))
        o.append(pen.line((ex, ey), (ex, ey - h * 0.1), 1.8, amp=0.1))
        o.append(f'<ellipse cx="{ex:.1f}" cy="{ey - h * 0.12:.1f}" rx="{w * 0.15:.1f}" ry="{h * 0.045:.1f}" fill="{SOFT}" stroke="{INK}" stroke-width="1.8"/>')
    o.append(pen.stroke([(cx - w * 0.1, cy - h * 0.08), (cx + w * 0.1, cy - h * 0.08), (cx + w * 0.12, cy + h * 0.1), (cx - w * 0.12, cy + h * 0.1)], 2.6, closed=True, fill=PAPER))
    o.append(f'<circle cx="{cx:.1f}" cy="{cy + h * 0.2:.1f}" r="{min(w, h) * 0.07:.1f}" fill="{INK}"/>')
    o.append(pen.line((cx, cy + h * 0.1), (cx, cy + h * 0.14), 1.8, amp=0.1))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def aquarium(pen, x, y, w, h, p, fs):
    """An aquarium tank: a glass box with water, a wavy surface, a few bubbles and gravel."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.4, p, fs)
    top = y + h * 0.2
    o = [pen.rect(x, y + h * 0.1, w, h * 0.88, 2.6, fill=PAPER, over=1),
         f'<rect x="{x + 2:.1f}" y="{top:.1f}" width="{w - 4:.1f}" height="{y + h * 0.96 - top:.1f}" fill="{SOFT}" stroke="none" opacity="0.7"/>',
         pen.stroke([(x + 2, top), (x + w * 0.25, top - 4), (x + w * 0.5, top + 2), (x + w * 0.75, top - 3), (x + w - 2, top)], 1.8, color=MID)]
    for i in range(7):
        o.append(f'<ellipse cx="{x + w * (0.1 + 0.13 * i):.1f}" cy="{y + h * 0.93:.1f}" rx="{w * 0.05:.1f}" ry="{h * 0.03:.1f}" fill="{MID}"/>')
    for bx, by, br in ((0.2, 0.7, 0.025), (0.24, 0.55, 0.018), (0.27, 0.42, 0.012), (0.78, 0.6, 0.02), (0.8, 0.45, 0.013)):
        o.append(f'<circle cx="{x + w * bx:.1f}" cy="{y + h * by:.1f}" r="{w * br:.1f}" fill="{PAPER}" stroke="{INK}" stroke-width="1.4"/>')
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def freezer(pen, x, y, w, h, p, fs):
    """A freezer: an upright box with a door, a handle and a snowflake."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.8, p, fs)
    o = [pen.rect(x, y, w, h, 2.8, fill=PAPER, over=1), pen.line((x, y + h * 0.3), (x + w, y + h * 0.3), 2.0, amp=0.3),
         pen.rect(x + w * 0.82, y + h * 0.1, w * 0.06, h * 0.14, 2.0, fill=SOFT, over=0),
         pen.rect(x + w * 0.82, y + h * 0.4, w * 0.06, h * 0.3, 2.0, fill=SOFT, over=0)]
    cx, cy, r = x + w * 0.4, y + h * 0.62, min(w, h) * 0.2
    for k in range(3):
        a = math.pi * k / 3
        o.append(pen.line((cx - r * math.cos(a), cy - r * math.sin(a)), (cx + r * math.cos(a), cy + r * math.sin(a)), 1.8, amp=0.1, color=INK))
        for sgn in (-1, 1):
            bx, by = cx + sgn * r * 0.7 * math.cos(a), cy + sgn * r * 0.7 * math.sin(a)
            o.append(pen.line((bx, by), (bx + r * 0.25 * math.cos(a + 1.0), by + r * 0.25 * math.sin(a + 1.0)), 1.2, amp=0.05, color=MID))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def tag(pen, x, y, w, h, p, fs):
    """A satellite tag for an animal: a streamlined case on a glued base plate, a strip of solar cells on top, a thin whip
    antenna with signal arcs leaving it. It is stuck to fur or feathers; draw it beside the animal, or on it."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.7, p, fs)
    o = [pen.rect(x + w * 0.04, y + h * 0.86, w * 0.76, h * 0.1, 2.2, fill=SOFT, over=0.4)]
    case = [(x + w * 0.08, y + h * 0.86), (x + w * 0.1, y + h * 0.56), (x + w * 0.28, y + h * 0.4), (x + w * 0.6, y + h * 0.38), (x + w * 0.78, y + h * 0.6), (x + w * 0.78, y + h * 0.86)]
    o.append(pen.stroke(case, 2.6, closed=True, fill=PAPER))
    for i in range(5):  # the solar cells along the top
        cx = x + w * (0.22 + i * 0.1)
        o.append(pen.rect(cx, y + h * (0.43 + abs(i - 2) * 0.012), w * 0.085, h * 0.12, 1.2, fill=SOFT, over=0))
    o.append(pen.line((x + w * 0.3, y + h * 0.7), (x + w * 0.62, y + h * 0.7), 1.2, amp=0.1, color=MID))
    tip = (x + w * 0.9, y + h * 0.08)
    o.append(pen.line((x + w * 0.68, y + h * 0.42), tip, 1.8, amp=0.1))
    o.append(_dot(tip[0], tip[1], max(3.0, w * 0.018)))
    for r in (0.07, 0.13, 0.19):  # the signal
        pts = [(tip[0] + w * r * math.cos(a), tip[1] + w * r * math.sin(a)) for a in [math.radians(k) for k in range(-70, 20, 15)]]
        o.append(pen.stroke(pts, 1.6, color=MID))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def scatter(pen, x, y, w, h, p, fs):
    """Dots round a fitted line, on two axes: a relationship or a calibration. The dots and the slope are schematic and
    mean nothing; `x_label` and `y_label` name the axes."""
    fsb = max(11.0, fs * 0.93)
    ox, oy, ow, oh = x, y, w, h
    x, y, w, h = _fit(x, y, w, h - (fsb * 1.3 if p.get("x_label") else 0), 1.4)
    o = [pen.arrow((x, y + h), (x, y), 1.8, head=7), pen.arrow((x, y + h), (x + w, y + h), 1.8, head=7)]
    offs = [0.08, -0.1, 0.05, -0.04, 0.12, -0.08, 0.02, 0.1, -0.12, 0.04, -0.02, 0.09, -0.07, 0.0]
    n = len(offs)
    for i, off in enumerate(offs):
        t = (i + 0.5) / n
        o.append(_dot(x + 10 + t * (w - 24), y + h - 10 - (0.12 + 0.7 * t + off) * (h - 24), max(3.0, min(w, h) * 0.025)))
    o.append(pen.line((x + 6, y + h - 10 - 0.1 * (h - 24)), (x + w - 8, y + h - 10 - 0.84 * (h - 24)), 2.2, amp=0.2, dash="6 4"))
    if p.get("x_label"):
        o.append(text(x + w / 2, y + h + 4, [p["x_label"]], fsb, anchor="middle"))
    if p.get("y_label"):
        o.append(text(x + 6, y - fsb * 0.2, [p["y_label"]], fsb))
    return "".join(o)


def boxplot(pen, x, y, w, h, p, fs):
    """Box-and-whisker plots for two to four groups on one axis (a comparison of spreads); `items` name the groups.
    The boxes are schematic: their heights and the medians mean nothing."""
    items = p.get("items", [])
    k = clamp(len(items) or 3, 2, 4)
    fsb = max(11.0, fs * 0.93)
    x, y, w, h = _fit(x, y, w, h - fsb * 1.4, 1.4)
    o = [pen.arrow((x, y + h), (x, y), 1.8, head=7), pen.line((x, y + h), (x + w, y + h), 1.8, amp=0.2)]
    specs = [(0.18, 0.5, 0.34, 0.1, 0.62), (0.3, 0.7, 0.5, 0.2, 0.8), (0.1, 0.36, 0.22, 0.04, 0.5), (0.4, 0.78, 0.58, 0.3, 0.9)]
    slot = (w - 12) / k
    for i in range(k):
        lo, hi, med, wlo, whi = specs[i]
        cx = x + 12 + slot * (i + 0.5)
        bw = slot * 0.46
        yb = lambda f: y + h - 8 - f * (h - 18)
        o.append(pen.line((cx, yb(wlo)), (cx, yb(whi)), 1.8, amp=0.1))
        for f in (wlo, whi):
            o.append(pen.line((cx - bw * 0.3, yb(f)), (cx + bw * 0.3, yb(f)), 1.8, amp=0.1))
        o.append(pen.rect(cx - bw / 2, yb(hi), bw, yb(lo) - yb(hi), 2.2, fill=SOFT if i % 2 else PAPER, over=1))
        o.append(pen.line((cx - bw / 2, yb(med)), (cx + bw / 2, yb(med)), 3.0, amp=0.1))
        if i < len(items) and items[i].get("label"):
            o.append(text(cx, y + h + 3, [items[i]["label"]], fsb, anchor="middle"))
    return "".join(o)


def modelgrid(pen, x, y, w, h, p, fs):
    """A model of the Earth: a globe with latitude and longitude lines, and a patch of it cut into grid cells. Schematic."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.4, p, fs)
    r = min(w * 0.3, h * 0.46)
    cx, cy = x + w * 0.3, y + h / 2
    o = [pen.ellipse(cx, cy, r, r, 2.6, fill=PAPER)]
    for f in (0.35, 0.7):  # meridians
        o.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r * f:.1f}" ry="{r:.1f}" fill="none" stroke="{MID}" stroke-width="1.4"/>')
    for f in (-0.5, 0.0, 0.5):  # parallels
        half = math.sqrt(1 - f * f) * r
        o.append(pen.line((cx - half, cy + f * r), (cx + half, cy + f * r), 1.4, amp=0.2, color=MID))
    gx, gy, cell = x + w * 0.72, y + h * 0.24, min(w, h) * 0.09
    for i in range(4):
        for j in range(4):
            o.append(pen.rect(gx + i * cell, gy + j * cell, cell, cell, 1.6, fill=SOFT if (i + j) % 3 == 0 else PAPER, over=0))
    o.append(pen.line((cx + r * 0.55, cy - r * 0.45), (gx, gy), 1.2, amp=0.2, color=MID, dash="4 3"))
    o.append(pen.line((cx + r * 0.55, cy - r * 0.45), (gx, gy + 4 * cell), 1.2, amp=0.2, color=MID, dash="4 3"))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


# ---------------------------------------------------------------- maps and the sea
# Scene-setting pictures for polar and ocean papers. All are schematic: a map shows real coastlines but a simplified
# projection, and every other picture here (ice, layers) is a generic sketch whose shape means nothing.

def _polar(lon, lat, cx, cy, R, edge):
    """A point on a south-polar map: the pole at the centre, 0 degrees up, longitudes increasing clockwise (east)."""
    r = (90 + lat) / (90 + edge)
    a = math.radians(lon)
    return (cx + R * r * math.sin(a), cy - R * r * math.cos(a))


def _map_frame(x, y, w, h, p, fs):
    """Fit the round map into the box, leave room for a label, and return the geometry the map and its overlays share."""
    view = p.get("view", "polar")
    edge = -50.0 if view == "polar" else -10.0
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.0, p, fs)
    return edge, x, y, w, h, lines, fsb, x + w / 2, y + h / 2, min(w, h) / 2


def _clip_south(poly, edge):
    """Cut an outline (a list of (lon, lat)) to latitudes at or south of `edge` (Sutherland-Hodgman against one parallel)."""
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ain, bin_ = a[1] <= edge, b[1] <= edge
        if ain:
            out.append(a)
        if ain != bin_:
            t = (edge - a[1]) / (b[1] - a[1])
            out.append((a[0] + (b[0] - a[0]) * t, edge))
    return out


def map_(pen, x, y, w, h, p, fs):
    """A map of the south polar region on a round disc: Antarctica with its real coast and, with `view: wide`, Australia, New
    Zealand and the other southern lands too. Land is white on a pale sea; dashed rings mark 60 and 30 degrees south. `places`
    (each `lon`, `lat`, `label`) pin named spots. Schematic: a simplified outline on an equidistant projection."""
    import mapdata
    edge, x, y, w, h, lines, fsb, cx, cy, R = _map_frame(x, y, w, h, p, fs)
    o = [pen.stroke([(cx + R * math.cos(t), cy + R * math.sin(t)) for t in [math.tau * k / 48 for k in range(48)]], 2.8, closed=True, fill=SOFT)]
    for lat in (-60, -30):  # graticule rings: only those inside the map (south of its edge)
        if lat < edge:
            r = R * (90 + lat) / (90 + edge)
            o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="none" stroke="{MID}" stroke-width="1.1" stroke-dasharray="4 5"/>')
    for poly, width in [(q, 1.6) for q in mapdata.LAND] + [(q, 2.4) for q in mapdata.ANTARCTICA]:
        poly = _clip_south(poly, edge)  # an outline that runs past the map's rim is cut at it
        if len(poly) >= 3:
            o.append(pen.poly([_polar(lon, lat, cx, cy, R, edge) for lon, lat in poly], width, fill=PAPER, jit=0.12))
    for pl in p.get("places", []):
        px, py = _polar(pl["lon"], pl["lat"], cx, cy, R, edge)
        o.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{max(3.0, R * 0.025):.1f}" fill="{INK}"/>')
        if pl.get("label"):
            right = px < cx + R * 0.3
            o.append(text(px + (8 if right else -8), py - fsb * 0.55, [pl["label"]], fsb, anchor="start" if right else "end", halo=True))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def _arrow_path(pen, pts, width=2.6, color=INK, head=9):
    """A line through `pts` with an arrowhead at its end."""
    o = [pen.stroke(pts, width, color=color)]
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    d = math.hypot(x2 - x1, y2 - y1) or 1
    ux, uy = (x2 - x1) / d, (y2 - y1) / d
    o.append(pen.stroke([(x2, y2), (x2 - ux * head - uy * head * 0.55, y2 - uy * head + ux * head * 0.55),
                         (x2 - ux * head + uy * head * 0.55, y2 - uy * head - ux * head * 0.55)], width * 0.6, closed=True, fill=color, color=color))
    return "".join(o)


def currents(pen, x, y, w, h, p, fs):
    """The major currents, as arrows, to lay over a `map` prop given the same box and `view`: the Antarctic Circumpolar
    Current running east all the way round, the Weddell and Ross gyres turning clockwise, and in the `wide` view the East
    Australian, Leeuwin, Agulhas and Humboldt currents. Schematic: where and which way, not how strong."""
    edge, x, y, w, h, lines, fsb, cx, cy, R = _map_frame(x, y, w, h, p, fs)
    o = []

    def P(lon, lat):
        return _polar(lon, lat, cx, cy, R, edge)

    for k in range(5):  # the circumpolar current: five arcs with gaps, each with a head, meandering a little
        start = k * 72 + 4
        pts = [P(start + t * 4.5, -54 + 1.1 * math.sin(math.radians((start + t * 4.5) * 3))) for t in range(15)]
        o.append(_arrow_path(pen, pts, 2.8, INK, 10))
    for lon0, lat0 in ((-40, -68.5), (178, -69)):  # the two gyres, clockwise on the page
        gx, gy = P(lon0, lat0)
        rx = ry = R * (0.15 if edge < -40 and p.get("view", "polar") == "polar" else 0.07)
        a0 = math.radians(215 if lon0 < 0 else 200)
        pts = [(gx + rx * math.cos(a0 + math.radians(t)), gy + ry * math.sin(a0 + math.radians(t))) for t in range(0, 300, 20)]
        o.append(_arrow_path(pen, pts, 2.4, MID, 9))
    if p.get("view", "polar") == "wide":
        for path in (((153, -20), (154, -28), (153, -34), (151, -39)),   # the East Australian Current, southward
                     ((112, -22), (111, -29), (113, -34), (120, -36)),   # the Leeuwin Current, south then east
                     ((35, -27), (32, -33), (25, -38)),                  # the Agulhas Current
                     ((-74, -40), (-73, -30), (-71, -20))):              # the Humboldt Current, northward
            o.append(_arrow_path(pen, [P(*q) for q in path], 2.2, MID, 8))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def _berg_under(pen, x, y, w, h, wl, left, right, depth):
    """The submerged mass of an iceberg: a larger, rounded, pale shape under the waterline with a dashed outline. Most of an
    iceberg is below the surface; the proportion shown here is schematic."""
    pts = [(left, wl), (left - w * 0.06, wl + (depth - wl) * 0.4), (left + w * 0.1, y + h * 0.9), (x + w * 0.5, y + h * depth / h),
           (right - w * 0.08, y + h * 0.9), (right + w * 0.06, wl + (depth - wl) * 0.4), (right, wl)]
    return pen.stroke(pts, 1.6, closed=True, fill=SOFT, color=MID, dash="5 4")


def _wl(pen, x0, x1, y, amp=2.0):
    """A wavy waterline."""
    n = 14
    return pen.stroke([(x0 + (x1 - x0) * i / n, y + amp * math.sin(i * 1.9) * (1 if i % 2 else 0.5)) for i in range(n + 1)], 2.2, color=INK)


def iceberg(pen, x, y, w, h, p, fs):
    """A tabular iceberg: a flat-topped block with weathered sides standing out of the water, and its much larger
    submerged part shown pale and dashed below the waterline."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.2, p, fs)
    wl = y + h * 0.42
    o = [_berg_under(pen, x, y, w, h, wl, x + w * 0.12, x + w * 0.88, h * 0.96)]
    top = [(x + w * 0.1, wl), (x + w * 0.11, y + h * 0.14), (x + w * 0.3, y + h * 0.1), (x + w * 0.52, y + h * 0.13), (x + w * 0.7, y + h * 0.1),
           (x + w * 0.74, y + h * 0.2), (x + w * 0.89, y + h * 0.2), (x + w * 0.9, wl)]
    o.append(pen.poly(top, 2.6, fill=PAPER, jit=0.3))
    for fx in (0.2, 0.36, 0.6, 0.78):  # weathering streaks down the face
        o.append(pen.line((x + w * fx, y + h * 0.17), (x + w * (fx + 0.02), wl - 3), 1.0, amp=0.3, color=MID))
    o.append(_wl(pen, x, x + w, wl))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def mixedlayer(pen, x, y, w, h, p, fs):
    """A section of the upper ocean: wind on the surface, a well-mixed surface layer with eddies, a thermocline of
    closely stacked lines where the water changes quickly with depth, and still, dense water below. `items` (up to three
    `label`s, top to bottom) name the layers at the right. Schematic: the depths mean nothing."""
    items = p.get("items", [])
    fsb = max(11.0, fs * 0.93)
    label_w = (max((len(it.get("label", "")) for it in items), default=0) * fsb * CHAR_W + 16) if items else 0
    x, y, w, h, lines, fsb2 = _under(x, y, w - label_w, h, 1.2, p, fs)
    s0, s1, s2 = y + h * 0.2, y + h * 0.5, y + h * 0.68
    o = []
    for k in range(3):  # wind arrows over the surface
        ax = x + w * (0.12 + 0.3 * k)
        o.append(pen.arrow((ax, y + h * 0.08), (ax + w * 0.2, y + h * 0.08), 2.0, head=7))
    o.append(pen.rect(x, s0, w, s1 - s0, 2.4, fill=PAPER, over=0.5))  # the mixed layer
    o.append(pen.rect(x, s1, w, s2 - s1, 2.4, fill=SOFT, over=0.5))  # the thermocline
    o.append(pen.rect(x, s2, w, y + h - s2, 2.4, fill=SOFT, over=0.5))  # the deep water
    o.append(pen.stroke([(x + w * i / 12, s0 + 2.2 * math.sin(i * 2.1)) for i in range(13)], 2.6))  # the rough surface
    for k in range(8):  # the thermocline: lines packed close together
        yy = s1 + (s2 - s1) * (k + 1) / 9
        o.append(pen.stroke([(x + 3, yy), (x + w * 0.5, yy + pen.n(0.8)), (x + w - 3, yy)], 1.0, color=INK if k % 2 else MID))
    for ex, ey in ((0.2, 0.3), (0.5, 0.38), (0.78, 0.3), (0.35, 0.44), (0.66, 0.45)):  # eddies stirring the mixed layer
        cx, cy, r = x + w * ex, y + h * ey, h * 0.045
        o.append(pen.stroke([(cx + r * math.cos(t), cy + r * math.sin(t) * 0.9) for t in [0.4 + k * 0.45 for k in range(11)]], 1.4, color=MID))
    for k in range(3):
        o.append(pen.line((x + w * (0.2 + 0.3 * k), y + h * 0.86), (x + w * (0.3 + 0.3 * k), y + h * 0.86), 1.2, amp=0.4, color=MID))  # still deep water
    line_h = fsb * 1.2
    last = -1e9
    for it, yy in zip(items[:3], (s0 + (s1 - s0) / 2, (s1 + s2) / 2, s2 + (y + h - s2) / 2)):
        if it.get("label"):
            ty = max(yy, last + line_h * 1.1)  # push a label down rather than let it run into the one above
            last = ty
            o.append(pen.line((x + w + 2, yy), (x + w + 10, ty), 1.2, amp=0.1, color=MID))
            o.append(text(x + w + 14, ty - fsb * 0.55, [it["label"]], fsb, lh=1.05))
    _caption(o, x, y, w, h, lines, fsb2)
    return "".join(o)


def seaice(pen, x, y, w, h, p, fs):
    """Sea ice seen from above, in one of four conditions chosen by `condition`: pancake (a mass of small round rimmed
    floes), pack (angular floes tightly packed with narrow leads), drift (a few floes with open water between) or fast (a
    continuous sheet held against the coast, cracked and ridged). White is ice, grey is water."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.5, p, fs)
    cond = p.get("condition", "pack")
    r = pen.r
    o = [pen.rect(x, y, w, h, 2.6, fill=SOFT, over=0.5)]

    def floe(cx, cy, rad, k=6, jit=0.3):
        """An angular floe: a rough polygon with straight edges."""
        pts = [(cx + rad * (1 + r.uniform(-jit, jit)) * math.cos(a), cy + rad * (1 + r.uniform(-jit, jit)) * 0.8 * math.sin(a)) for a in [math.tau * i / k + r.uniform(-0.2, 0.2) for i in range(k)]]
        return pen.poly(pts, 1.8, fill=PAPER, jit=0.1)

    if cond == "pancake":
        rad = w * 0.05
        for row in range(6):
            for col in range(10):
                cx = x + w * 0.06 + col * w * 0.095 + (w * 0.047 if row % 2 else 0) + r.uniform(-3, 3)
                cy = y + h * 0.1 + row * h * 0.16 + r.uniform(-3, 3)
                if x + rad < cx < x + w - rad:
                    rr = rad * r.uniform(0.75, 1.05)
                    o.append(pen.ellipse(cx, cy, rr, rr * 0.85, 1.8, fill=PAPER))
                    o.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rr * 0.68:.1f}" ry="{rr * 0.58:.1f}" fill="none" stroke="{MID}" stroke-width="1"/>')  # the raised rim
    elif cond == "drift":
        for fx, fy, rd in ((0.2, 0.3, 0.13), (0.55, 0.22, 0.09), (0.8, 0.5, 0.15), (0.38, 0.68, 0.11), (0.12, 0.78, 0.07), (0.62, 0.8, 0.08), (0.9, 0.18, 0.05)):
            o.append(floe(x + w * fx, y + h * fy, w * rd, k=7, jit=0.25))
    elif cond == "fast":
        edge = [(x + w * (0.28 + 0.07 * math.sin(i * 1.3) + r.uniform(-0.02, 0.02)), y + h * i / 10) for i in range(11)]
        o.append(pen.stroke(edge + [(x + w, y + h), (x + w, y)], 2.4, closed=True, fill=PAPER))
        for _ in range(3):  # cracks across the sheet
            sx, sy = x + w * r.uniform(0.4, 0.9), y + h * r.uniform(0.1, 0.9)
            o.append(pen.stroke([(sx, sy), (sx - w * 0.1, sy + h * r.uniform(0.05, 0.15)), (sx - w * 0.2, sy + h * r.uniform(0.0, 0.2))], 1.2, color=MID))
        for ry in (0.25, 0.6, 0.85):  # pressure ridges along the edge
            o.append(pen.stroke([(x + w * (0.4 + 0.04 * k), y + h * ry + (4 if k % 2 else -4)) for k in range(6)], 1.4, color=MID))
    else:  # pack
        for row in range(4):
            for col in range(6):
                cx = x + w * (0.1 + col * 0.16) + r.uniform(-4, 4)
                cy = y + h * (0.13 + row * 0.25) + r.uniform(-4, 4)
                o.append(floe(cx, cy, w * 0.075, k=5, jit=0.18))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def iceshelf(pen, x, y, w, h, p, fs):
    """An ice shelf in side view: a thick flat slab with a sheer cliff at its seaward edge, strata in the cliff, a crack and
    the floating shelf below the waterline, and a tabular iceberg that has broken off to the right."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.4, p, fs)
    wl = y + h * 0.5
    o = [pen.poly([(x, wl), (x + w * 0.6, wl), (x + w * 0.64, y + h * 0.86), (x, y + h * 0.9)], 1.6, fill=SOFT, jit=0.2)]  # the shelf below the water
    o.append(pen.poly([(x, wl), (x, y + h * 0.2), (x + w * 0.2, y + h * 0.17), (x + w * 0.4, y + h * 0.2), (x + w * 0.56, y + h * 0.17), (x + w * 0.58, wl)], 2.6, fill=PAPER, jit=0.25))
    for fy in (0.27, 0.34, 0.41):  # strata in the cliff
        o.append(pen.line((x + w * 0.4, y + h * fy), (x + w * 0.58, y + h * fy + 1), 1.0, amp=0.3, color=MID))
    o.append(pen.stroke([(x + w * 0.5, y + h * 0.18), (x + w * 0.52, y + h * 0.3), (x + w * 0.5, y + h * 0.42)], 1.4, color=INK))  # a crack
    berg = [(x + w * 0.68, wl), (x + w * 0.69, y + h * 0.33), (x + w * 0.88, y + h * 0.31), (x + w * 0.9, wl)]
    o.append(pen.stroke([(x + w * 0.68, wl), (x + w * 0.66, y + h * 0.7), (x + w * 0.78, y + h * 0.78), (x + w * 0.92, y + h * 0.68), (x + w * 0.9, wl)], 1.4, closed=True, fill=SOFT, color=MID, dash="5 4"))
    o.append(pen.poly(berg, 2.4, fill=PAPER, jit=0.25))
    o.append(_wl(pen, x, x + w, wl))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


# ---------------------------------------------------------------- polar field gear and a molecule
def stake(pen, x, y, w, h, p, fs):
    """A mass-balance (ablation) stake: a tall pole in banded segments set in the ice, with its tick marks and a flag, in a
    small melt hollow. Glaciologists read the surface height off it."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.45, p, fs)
    cx = x + w / 2
    ice = y + h * 0.8
    o = [pen.stroke([(x, ice + 2), (x + w * 0.3, ice - 3), (cx - w * 0.12, ice + 4), (cx + w * 0.12, ice + 4), (x + w * 0.7, ice - 2), (x + w, ice + 2)], 2.2),
         pen.stroke([(x + w * 0.1, ice + h * 0.05), (x + w * 0.5, ice + h * 0.12), (x + w * 0.9, ice + h * 0.05)], 1.2, color=MID)]
    top = y + h * 0.1
    o.append(pen.rect(cx - w * 0.07, top, w * 0.14, ice - top, 2.4, fill=PAPER, over=0.4))  # the pole
    n = 9
    for k in range(n):  # alternating bands, like a survey pole
        if k % 2:
            yy = top + (ice - top) * k / n
            o.append(pen.rect(cx - w * 0.07, yy, w * 0.14, (ice - top) / n, 1.2, fill=INK, over=0))
    for k in range(0, n + 1, 3):  # the ticks, reaching out to the side
        yy = top + (ice - top) * k / n
        o.append(pen.line((cx + w * 0.07, yy), (cx + w * 0.2, yy), 1.6, amp=0.05))
    o.append(pen.poly([(cx + w * 0.07, top), (cx + w * 0.34, top + h * 0.05), (cx + w * 0.07, top + h * 0.1)], 1.8, fill=SOFT, jit=0.1))  # the flag
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def emsled(pen, x, y, w, h, p, fs):
    """An ice-thickness sensor on a sled: a long low sled with its nose turned up, a long electromagnetic boom with a coil
    box at each end lying along it, a small GPS antenna on a pole, a tow rope, and arcs of signal going down into the ice."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.2, p, fs)
    ice = y + h * 0.58
    o = [pen.stroke([(x, ice + 3), (x + w * 0.3, ice - 2), (x + w * 0.6, ice + 3), (x + w, ice)], 2.2)]
    sled = [(x + w * 0.22, ice - h * 0.02), (x + w * 0.2, ice - h * 0.14), (x + w * 0.3, ice - h * 0.2), (x + w * 0.9, ice - h * 0.16), (x + w * 0.92, ice - h * 0.02)]
    o.append(pen.stroke(sled, 2.4, closed=True, fill=SOFT))
    o.append(pen.line((x + w * 0.05, y + h * 0.28), (x + w * 0.22, ice - h * 0.12), 1.6, amp=0.2, color=MID))  # the tow rope
    o.append(pen.rect(x + w * 0.3, ice - h * 0.31, w * 0.56, h * 0.07, 2.2, fill=PAPER, over=0.3))  # the boom along the sled
    for bx in (0.3, 0.8):  # a coil box at each end
        o.append(pen.rect(x + w * bx, ice - h * 0.37, w * 0.07, h * 0.19, 2.2, fill=INK, over=0.2))
    o.append(pen.line((x + w * 0.58, ice - h * 0.24), (x + w * 0.58, y + h * 0.08), 1.8, amp=0.1))  # the GPS antenna
    o.append(f'<circle cx="{x + w * 0.58:.1f}" cy="{y + h * 0.07:.1f}" r="{max(3.0, w * 0.014):.1f}" fill="{INK}"/>')
    for r in (0.05, 0.1, 0.15):  # the signal reaching into the ice
        cx0 = x + w * 0.57
        o.append(pen.stroke([(cx0 + w * r * math.cos(a), ice + 6 + h * 0.1 + w * r * 0.5 * math.sin(a)) for a in [math.radians(k) for k in range(20, 161, 20)]], 1.2, color=MID))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def fieldcamp(pen, x, y, w, h, p, fs):
    """A polar field camp: a ridge tent held down with guy lines, a loaded cargo sled beside it and a flag, on the ice."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.9, p, fs)
    ice = y + h * 0.84
    o = [pen.stroke([(x, ice), (x + w * 0.25, ice - 3), (x + w * 0.5, ice + 2), (x + w * 0.75, ice - 2), (x + w, ice)], 2.2)]
    tent = [(x + w * 0.08, ice), (x + w * 0.26, y + h * 0.2), (x + w * 0.52, ice)]
    o.append(pen.poly(tent, 2.6, fill=SOFT, jit=0.2))
    o.append(pen.poly([(x + w * 0.2, ice), (x + w * 0.26, y + h * 0.42), (x + w * 0.32, ice)], 1.8, fill=INK, jit=0.1))  # the door
    for gx in (x - w * 0.02, x + w * 0.62):  # guy lines
        o.append(pen.line((x + w * 0.26 if gx < x + w * 0.3 else x + w * 0.4, y + h * 0.3), (gx, ice), 1.0, amp=0.1, color=MID))
    sled = [(x + w * 0.6, ice), (x + w * 0.58, ice - h * 0.1), (x + w * 0.64, ice - h * 0.16), (x + w * 0.96, ice - h * 0.14), (x + w * 0.97, ice)]
    o.append(pen.stroke(sled, 2.2, closed=True, fill=PAPER))
    o.append(pen.rect(x + w * 0.66, ice - h * 0.32, w * 0.26, h * 0.16, 2.4, fill=SOFT, over=0.4))  # the load, strapped down
    o.append(pen.line((x + w * 0.73, ice - h * 0.32), (x + w * 0.73, ice - h * 0.14), 1.4, amp=0.05, color=INK))
    o.append(pen.line((x + w * 0.85, ice - h * 0.32), (x + w * 0.85, ice - h * 0.14), 1.4, amp=0.05, color=INK))
    o.append(pen.line((x + w * 0.5, y + h * 0.1), (x + w * 0.5, ice), 1.8, amp=0.1))  # the flag
    o.append(pen.poly([(x + w * 0.5, y + h * 0.1), (x + w * 0.62, y + h * 0.15), (x + w * 0.5, y + h * 0.21)], 1.6, fill=INK, jit=0.1))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def molecule(pen, x, y, w, h, p, fs):
    """A ball-and-stick molecule, generic: a six-ring with one double bond and a zigzag tail of four atoms (the look of a lipid or an
    organic compound). The atoms and bonds are decoration and say nothing about a particular compound."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.5, p, fs)
    r = min(w, h) * 0.085
    ccx, ccy, rr = x + w * 0.3, y + h * 0.5, h * 0.3
    ring = [(ccx + rr * math.cos(math.radians(30 + 60 * k)), ccy + rr * math.sin(math.radians(30 + 60 * k))) for k in range(6)]
    tail = [ring[0]]
    for k in range(1, 5):
        tail.append((tail[-1][0] + w * 0.12, tail[-1][1] + (h * 0.14 if k % 2 else -h * 0.14)))
    o = []
    for a, b in zip(ring, ring[1:] + ring[:1]):
        o.append(pen.line(a, b, 3.0, amp=0.1))
    mid = ((ring[1][0] + ring[2][0]) / 2, (ring[1][1] + ring[2][1]) / 2)  # the double bond: a second line inside one edge
    inner = lambda pt: (pt[0] + (ccx - pt[0]) * 0.16, pt[1] + (ccy - pt[1]) * 0.16)
    o.append(pen.line(inner(ring[1]), inner(ring[2]), 2.0, amp=0.05))
    for a, b in zip(tail, tail[1:]):
        o.append(pen.line(a, b, 3.0, amp=0.1))
    o.append(pen.line(ring[4], (ring[4][0], ring[4][1] + h * 0.14), 3.0, amp=0.1))  # a short side bond
    tones = [PAPER, SOFT, INK]
    for k, pt in enumerate(ring):
        o.append(f'<circle cx="{pt[0]:.1f}" cy="{pt[1]:.1f}" r="{r:.1f}" fill="{tones[k % 2]}" stroke="{INK}" stroke-width="2.4"/>')
    for k, pt in enumerate(tail[1:], 1):
        o.append(f'<circle cx="{pt[0]:.1f}" cy="{pt[1]:.1f}" r="{r * (0.85 if k < 4 else 1.15):.1f}" fill="{tones[(k + 1) % 3]}" stroke="{INK}" stroke-width="2.4"/>')
    sx, sy = ring[4][0], ring[4][1] + h * 0.14
    o.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{r * 0.8:.1f}" fill="{INK}" stroke="{INK}" stroke-width="2"/>')
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


_DRAW = {"stake": stake, "emsled": emsled, "fieldcamp": fieldcamp, "molecule": molecule, "iceberg": iceberg, "mixedlayer": mixedlayer, "seaice": seaice, "iceshelf": iceshelf, "map": map_, "currents": currents, "desk": desk, "phone": phone, "bowl": bowl, "bongo": bongo, "trawl": trawl, "rmt": rmt, "ctd": ctd, "satellite": satellite, "radar": radar, "radarscreen": radarscreen, "icecore": icecore, "massspec": massspec, "helicopter": helicopter, "drone": drone,
         "aquarium": aquarium, "freezer": freezer, "tag": tag, "scatter": scatter, "boxplot": boxplot, "modelgrid": modelgrid,
         "sequence": sequence, "tree": tree, "clusters": clusters, "network": network, "database": database, "filter": filter_rig, "tubes": tubes,
         "sequencer": sequencer, "cpr": cpr, "echosounder": echosounder, "venn": venn, "laptop": laptop, "microscope": microscope, "teapot": teapot, "net": net, "thermometer": thermometer, "axis": axis, "plot": plot, "pie": pie, "flow": flow, "steps": steps, "stack": stack, "ship": ship,
         "bottle": bottle, "jar": jar, "flash": flash, "cups": cups}


def extra_prop(pen, x, y, w, h, p, fs):
    return _DRAW[p["kind"]](pen, x, y, w, h, p, fs)
