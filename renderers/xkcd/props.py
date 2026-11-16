"""Props for charts, diagrams and objects, drawn in the xkcd style.

Each function takes a Pen, the box (x, y, w, h) in page units, the prop's spec and the font size,
and returns SVG. Positions inside a spec (`at`, `to`, `points`, `x`, `y`) are fractions 0 to 1 of
the prop's box (y runs up in `plot`, as on a chart).
"""
import math

from draw import CHAR_W, INK, MID, PAPER, SOFT, block_h, clamp, text, wrap

EXTRA = {"stake", "emsled", "fieldcamp", "molecule", "iceberg", "mixedlayer", "seaice", "iceshelf", "map", "currents", "desk", "phone", "bowl", "bongo", "trawl", "rmt", "ctd", "satellite", "radar", "radarscreen", "icecore", "massspec", "helicopter", "drone", "aquarium", "freezer", "tag", "scatter", "boxplot", "modelgrid", "sequence", "tree", "clusters", "network", "database", "filter", "tubes", "sequencer", "cpr", "echosounder", "venn", "axis", "plot", "pie", "flow", "steps", "stack", "ship", "bottle", "jar", "flash", "cups", "laptop", "microscope", "teapot", "net", "thermometer", "clay", "mosaic", "armchair", "wheelchair", "piano", "guitar", "easel", "camera", "brain", "headphones", "notes", "gallery", "cycle", "book", "headprofile", "cloud", "scales", "door", "heart", "trolley", "van", "skyline", "staff", "livingroom", "gears", "ear", "funnel", "stage", "blackbox", "circle", "bridge", "eye", "bookshelf", "spinalcord"}


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

    sw = clamp(fw / 110, 1.6, 2.6)
    amp = clamp(fw / 330, 0.5, 1.2)  # how far a hand-drawn edge wanders

    def P(pts, w, fill="none", jit=0.0):
        """A closed shape drawn as separate wobbly strokes that overshoot at the corners, the way a pen draws it by hand."""
        pts = [(a + pen.n(max(jit, 0.3)), b + pen.n(max(jit, 0.3))) for a, b in pts]
        out = []
        if fill != "none":
            out.append(f'<path d="M{" L".join(f"{a:.1f} {b:.1f}" for a, b in pts)}Z" fill="{fill}" stroke="none"/>')
        for i in range(len(pts)):
            (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % len(pts)]
            ln = math.hypot(x2 - x1, y2 - y1) or 1
            ux, uy = (x2 - x1) / ln, (y2 - y1) / ln
            e0, e1 = pen.r.uniform(-0.5, 1.6), pen.r.uniform(-0.5, 1.6)
            out.append(pen.line((x1 - ux * e0, y1 - uy * e0), (x2 + ux * e1, y2 + uy * e1), w, amp=amp))
        return "".join(out)

    def R(px0, py0, px1, py1, sw=2.0, fill=PAPER):
        (a, b), (c, d) = N(px0, py0), N(px1, py1)
        return pen.rect(a, b, c - a, d - b, sw, fill=fill, over=1.8)

    hull = [N(*q) for q in ((252, 588), (1745, 585), (1745, 690), (1700, 745), (1685, 795), (430, 795), (430, 745), (300, 715), (262, 690), (256, 640))]
    under = [N(*q) for q in ((262, 690), (1745, 690), (1700, 745), (1685, 795), (430, 795), (430, 745), (300, 715))]
    o = [P(hull, sw, fill=SOFT, jit=0.25), P(under, sw, fill=MID, jit=0.2)]
    o.append(P([N(*q) for q in ((360, 572), (440, 580), (450, 590), (362, 586))], sw * 0.8, fill=MID, jit=0.1))  # the raised bow edge
    o.append(pen.line(N(278, 585), N(278, 445), sw * 0.9, amp=0.2))  # the foremast
    # the long deckhouse, the funnel casing, and the bridge tower with its sloped front and wings
    o += [R(668, 522, 1385, 584, sw), R(1005, 462, 1150, 525, sw)]
    o.append(P([N(*q) for q in ((745, 525), (742, 484), (766, 470), (862, 470), (962, 490), (966, 525))], sw, fill=PAPER, jit=0.15))
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
    o.append(P([N(*q) for q in ((476, 498), (734, 494), (734, 514), (476, 512))], sw * 0.9, fill=PAPER, jit=0.1))
    o.append(P([N(*q) for q in ((482, 512), (606, 548), (690, 516))], sw * 0.8, fill="none", jit=0.1))
    # the aft crane: its pedestal, boom and a blue cover
    o.append(R(1330, 468, 1384, 524, sw))
    o.append(P([N(*q) for q in ((1214, 482), (1384, 462), (1384, 478), (1214, 496))], sw * 0.9, fill=PAPER, jit=0.1))
    o.append(R(1232, 494, 1352, 516, sw * 0.8, fill=SOFT))
    for a, b in ((932, 1010), (1030, 1126)):  # the two orange lifeboats, as pods under the bridge
        o.append(pen.stroke([N(a, 562), N(a + 6, 542), N(b - 10, 540), N(b, 556), N(b - 4, 566)], sw * 0.9, closed=True, fill=SOFT))
    for a, b in ((1145, 1250), (1262, 1365)):  # rescue-boat bays in the hull, each with a small boat
        o.append(R(a, 592, b, 638, sw * 0.9))
        if big:
            o.append(P([N(a + 12, 622), N(b - 12, 622), N(b - 22, 634), N(a + 22, 634)], 1.4, fill=SOFT, jit=0.1))
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
    """A continuous plankton recorder in side view, drawn after the real instrument (front on the left): a tow wire and weight, a nose
    cone with a small intake, a box holding two silk reels and the preservation tank, a gear box on top driven by a long shaft from a
    propeller behind, a tapering tail and a tail fin. Water and plankton run in at the nose and are trapped between two moving sheets of silk. A generic drawing, not to scale."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.3, p, fs)
    U = lambda u, v: (x + w * u, y + h * v)  # noqa: E731
    cy = 0.62
    sw = clamp(w / 90, 1.6, 2.6)
    o = []
    o.append(pen.poly([U(0.86, cy - 0.38), U(1.0, cy - 0.38), U(1.0, cy + 0.3), U(0.86, cy + 0.3)], sw, fill=MID, jit=0.3))  # the tail fin
    o.append(pen.poly([U(0.1, cy - 0.06), U(0.3, cy - 0.21), U(0.3, cy + 0.21), U(0.1, cy + 0.06)], sw, fill=SOFT, jit=0.25))  # the nose cone
    o.append(pen.poly([U(0.62, cy - 0.21), U(0.88, cy - 0.07), U(0.88, cy + 0.07), U(0.62, cy + 0.21)], sw, fill=SOFT, jit=0.25))  # the tail cone
    ax, ay = U(0.3, cy - 0.25)
    o.append(pen.rect(ax, ay, w * 0.32, h * 0.49, sw, fill=PAPER, over=1.2))  # the box with the silk and the tank
    for rx_, ry_, r_ in ((0.37, cy - 0.1, 0.055), (0.37, cy + 0.11, 0.055)):  # the two silk reels
        cx, cyy = U(rx_, ry_)
        o.append(pen.ellipse(cx, cyy, w * r_ * 0.6, h * r_ * 1.4, sw * 0.8, fill=SOFT))
    tx, ty = U(0.52, cy - 0.03)
    o.append(pen.ellipse(tx, ty, w * 0.06, h * 0.15, sw * 0.9, fill=SOFT))  # the preservation tank reel
    o.append(pen.stroke([U(0.4, cy - 0.12), U(0.46, cy - 0.17), U(0.52, cy - 0.17), U(0.58, cy - 0.06)], sw * 0.9, color=INK))  # cover silk
    o.append(pen.stroke([U(0.4, cy + 0.15), U(0.46, cy + 0.08), U(0.52, cy + 0.1), U(0.57, cy - 0.06)], sw * 0.9, color=MID))  # collecting silk
    gx, gy = U(0.42, cy - 0.37)
    o.append(pen.rect(gx, gy, w * 0.09, h * 0.12, sw * 0.9, fill=SOFT, over=0.8))  # the gear box
    o.append(pen.line(U(0.51, cy - 0.31), U(0.9, cy - 0.31), sw * 0.8, amp=0.3))  # the drive shaft
    o.append(pen.line(U(0.88, cy - 0.07), U(0.88, cy - 0.33), sw, amp=0.3))  # the propeller stand
    px, py = U(0.915, cy - 0.31)
    o.append(pen.ellipse(px, py, w * 0.014, h * 0.11, sw * 0.9, fill=PAPER))  # the propeller
    wx, wy = U(0.2, cy - 0.38)
    o.append(pen.line(U(0.05, 0.0), (wx, wy - h * 0.075), 1.8, amp=0.4, color=MID))  # the tow wire
    o.append(pen.ellipse(wx, wy, w * 0.022, h * 0.075, sw * 0.9, fill=SOFT))  # the weight on the tow wire
    o.append(pen.line((wx, wy + h * 0.075), U(0.24, cy - 0.25), sw * 0.8, amp=0.2))  # its hook to the body
    o.append(pen.arrow(U(0.0, cy), U(0.1, cy), 1.6, head=5))  # water and plankton in
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


def clay(pen, x, y, w, h, p, fs):
    """Clay on a board: a pinch pot with a thumb dent, a smooth ball, a rolled coil and a small slab with a tool mark. Making with clay."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.5, p, fs)
    U, sw = _u(x, y, w, h), 2.4
    base = 0.88
    o = [pen.line(U(0.0, base), U(1.0, base), 2.6, amp=0.4)]
    pot = [U(0.04, 0.38), U(0.06, 0.62), U(0.16, 0.82), U(0.3, 0.88), U(0.44, 0.82), U(0.52, 0.62), U(0.5, 0.38)]
    o.append(pen.stroke(pot, sw, closed=True, fill=SOFT))  # the pinch pot's body
    o.append(pen.ellipse(*U(0.27, 0.38), w * 0.24, h * 0.1, sw, fill=PAPER))  # its rim
    o.append(pen.ellipse(*U(0.27, 0.4), w * 0.15, h * 0.055, 1.4, fill=MID))  # the thumb dent inside
    o.append(pen.ellipse(*U(0.66, 0.72), w * 0.095, w * 0.095, sw, fill=SOFT))  # a ball
    o.append(f'<ellipse cx="{x + w * 0.63:.1f}" cy="{y + h * 0.68:.1f}" rx="{w * 0.02:.1f}" ry="{h * 0.03:.1f}" fill="{PAPER}"/>')
    coil = [U(0.8, 0.84), U(0.94, 0.84), U(0.98, 0.76), U(0.9, 0.7), U(0.82, 0.74), U(0.84, 0.8), U(0.9, 0.78)]
    o.append(pen.stroke(coil, sw * 1.6, color=INK))
    o.append(pen.stroke(coil, sw * 0.9, color=SOFT))  # a rolled coil
    slab = [U(0.56, 0.9), U(0.58, 0.86), U(0.78, 0.86), U(0.8, 0.9)]
    o.append(pen.poly(slab, 1.8, fill=PAPER, jit=0.2))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def mosaic(pen, x, y, w, h, p, fs):
    """A mosaic: a frame of irregular tiles with grout between them and a few places still empty, as a work in progress."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.2, p, fs)
    o = [pen.rect(x, y, w, h, 3.0, fill=PAPER, over=1)]
    cols, rows = 6, 5
    tw, th = (w - 14) / cols, (h - 14) / rows
    tones = [SOFT, PAPER, MID, SOFT, PAPER, SOFT]
    empty = {(1, 4), (2, 4), (4, 3), (5, 4), (3, 4)}
    for r in range(rows):
        for c in range(cols):
            if (r, c) in empty:
                continue
            tx, ty = x + 7 + c * tw + 1.5, y + 7 + r * th + 1.5
            wob = ((r * 7 + c * 3) % 5 - 2) * 0.04
            pts = [(tx + tw * (0.04 + wob), ty + th * 0.05), (tx + tw * 0.9, ty + th * (0.02 - wob)), (tx + tw * (0.92 + wob), ty + th * 0.9), (tx + tw * 0.06, ty + th * (0.92 - wob))]
            o.append(pen.poly(pts, 1.6, fill=tones[(r * 2 + c) % len(tones)], jit=0.15))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def _u(x, y, w, h):
    """A function from unit coordinates (0 to 1, y down) to the box, for props drawn from a plan."""
    return lambda u, v: (x + w * u, y + h * v)


def armchair(pen, x, y, w, h, p, fs):
    """An armchair seen from the front, drawn as a hand would: a rounded back, two plump arms, a seat cushion you can sit on and
    short legs. Care homes, waiting rooms, the listener. A figure with `pose: sit` rests on the top of the cushion (see the
    gallery for where to stand it)."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.05, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = [pen.stroke([U(0.15, 0.6), U(0.13, 0.28), U(0.17, 0.09), U(0.3, 0.03), U(0.5, 0.02), U(0.7, 0.03), U(0.83, 0.09), U(0.87, 0.28), U(0.85, 0.6)],
                    sw, closed=True, fill=SOFT)]  # the back
    for a, b in ((0.0, 0.17), (0.83, 1.0)):  # the arms: rounded rolls with a drop to the seat
        m = (a + b) / 2
        o.append(pen.stroke([U(a, 0.78), U(a - 0.01, 0.46), U(m, 0.36), U(b, 0.46), U(b + 0.01 * (1 if a else -1), 0.78)], sw, closed=True, fill=PAPER))
    o.append(pen.stroke([U(0.12, 0.7), U(0.16, 0.58), U(0.36, 0.52), U(0.64, 0.52), U(0.84, 0.58), U(0.88, 0.7), U(0.86, 0.8), U(0.5, 0.83), U(0.14, 0.8)],
                        sw, closed=True, fill=PAPER))  # the seat cushion: plump, its top at about half the chair's height
    o.append(pen.stroke([U(0.2, 0.63), U(0.5, 0.67), U(0.8, 0.63)], 1.3, color=MID))  # the front edge of the cushion
    for a in (0.06, 0.88):  # the legs
        o.append(pen.line(U(a + 0.03, 0.84), U(a + 0.04, 0.97), sw, amp=0.3))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def wheelchair(pen, x, y, w, h, p, fs):
    """A wheelchair in side view: a big wheel with a push rim, a small front wheel, a seat, a back with a push handle and a footrest."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.0, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = []
    cx, cy = U(0.4, 0.68)
    o.append(pen.ellipse(cx, cy, w * 0.3, h * 0.3, sw, fill="none"))  # the big wheel
    o.append(pen.ellipse(cx, cy, w * 0.24, h * 0.24, 1.2, fill="none"))  # its push rim
    o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{w * 0.025:.1f}" fill="{INK}"/>')
    for k in range(6):  # spokes
        a = math.pi * k / 3
        o.append(pen.line((cx - w * 0.24 * math.cos(a), cy - h * 0.24 * math.sin(a)), (cx + w * 0.24 * math.cos(a), cy + h * 0.24 * math.sin(a)), 1.0, amp=0.1, color=MID))
    fx, fy = U(0.86, 0.88)
    o.append(pen.ellipse(fx, fy, w * 0.07, h * 0.07, sw * 0.9, fill=SOFT))  # the small front wheel
    o.append(pen.stroke([U(0.18, 0.04), U(0.2, 0.42), U(0.74, 0.44)], sw, color=INK))  # the back and seat
    o.append(pen.poly([U(0.2, 0.4), U(0.74, 0.42), U(0.74, 0.5), U(0.2, 0.48)], sw * 0.8, fill=SOFT, jit=0.2))  # the seat cushion
    o.append(pen.line(U(0.18, 0.04), U(0.08, 0.04), sw, amp=0.2))  # the push handle
    o.append(pen.stroke([U(0.74, 0.46), U(0.84, 0.64), U(0.86, 0.84)], sw, color=INK))  # the leg support
    o.append(pen.line(U(0.86, 0.84), U(0.96, 0.84), sw, amp=0.2))  # the footrest
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def piano(pen, x, y, w, h, p, fs):
    """An upright piano from the front: a lid, a music stand, a row of white keys with black keys between and two legs."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.4, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = [pen.rect(*U(0.0, 0.02), w, h * 0.5, sw, fill=SOFT, over=1.5),  # the case
         pen.poly([U(0.08, 0.14), U(0.92, 0.14), U(0.9, 0.34), U(0.1, 0.34)], 1.6, fill=PAPER, jit=0.2)]  # the music stand
    kx0, kx1, ky0, ky1 = 0.04, 0.96, 0.52, 0.66
    o.append(pen.rect(*U(kx0, ky0), w * (kx1 - kx0), h * (ky1 - ky0), sw * 0.8, fill=PAPER, over=0.6))
    n = 14
    for i in range(1, n):
        o.append(pen.line(U(kx0 + (kx1 - kx0) * i / n, ky0), U(kx0 + (kx1 - kx0) * i / n, ky1), 1.0, amp=0.05, color=INK))
    for i in range(n):
        if i % 7 in (2, 6):
            continue  # no black key after E and B
        bx = U(kx0 + (kx1 - kx0) * (i + 0.68) / n, ky0)[0]
        o.append(f'<rect x="{bx:.1f}" y="{y + h * ky0:.1f}" width="{w * (kx1 - kx0) / n * 0.6:.1f}" height="{h * (ky1 - ky0) * 0.6:.1f}" fill="{INK}"/>')
    for a in (0.04, 0.9):
        o.append(pen.rect(*U(a, 0.66), w * 0.06, h * 0.32, sw * 0.8, fill=SOFT, over=0.8))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def guitar(pen, x, y, w, h, p, fs):
    """An acoustic guitar standing up: a figure-of-eight body with a sound hole and bridge, a long neck with frets and a headstock."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.4, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    body = [U(0.5, 0.48), U(0.74, 0.5), U(0.8, 0.58), U(0.68, 0.66), U(0.96, 0.78), U(0.9, 0.94), U(0.5, 0.99), U(0.1, 0.94), U(0.04, 0.78), U(0.32, 0.66), U(0.2, 0.58), U(0.26, 0.5)]
    o = [pen.rect(*U(0.42, 0.1), w * 0.16, h * 0.46, sw * 0.9, fill=SOFT, over=0.8),  # the neck
         pen.poly([U(0.4, 0.0), U(0.6, 0.0), U(0.62, 0.1), U(0.38, 0.1)], sw * 0.9, fill=INK, jit=0.15),  # the headstock
         pen.stroke(body, sw, closed=True, fill=PAPER)]
    cx, cy = U(0.5, 0.79)
    o.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{w * 0.14:.1f}" fill="{INK}"/>')  # the sound hole
    o.append(pen.rect(*U(0.36, 0.93), w * 0.28, h * 0.025, 1.6, fill=MID, over=0.4))  # the bridge
    for v in (0.2, 0.3, 0.4, 0.5):
        o.append(pen.line(U(0.42, v), U(0.58, v), 1.0, amp=0.05, color=INK))  # frets
    for u in (0.46, 0.5, 0.54):
        o.append(pen.line(U(u, 0.08), U(u, 0.93), 0.8, amp=0.05, color=MID))  # strings
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def easel(pen, x, y, w, h, p, fs):
    """An artist's easel: three legs, a canvas with a simple painting (hills and a sun) and a small tray under it."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.85, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = [pen.line(U(0.2, 0.02), U(0.02, 0.99), sw, amp=0.3), pen.line(U(0.8, 0.02), U(0.98, 0.99), sw, amp=0.3),
         pen.line(U(0.5, 0.1), U(0.5, 0.99), sw * 0.9, amp=0.3),
         pen.rect(*U(0.16, 0.08), w * 0.68, h * 0.6, sw, fill=PAPER, over=1.2),  # the canvas
         pen.stroke([U(0.18, 0.6), U(0.32, 0.4), U(0.46, 0.55), U(0.62, 0.34), U(0.82, 0.6)], 1.8, color=MID),  # the hills
         pen.rect(*U(0.08, 0.72), w * 0.84, h * 0.04, sw * 0.9, fill=SOFT, over=0.8)]  # the tray
    sx, sy = U(0.68, 0.22)
    o.append(pen.ellipse(sx, sy, w * 0.06, w * 0.06, 1.6, fill=SOFT))  # the sun
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def camera(pen, x, y, w, h, p, fs):
    """A camera from the front: a body with a top hump and shutter button, a big lens (rings and a glint), a flash and a viewfinder."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.4, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = [pen.poly([U(0.3, 0.22), U(0.36, 0.08), U(0.64, 0.08), U(0.7, 0.22)], sw, fill=SOFT, jit=0.2),
         pen.rect(*U(0.0, 0.22), w, h * 0.72, sw, fill=PAPER, over=1.5),
         pen.rect(*U(0.08, 0.3), w * 0.14, h * 0.12, 1.6, fill=SOFT, over=0.5),  # the flash
         pen.rect(*U(0.74, 0.3), w * 0.14, h * 0.1, 1.6, fill=SOFT, over=0.5),  # the viewfinder
         pen.rect(*U(0.78, 0.02), w * 0.1, h * 0.06, 1.8, fill=INK, over=0.3)]  # the shutter button
    cx, cy = U(0.5, 0.6)
    r = min(w * 0.2, h * 0.3)
    o += [pen.ellipse(cx, cy, r * 1.2, r * 1.2, sw, fill=SOFT), pen.ellipse(cx, cy, r * 0.85, r * 0.85, 1.8, fill=PAPER),
          pen.ellipse(cx, cy, r * 0.45, r * 0.45, 1.6, fill=INK),
          f'<circle cx="{cx - r * 0.2:.1f}" cy="{cy - r * 0.22:.1f}" r="{r * 0.14:.1f}" fill="{PAPER}"/>']
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


BRAIN_REGIONS = {  # lobes of the side-view brain (front at the left), as polygons that share the fissures and the outline, in the brain's own 0 to 1 box
    "frontal": [(0.08, 0.52), (0.09, 0.38), (0.16, 0.24), (0.28, 0.13), (0.44, 0.07), (0.52, 0.08), (0.5, 0.16), (0.46, 0.26), (0.44, 0.36), (0.42, 0.46),
                (0.34, 0.54), (0.27, 0.6), (0.16, 0.6), (0.1, 0.58)],
    "parietal": [(0.52, 0.08), (0.6, 0.07), (0.75, 0.12), (0.78, 0.14), (0.76, 0.24), (0.8, 0.36), (0.66, 0.4), (0.6, 0.44), (0.5, 0.5), (0.42, 0.46),
                 (0.44, 0.36), (0.46, 0.26), (0.5, 0.16)],
    "occipital": [(0.78, 0.14), (0.88, 0.22), (0.94, 0.36), (0.94, 0.48), (0.9, 0.57), (0.8, 0.6), (0.78, 0.5), (0.8, 0.36), (0.76, 0.24)],
    "temporal": [(0.27, 0.6), (0.38, 0.54), (0.5, 0.5), (0.6, 0.44), (0.66, 0.4), (0.8, 0.36), (0.78, 0.5), (0.8, 0.6), (0.7, 0.62), (0.62, 0.7), (0.52, 0.74),
                 (0.4, 0.72), (0.3, 0.66), (0.24, 0.62)],
}
BRAIN_LABELS = {"frontal": (0.27, 0.3), "parietal": (0.63, 0.22), "occipital": (0.87, 0.38), "temporal": (0.5, 0.63)}
BRAIN_TOP_FOLDS = (  # left hemisphere seen from above (front at the top); the right is the mirror image
    ((0.18, 0.2), (0.26, 0.15), (0.34, 0.2), (0.42, 0.13)), ((0.12, 0.34), (0.22, 0.28), (0.3, 0.34), (0.4, 0.27)), ((0.1, 0.5), (0.2, 0.44), (0.3, 0.5), (0.42, 0.42)),
    ((0.12, 0.64), (0.22, 0.58), (0.32, 0.64), (0.42, 0.57)), ((0.16, 0.78), (0.26, 0.72), (0.34, 0.78), (0.42, 0.7)), ((0.24, 0.88), (0.32, 0.84), (0.4, 0.88)),
)


def _top_brain(pen, x, y, w, h, p, fs, lines, fsb):
    """The brain from above: two hemispheres side by side with the fissure between them and the front at the top. `highlight: left` or `right` shades one
    hemisphere (drawn as the reader sees the page: the left hemisphere on the left)."""
    U, sw = _u(x, y, w, h), 2.6
    n = 28
    ring = [(0.5 + 0.4 * math.cos(math.tau * k / n) * (1 + 0.1 * math.sin(math.tau * k / n)), 0.5 + 0.46 * math.sin(math.tau * k / n)) for k in range(n)]  # k = 7 is the back, 21 the front
    o = [pen.stroke([U(*q) for q in ring], sw, closed=True, fill=PAPER)]
    name = p.get("highlight")
    if name in ("left", "right"):  # shade one hemisphere: the half of the outline on its side of the midline, with straight edges and no stroke of its own
        half = [ring[k] for k in range(7, 22)] if name == "left" else [ring[k % n] for k in range(21, 36)]
        o.append(pen.poly([U(*q) for q in half], 0, fill=MID, color="none"))
        o.append(pen.stroke([U(*q) for q in ring], sw, closed=True))
    o.append(pen.stroke([U(0.5, 0.05), U(0.495, 0.3), U(0.505, 0.5), U(0.495, 0.7), U(0.5, 0.95)], 2.6, color=INK))  # the fissure between the hemispheres
    ink = INK if p.get("highlight") in ("left", "right") else MID
    for fold in BRAIN_TOP_FOLDS:
        o.append(pen.stroke([U(*q) for q in fold], 1.6, color=ink))
        o.append(pen.stroke([U(1 - u, v) for u, v in fold], 1.6, color=ink))
    if p.get("labels"):
        for name, u in (("left", 0.27), ("right", 0.73)):
            o.append(text(x + w * u, y + h * 0.5 - fsb * 0.6, [name], fsb * 1.1, anchor="middle", halo=True))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def brain(pen, x, y, w, h, p, fs):
    """A brain in side view with the front at the left: the outline of the cerebrum with a frontal lobe, a temporal lobe hanging below the lateral fissure,
    parietal and occipital lobes, the central sulcus, a cerebellum with its fine ridges and the brain stem. For neuroscience, memory,
    language, ageing. `highlight` (frontal, parietal, temporal or occipital) shades that lobe; `labels: true` names the four lobes; `tracts: true` draws
    bundles of fibres between regions (white matter); `signal: true` draws one arrowed route from the back to the front, a signal passing along.
    `view: top` (or `highlight: left` or `right`) draws the brain from above instead, as two hemispheres, for a left against right comparison."""
    top_view = p.get("view") == "top" or p.get("highlight") in ("left", "right")
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.0 if top_view else 1.3, p, fs)
    if top_view:
        return _top_brain(pen, x, y, w, h, p, fs, lines, fsb)
    U, sw = _u(x, y, w, h), 2.6
    outline = [U(0.08, 0.52), U(0.09, 0.38), U(0.16, 0.24), U(0.28, 0.13), U(0.44, 0.07), U(0.6, 0.07), U(0.75, 0.12), U(0.88, 0.22), U(0.94, 0.36), U(0.94, 0.48), U(0.9, 0.57),
               U(0.8, 0.6), U(0.7, 0.62), U(0.62, 0.7), U(0.52, 0.74), U(0.4, 0.72), U(0.3, 0.66), U(0.24, 0.62), U(0.16, 0.6), U(0.1, 0.58)]
    o = [pen.stroke([U(0.5, 0.68), U(0.54, 0.88), U(0.58, 0.97), U(0.66, 0.96), U(0.66, 0.8), U(0.64, 0.66)], sw * 0.9, fill=SOFT),  # the brain stem
         pen.stroke([U(0.66, 0.64), U(0.78, 0.62), U(0.9, 0.64), U(0.9, 0.74), U(0.8, 0.82), U(0.68, 0.8), U(0.62, 0.72)], sw * 0.9, closed=True, fill=SOFT)]  # the cerebellum
    o += [pen.stroke([U(0.65 + 0.012 * k, 0.66 + 0.035 * k), U(0.78, 0.65 + 0.035 * k), U(0.89 - 0.01 * k, 0.67 + 0.035 * k)], 1.1, color=MID) for k in range(4)]  # its ridges
    o.append(pen.stroke(outline, sw, closed=True, fill=PAPER))
    region = BRAIN_REGIONS.get(p.get("highlight"))
    if region:
        o.append(pen.stroke([U(*q) for q in region], 1.6, closed=True, fill=MID))
    o.append(pen.stroke([U(0.27, 0.6), U(0.38, 0.54), U(0.5, 0.5), U(0.6, 0.44), U(0.66, 0.4)], 2.2, color=INK))  # the lateral fissure
    o.append(pen.stroke([U(0.52, 0.08), U(0.5, 0.16), U(0.46, 0.26), U(0.44, 0.36), U(0.42, 0.46)], 2.2, color=INK))  # the central sulcus
    if p.get("tracts"):  # three bundles of fibres, each a dotted line with a ring at both ends, so none can be mistaken for a fissure (which is one solid line)
        for path in (((0.16, 0.42), (0.3, 0.26), (0.58, 0.22), (0.78, 0.3), (0.84, 0.46)), ((0.3, 0.62), (0.46, 0.6), (0.64, 0.58), (0.82, 0.54)),
                     ((0.2, 0.42), (0.34, 0.3), (0.5, 0.32), (0.58, 0.44), (0.5, 0.58))):
            pts = [U(*q) for q in path]
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                n = max(1, int(math.hypot(bx - ax, by - ay) / 9))
                o += [_dot(ax + (bx - ax) * k / n, ay + (by - ay) * k / n, 2.3) for k in range(n)]
            for ex, ey in (pts[0], pts[-1]):
                o.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="5" fill="{PAPER}" stroke="{INK}" stroke-width="2.2"/>')
    if p.get("signal"):  # one route with an arrowhead: a signal passing from the back of the brain to the front
        route = [U(0.82, 0.46), U(0.66, 0.3), U(0.44, 0.26), U(0.24, 0.38)]
        o.append(pen.stroke(route, 3.0, color=INK))
        ang = math.atan2(route[-1][1] - route[-2][1], route[-1][0] - route[-2][0])
        o += [pen.line((route[-1][0] - 11 * math.cos(ang + s * 0.5), route[-1][1] - 11 * math.sin(ang + s * 0.5)), route[-1], 3.0, amp=0.2) for s in (-1, 1)]
        o.append(_dot(*route[0], 4.0))
    if p.get("labels"):
        for name, (u, v) in BRAIN_LABELS.items():
            o.append(text(x + w * u, y + h * v - fsb * 0.6, [name], fsb * 0.95, anchor="middle", halo=True))
        o.append(text(x + w * 0.78, y + h * 0.84, ["cerebellum"], fsb * 0.95, anchor="start", halo=True))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def headphones(pen, x, y, w, h, p, fs):
    """Headphones: a headband arc and two ear cups."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.0, p, fs)
    U, sw = _u(x, y, w, h), 2.8
    arc = [U(0.12, 0.62), U(0.12, 0.34), U(0.3, 0.08), U(0.5, 0.04), U(0.7, 0.08), U(0.88, 0.34), U(0.88, 0.62)]
    o = [pen.stroke(arc, sw + 1.6, color=INK), pen.stroke(arc, sw - 1.0, color=SOFT)]
    for u in (0.12, 0.88):
        cx, cy = U(u, 0.72)
        o.append(pen.ellipse(cx, cy, w * 0.13, h * 0.24, sw, fill=PAPER))
        o.append(pen.ellipse(cx, cy, w * 0.07, h * 0.14, 1.4, fill=SOFT))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def notes(pen, x, y, w, h, p, fs):
    """Music notes: a pair of eighth notes joined by a beam, and a single note."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.1, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = []
    for hx, hy, stem in ((0.18, 0.82, 0.18), (0.5, 0.74, 0.5)):  # the pair
        cx, cy = U(hx, hy)
        o.append(pen.ellipse(cx, cy, w * 0.1, h * 0.07, sw, fill=INK))
        o.append(pen.line(U(hx + 0.09, hy - 0.02), U(hx + 0.09, 0.1), sw, amp=0.2))
    o.append(pen.poly([U(0.27, 0.1), U(0.59, 0.04), U(0.59, 0.14), U(0.27, 0.2)], sw * 0.6, fill=INK, jit=0.1))  # the beam
    cx, cy = U(0.82, 0.88)
    o.append(pen.ellipse(cx, cy, w * 0.09, h * 0.065, sw, fill=INK))
    o.append(pen.line(U(0.9, 0.86), U(0.9, 0.38), sw, amp=0.2))
    o.append(pen.stroke([U(0.9, 0.38), U(0.97, 0.5), U(0.99, 0.62)], sw * 0.9, color=INK))  # the flag
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def _heart_pts(cx, cy, r):
    """Points round a heart centred near (cx, cy), about 2r wide, for a smooth closed stroke."""
    pts = []
    for k in range(24):
        t = math.tau * k / 24
        pts.append((cx + r * 16 * math.sin(t) ** 3 / 16, cy - r * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16))
    return pts


def heart(pen, x, y, w, h, p, fs):
    """A plain heart, to put between two things (a person and a painting) or on a cover."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.1, p, fs)
    cx, cy = x + w / 2, y + h * 0.5
    o = [pen.stroke(_heart_pts(cx, cy, min(w * 0.46, h * 0.5)), 2.8, closed=True, fill=SOFT)]
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def gallery(pen, x, y, w, h, p, fs):
    """A gallery room: a wall with framed pictures, a floor line and, if asked, a bench (`bench`), an access ramp at the right (`ramp`)
    and easels in front (`easels`, 1 to 3), and `empty: n` leaves the last n frames empty (dashed, with a question mark: the picture that is missing). `frames` (1 to 5, default 3) is how many pictures hang on the wall; each shows a different
    simple mark (a hill, a sun, a wave, a tree) so it reads as a painting. The place for a `shot: wide` opener."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.6, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    n = int(clamp(p.get("frames", 3), 1, 5))
    floor = 0.9
    o = [pen.line(U(0.0, floor), U(1.0, floor), sw, amp=0.6), pen.line(U(0.0, 0.8), U(1.0, 0.8), 1.2, amp=0.5, color=MID)]  # the floor, and the skirting board
    fw, fh = clamp(0.8 / n - 0.04, 0.12, 0.22), 0.42
    marks = ("hills", "sun", "wave", "tree", "hills")
    for i in range(n):
        u = 0.1 + (0.8 - fw) * (i / max(n - 1, 1)) if n > 1 else 0.5 - fw / 2
        v = 0.1 + 0.03 * ((i * 3) % 2)
        if i >= n - int(clamp(p.get("empty", 0), 0, n)):  # a frame with nothing in it: a dashed outline and a question mark, the picture that is missing
            fx, fy = U(u, v)
            o.append(pen.stroke([(fx, fy), (fx + w * fw, fy), (fx + w * fw, fy + h * fh), (fx, fy + h * fh)], 1.8, closed=True, color=MID, dash="6 5"))
            o.append(text(fx + w * fw / 2, fy + h * fh / 2 - fs * 0.6, ["?"], fs * 1.2, anchor="middle", fill=MID))
            continue
        o.append(pen.rect(*U(u, v), w * fw, h * fh, sw * 0.9, fill=PAPER, over=0.8))
        o.append(pen.rect(*U(u + fw * 0.12, v + fh * 0.14), w * fw * 0.76, h * fh * 0.72, 1.2, fill=SOFT, over=0.3))
        a, b, wd, ht = u + fw * 0.12, v + fh * 0.14, fw * 0.76, fh * 0.72
        k = marks[i]
        if k == "hills":
            o.append(pen.stroke([U(a, b + ht), U(a + wd * 0.3, b + ht * 0.45), U(a + wd * 0.55, b + ht * 0.8), U(a + wd * 0.78, b + ht * 0.35), U(a + wd, b + ht * 0.85)], 1.8, color=INK))
        elif k == "sun":
            o.append(pen.ellipse(*U(a + wd * 0.5, b + ht * 0.42), wd * w * 0.2, wd * w * 0.2, 1.8, fill=PAPER))
            o.append(pen.line(U(a, b + ht * 0.88), U(a + wd, b + ht * 0.88), 1.6, amp=0.3))
        elif k == "wave":
            o += [pen.stroke([U(a, b + ht * (0.4 + 0.22 * r)), U(a + wd * 0.25, b + ht * (0.3 + 0.22 * r)), U(a + wd * 0.5, b + ht * (0.4 + 0.22 * r)),
                              U(a + wd * 0.75, b + ht * (0.3 + 0.22 * r)), U(a + wd, b + ht * (0.4 + 0.22 * r))], 1.6, color=INK) for r in range(3)]
        else:
            o += [pen.line(U(a + wd * 0.5, b + ht * 0.95), U(a + wd * 0.5, b + ht * 0.5), 2.0, amp=0.2), pen.ellipse(*U(a + wd * 0.5, b + ht * 0.36), wd * w * 0.26, ht * h * 0.26, 1.8, fill=PAPER)]
    if p.get("ramp"):  # a ramp rising to the right, with a handrail
        o += [pen.poly([U(0.7, floor), U(1.0, floor), U(1.0, 0.8)], sw * 0.8, fill=SOFT, jit=0.2),
              pen.line(U(0.74, 0.72), U(1.0, 0.62), 1.8, amp=0.2), pen.line(U(0.76, 0.72), U(0.76, 0.88), 1.6, amp=0.1), pen.line(U(0.9, 0.66), U(0.9, 0.82), 1.6, amp=0.1)]
    if p.get("bench"):  # a bench in front of the wall
        bx = 0.3 if not p.get("ramp") else 0.2
        o += [pen.rect(*U(bx, 0.68), w * 0.3, h * 0.05, sw * 0.9, fill=PAPER, over=0.4),
              pen.line(U(bx + 0.03, 0.73), U(bx + 0.03, floor), sw * 0.9, amp=0.1), pen.line(U(bx + 0.27, 0.73), U(bx + 0.27, floor), sw * 0.9, amp=0.1)]
    for k in range(int(clamp(p.get("easels", 0), 0, 3))):  # easels with a blank board
        ex = 0.14 + 0.2 * k
        o += [pen.line(U(ex, 0.58), U(ex - 0.03, floor), 2.0, amp=0.2), pen.line(U(ex + 0.08, 0.58), U(ex + 0.11, floor), 2.0, amp=0.2),
              pen.rect(*U(ex - 0.01, 0.5), w * 0.1, h * 0.2, 2.2, fill=PAPER, over=0.5)]
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def cycle(pen, x, y, w, h, p, fs):
    """A ring of arrows through three to six stages, each a dot on the ring with its label outside it: a feedback loop, a life cycle,
    a cycle of learning."""
    items, fsb = p.get("items", [])[:6], max(11.0, fs * 0.93)
    n = max(len(items), 1)
    cx, cy = x + w / 2, y + h / 2
    lw = clamp(w * 0.3, 60, 140)  # the room a label may take beside the ring
    R = max(min(h / 2 - fsb * 1.6, w / 2 - lw - 6), 26)
    ang = lambda i: -math.pi / 2 + math.tau * i / n
    o = []
    for i in range(n if n > 1 else 0):
        a0, a1 = ang(i), ang(i + 1)
        gap = min(0.35, 0.25 * (a1 - a0))
        pts = [(cx + R * math.cos(a0 + gap + (a1 - a0 - 2 * gap) * t / 8), cy + R * math.sin(a0 + gap + (a1 - a0 - 2 * gap) * t / 8)) for t in range(9)]
        o.append(pen.stroke(pts, 2.4))
        tip, prev = pts[-1], pts[-2]
        d = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
        o += [pen.line((tip[0] - 10 * math.cos(d + k), tip[1] - 10 * math.sin(d + k)), tip, 2.4, amp=0.2) for k in (-0.5, 0.5)]
    for i, it in enumerate(items):
        a = ang(i)
        px, py = cx + R * math.cos(a), cy + R * math.sin(a)
        o.append(_dot(px, py, 5.5))
        lab = wrap(it.get("label", ""), lw, fsb)
        bh = block_h(lab, fsb, 1.05)
        c, sn = math.cos(a), math.sin(a)
        if c > 0.3:
            o.append(text(px + 12, py - bh / 2, lab, fsb, anchor="start", lh=1.05))
        elif c < -0.3:
            o.append(text(px - 12, py - bh / 2, lab, fsb, anchor="end", lh=1.05))
        else:
            o.append(text(px, py - 10 - bh if sn < 0 else py + 10, lab, fsb, anchor="middle", lh=1.05))
    return "".join(o)


def book(pen, x, y, w, h, p, fs):
    """A closed book from the front: a spine band, page edges at the right and foot, a title on the cover (`title`) and, if `heart` is true,
    a small heart under it. `blank: true` leaves the cover with a dashed head-and-shoulders silhouette instead of a title."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.78, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = [pen.rect(*U(0.08, 0.03), w * 0.9, h * 0.93, sw * 0.7, fill=SOFT, over=0.4),  # the page edges, behind
         pen.rect(*U(0.0, 0.0), w * 0.9, h * 0.93, sw, fill=PAPER, over=0.6),
         pen.rect(*U(0.0, 0.0), w * 0.12, h * 0.93, sw * 0.8, fill=SOFT, over=0.2)]  # the spine
    if p.get("blank"):  # no title: a dashed head-and-shoulders silhouette, the person or the evidence that is not on the cover
        cx, cy = x + w * 0.52, y + h * 0.4
        o.append(pen.stroke([(cx + w * 0.13 * math.cos(math.tau * k / 10), cy + w * 0.13 * math.sin(math.tau * k / 10)) for k in range(10)], 1.8, closed=True, color=MID, dash="5 4"))
        o.append(pen.stroke([(cx - w * 0.3, y + h * 0.85), (cx - w * 0.22, y + h * 0.6), (cx + w * 0.22, y + h * 0.6), (cx + w * 0.3, y + h * 0.85)], 1.8, color=MID, dash="5 4"))
        o.append(text(cx, cy - fsb * 0.65, ["?"], fsb * 1.2, anchor="middle", fill=MID))
    elif p.get("title"):
        tl = wrap(p["title"], w * 0.62, fsb)
        o.append(text(x + w * 0.52, y + h * 0.14, tl, fsb, anchor="middle", lh=1.1))
        o.append(pen.line(U(0.22, 0.14 + 0.02 + block_h(tl, fsb, 1.1) / h), U(0.8, 0.14 + 0.02 + block_h(tl, fsb, 1.1) / h), 1.4, amp=0.2, color=MID))
    if p.get("heart"):
        o.append(pen.stroke(_heart_pts(x + w * 0.52, y + h * 0.68, min(w, h) * 0.17), 2.2, closed=True, fill=SOFT))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def headprofile(pen, x, y, w, h, p, fs):
    """A head in profile, facing right, drawn as one wobbly outline: for memory, ageing, what a scan did or did not show. The inside is
    empty; `question: true` puts a question mark in it."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.85, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    pts = [U(0.5, 0.03), U(0.7, 0.07), U(0.82, 0.2), U(0.84, 0.36), U(0.88, 0.45), U(0.97, 0.56), U(0.88, 0.6), U(0.9, 0.66), U(0.85, 0.71), U(0.88, 0.78),
           U(0.78, 0.84), U(0.68, 0.87), U(0.68, 1.0), U(0.34, 1.0), U(0.36, 0.82), U(0.2, 0.7), U(0.1, 0.5), U(0.14, 0.24), U(0.28, 0.08)]
    o = [pen.stroke(pts, sw, closed=True, fill=PAPER)]
    ex, ey = U(0.72, 0.38)
    o.append(f'<circle cx="{ex:.1f}" cy="{ey:.1f}" r="{w * 0.022:.1f}" fill="{INK}"/>')
    if p.get("question"):
        o.append(text(*U(0.44, 0.26), ["?"], min(w, h) * 0.5, anchor="middle"))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def cloud(pen, x, y, w, h, p, fs):
    """A cloud of bumps: a fog, a weight, a thought. `faded: true` draws it dashed and grey, for something fading or half-remembered."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.6, p, fs)
    faded = bool(p.get("faded"))
    cx, cy, rx, ry = x + w / 2, y + h * 0.52, w * 0.4, h * 0.3
    n = 9
    pts = [(cx + rx * math.cos(math.tau * k / n + 0.2) + pen.n(1.0), cy + ry * math.sin(math.tau * k / n + 0.2) + pen.n(1.0)) for k in range(n)]
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for a, b in zip(pts, pts[1:] + pts[:1]):
        r = math.hypot(b[0] - a[0], b[1] - a[1]) * 0.62
        d += f"A{r:.1f} {r:.1f} 0 0 1 {b[0]:.1f} {b[1]:.1f}"
    stroke, fill, dash = (MID, "none", ' stroke-dasharray="7 6"') if faded else (INK, SOFT, "")
    o = [f'<path d="{d}Z" fill="{fill}" stroke="{stroke}" stroke-width="2.6" stroke-linejoin="round"{dash}/>']
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def scales(pen, x, y, w, h, p, fs):
    """A balance: a stand, a beam and two pans hung by strings. `tilt` is left or right for the heavier pan (the one that drops), or level.
    Up to two `items` label the pans, left then right."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.15, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    d = {"left": 0.07, "right": -0.07}.get(p.get("tilt", "level"), 0.0)  # positive: the left end drops
    top = 0.12
    ly, ry = top + d, top - d
    o = [pen.line(U(0.5, top), U(0.5, 0.9), sw, amp=0.3), pen.poly([U(0.34, 0.97), U(0.5, 0.88), U(0.66, 0.97)], sw * 0.8, fill=SOFT, jit=0.2),
         pen.line(U(0.12, ly), U(0.88, ry), sw, amp=0.3)]
    for u, vv, k in ((0.12, ly, 0), (0.88, ry, 1)):
        pan = vv + 0.36
        o += [pen.line(U(u, vv), U(u - 0.1, pan), 1.4, amp=0.1), pen.line(U(u, vv), U(u + 0.1, pan), 1.4, amp=0.1),
              pen.stroke([U(u - 0.13, pan), U(u - 0.1, pan + 0.05), U(u + 0.1, pan + 0.05), U(u + 0.13, pan)], sw * 0.9, color=INK)]
        items = p.get("items", [])
        if k < len(items) and items[k].get("label"):
            lab = wrap(items[k]["label"], w * 0.3, fsb)
            o.append(text(x + w * u, y + h * (pan + 0.09), lab, fsb, anchor="middle", lh=1.05))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def _padlock(pen, cx, cy, r):
    return (pen.stroke([(cx - r * 0.6, cy), (cx - r * 0.6, cy - r * 0.9), (cx, cy - r * 1.5), (cx + r * 0.6, cy - r * 0.9), (cx + r * 0.6, cy)], 2.2)
            + pen.rect(cx - r * 0.95, cy, r * 1.9, r * 1.4, 2.2, fill=INK, over=0.3))


def door(pen, x, y, w, h, p, fs):
    """A wall with a door in it: a barrier, an entrance. `locked: true` hangs a padlock on it; `open: true` swings it open."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.95, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = [pen.rect(*U(0.0, 0.04), w, h * 0.86, sw, fill=SOFT, over=0.6)]  # the wall, with a few courses of bricks
    for v in (0.2, 0.36, 0.52, 0.68, 0.82):
        o.append(pen.line(U(0.0, v), U(1.0, v), 1.0, amp=0.3, color=MID))
    o.append(pen.rect(*U(0.32, 0.22), w * 0.36, h * 0.68, sw, fill=PAPER, over=0.5))  # the doorway
    if p.get("open"):
        o.append(pen.poly([U(0.32, 0.22), U(0.2, 0.28), U(0.2, 0.86), U(0.32, 0.9)], sw * 0.9, fill=SOFT, jit=0.15))  # the door, swung back
        o.append(f'<circle cx="{x + w * 0.22:.1f}" cy="{y + h * 0.58:.1f}" r="{w * 0.014:.1f}" fill="{INK}"/>')
    else:
        o.append(pen.rect(*U(0.35, 0.25), w * 0.3, h * 0.62, 1.8, fill=SOFT, over=0.3))
        o.append(f'<circle cx="{x + w * 0.6:.1f}" cy="{y + h * 0.58:.1f}" r="{w * 0.018:.1f}" fill="{INK}"/>')  # the knob
        if p.get("locked"):
            o.append(_padlock(pen, x + w * 0.5, y + h * 0.46, w * 0.07))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def trolley(pen, x, y, w, h, p, fs):
    """A two-shelf trolley with a basket of objects on each shelf, a handle at one end and small wheels: an outreach trolley, a tea trolley."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.1, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = [pen.line(U(0.1, 0.9), U(0.1, 0.08), sw, amp=0.3), pen.line(U(0.82, 0.9), U(0.82, 0.08), sw, amp=0.3), pen.line(U(0.82, 0.08), U(0.97, 0.02), sw, amp=0.3),  # uprights and handle
         pen.line(U(0.06, 0.8), U(0.86, 0.8), sw, amp=0.3), pen.line(U(0.06, 0.45), U(0.86, 0.45), sw, amp=0.3)]  # the shelves
    for v in (0.8, 0.45):
        o.append(pen.stroke([U(0.18, v - 0.19), U(0.2, v), U(0.46, v), U(0.48, v - 0.19)], sw * 0.9, closed=True, fill=PAPER))  # a basket
        o.append(pen.line(U(0.19, v - 0.1), U(0.47, v - 0.1), 1.0, amp=0.2, color=MID))
        o += [pen.ellipse(*U(0.27, v - 0.22), w * 0.04, w * 0.04, 1.8, fill=SOFT), pen.rect(*U(0.36, v - 0.3), w * 0.05, h * 0.1, 1.8, fill=PAPER, over=0.2)]  # things in it
        o.append(pen.stroke([U(0.58, v - 0.14), U(0.6, v), U(0.78, v), U(0.8, v - 0.14)], sw * 0.8, closed=True, fill=SOFT))  # a second, smaller basket
    for u in (0.16, 0.76):
        o.append(pen.ellipse(*U(u, 0.94), w * 0.045, w * 0.045, sw * 0.9, fill=PAPER))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def van(pen, x, y, w, h, p, fs):
    """A small service van from the side with a pop-up table beside it and a few objects on the table: mobile outreach."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.8, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    body = [U(0.02, 0.84), U(0.02, 0.32), U(0.08, 0.26), U(0.46, 0.26), U(0.56, 0.4), U(0.64, 0.46), U(0.66, 0.84)]
    o = [pen.line(U(0.0, 0.9), U(1.0, 0.9), sw, amp=0.6),
         pen.stroke(body, sw, closed=True, fill=PAPER),
         pen.poly([U(0.5, 0.31), U(0.57, 0.43), U(0.5, 0.43)], 1.8, fill=SOFT, jit=0.1),  # the cab window
         pen.line(U(0.3, 0.3), U(0.3, 0.82), 1.4, amp=0.1), pen.rect(*U(0.08, 0.34), w * 0.16, h * 0.14, 1.6, fill=SOFT, over=0.2)]  # the sliding door and a side window
    for u in (0.16, 0.52):
        o.append(pen.ellipse(*U(u, 0.86), w * 0.05, w * 0.05, sw, fill=PAPER))
    o += [pen.line(U(0.72, 0.6), U(0.98, 0.6), sw, amp=0.3), pen.line(U(0.74, 0.6), U(0.72, 0.9), sw * 0.8, amp=0.1), pen.line(U(0.96, 0.6), U(0.98, 0.9), sw * 0.8, amp=0.1)]  # the table
    o += [pen.rect(*U(0.76, 0.5), w * 0.05, h * 0.1, 1.8, fill=SOFT, over=0.2), pen.ellipse(*U(0.86, 0.55), w * 0.025, w * 0.025, 1.8, fill=PAPER), pen.rect(*U(0.9, 0.51), w * 0.05, h * 0.09, 1.8, fill=PAPER, over=0.2)]
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def skyline(pen, x, y, w, h, p, fs):
    """A row of buildings of different heights on a ground line, with a few windows. `markers` (0 to 6) puts that many dots above them,
    for the towns or places a study covers."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.2, p, fs)
    U, sw = _u(x, y, w, h), 2.4
    heights = (0.45, 0.7, 0.35, 0.85, 0.55, 0.4, 0.65, 0.3)
    n = len(heights)
    bw = 0.92 / n
    o = [pen.line(U(0.0, 0.92), U(1.0, 0.92), sw, amp=0.6)]
    tops = []
    for i, ht in enumerate(heights):
        u = 0.04 + i * bw
        o.append(pen.rect(*U(u, 0.92 - ht * 0.8), w * bw * 0.92, h * ht * 0.8, sw, fill=PAPER if i % 2 else SOFT, over=0.5))
        for r in range(int(ht * 5)):
            o.append(pen.rect(*U(u + bw * 0.25, 0.92 - ht * 0.8 + 0.07 + r * 0.11), w * bw * 0.18, h * 0.05, 1.2, fill=PAPER, over=0.1))
        tops.append((u + bw * 0.46, 0.92 - ht * 0.8))
    m = int(clamp(p.get("markers", 0), 0, 6))
    for k in range(m):
        tu, tv = tops[int(k * (n - 1) / max(m - 1, 1))] if m > 1 else tops[3]
        o.append(pen.line(U(tu, tv - 0.02), U(tu, tv - 0.12), 1.6, amp=0.1))
        o.append(_dot(*U(tu, tv - 0.14), 4.5))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def staff(pen, x, y, w, h, p, fs):
    """A bar of music: five staff lines, a time signature, a few notes on stems and a double barline at the end. `pitches` (0 to 8,
    low to high: 0 is the bottom line, 1 the space above it, 8 the space above the top line) sets the notes; the default is a rising and
    falling run of four. `meter` (default "4/4") is the time signature."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.2, p, fs)
    U, sw = _u(x, y, w, h), 2.2
    pitches = [int(clamp(v, 0, 8)) for v in (p.get("pitches") or [2, 4, 5, 3])][:8] or [2]
    top, gap = 0.28, 0.11  # the top line and the distance between lines, as fractions of the height
    o = [pen.line(U(0.0, top + gap * k), U(1.0, top + gap * k), 1.6, amp=0.3) for k in range(5)]
    o.append(pen.line(U(0.0, top), U(0.0, top + gap * 4), sw, amp=0.1))
    o += [pen.line(U(0.94, top), U(0.94, top + gap * 4), sw, amp=0.1), pen.line(U(0.985, top), U(0.985, top + gap * 4), sw * 1.8, amp=0.1)]  # the double barline
    meter = str(p.get("meter", "4/4")).split("/")
    if len(meter) == 2:
        o.append(text(x + w * 0.1, y + h * (top - 0.03), [meter[0]], h * 0.3, anchor="middle", weight="bold"))
        o.append(text(x + w * 0.1, y + h * (top + gap * 2 - 0.03), [meter[1]], h * 0.3, anchor="middle", weight="bold"))
    n = len(pitches)
    for i, pt in enumerate(pitches):
        u = 0.24 + 0.64 * (i + 0.5) / n
        v = top + gap * 4 - pt * gap / 2
        cx, cy = U(u, v)
        rx, ry = w * 0.018, h * 0.058
        o.append(pen.ellipse(cx, cy, rx, ry, 1.8, fill=INK, jit=0.02))
        if pt < 4:  # a stem up on the right of low notes, down on the left of high ones
            o.append(pen.line((cx + rx * 0.95, cy), (cx + rx * 0.95, cy - h * 0.34), 2.0, amp=0.1))
        else:
            o.append(pen.line((cx - rx * 0.95, cy), (cx - rx * 0.95, cy + h * 0.34), 2.0, amp=0.1))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def livingroom(pen, x, y, w, h, p, fs):
    """A living room as a backdrop: a wall with a window (curtains drawn back, a sill), a floor line with a skirting board.
    `lamp: true` adds a standing lamp. A good place for an armchair, a piano, a guitar or a laptop; a figure stands on the floor line."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.6, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    floor = 0.88
    o = [pen.line(U(0.0, floor), U(1.0, floor), sw, amp=0.6), pen.line(U(0.0, 0.8), U(1.0, 0.8), 1.2, amp=0.5, color=MID)]  # the floor and the skirting board
    wx, wy, ww, wh = 0.12, 0.1, 0.3, 0.46
    o.append(pen.rect(*U(wx, wy), w * ww, h * wh, sw, fill=PAPER, over=0.8))  # the window
    o += [pen.line(U(wx + ww / 2, wy), U(wx + ww / 2, wy + wh), 1.6, amp=0.2), pen.line(U(wx, wy + wh / 2), U(wx + ww, wy + wh / 2), 1.6, amp=0.2)]  # the panes
    o.append(pen.rect(*U(wx - 0.02, wy + wh), w * (ww + 0.04), h * 0.03, 2.0, fill=SOFT, over=0.3))  # the sill
    for a, b in ((wx - 0.03, wx + 0.04), (wx + ww - 0.04, wx + ww + 0.03)):  # the curtains, drawn back
        o.append(pen.poly([U(a, wy - 0.03), U(b, wy - 0.03), U(b + 0.01, wy + wh), U(a - 0.01, wy + wh)], sw * 0.7, fill=SOFT, jit=0.2))
    o.append(pen.line(U(wx - 0.05, wy - 0.03), U(wx + ww + 0.05, wy - 0.03), 2.0, amp=0.2))  # the curtain rail
    o.append(pen.rect(*U(0.56, 0.16), w * 0.14, h * 0.26, 2.2, fill=PAPER, over=0.6))  # a small picture on the wall
    o.append(pen.stroke([U(0.575, 0.36), U(0.6, 0.27), U(0.625, 0.33), U(0.65, 0.24), U(0.685, 0.36)], 1.6, color=INK))
    if p.get("lamp"):  # a standing lamp on the right
        o += [pen.line(U(0.88, floor), U(0.88, 0.4), 2.2, amp=0.2), pen.line(U(0.84, floor), U(0.92, floor), 2.2, amp=0.2),
              pen.poly([U(0.83, 0.4), U(0.93, 0.4), U(0.9, 0.24), U(0.86, 0.24)], sw * 0.8, fill=SOFT, jit=0.15)]
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def _gear(pen, cx, cy, ro, n, phase, hub, tooth=0.16):
    """A gear of outer radius `ro` with `n` square teeth, the first centred on angle `phase`, and a round hub."""
    rr, step, pts = ro * (1 - tooth), math.tau / n, []
    for k in range(n):
        a = phase + k * step
        for ang, rad in ((a - step * 0.3, rr), (a - step * 0.17, ro), (a + step * 0.17, ro), (a + step * 0.3, rr)):
            pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return pen.poly(pts, 2.4, fill=SOFT, jit=0.2) + pen.ellipse(cx, cy, hub, hub, 2.0, fill=PAPER)


def gears(pen, x, y, w, h, p, fs):
    """Two gears meshing: parts of a system that turn each other. Up to two `items` label the big and the small gear."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.6, p, fs)
    r1, r2 = h * 0.46, h * 0.36
    n1, n2 = 12, 9
    c1 = (x + r1, y + h * 0.5)
    c2 = (c1[0] + r1 + r2 - h * 0.07, y + h * 0.5)  # the teeth overlap by about a tooth's height
    o = [_gear(pen, *c1, r1, n1, 0.0, r1 * 0.62), _gear(pen, *c2, r2, n2, math.pi + math.pi / n2, r2 * 0.62)]
    for (cx, cy), r, item in zip((c1, c2), (r1, r2), (p.get("items") or []) + [{}, {}]):
        if item.get("label"):
            lab = wrap(item["label"], r * 1.25, fsb * 1.25)
            o.append(text(cx, cy - block_h(lab, fsb * 1.25, 1.05) / 2 - fsb * 0.05, lab, fsb * 1.25, anchor="middle", lh=1.05))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def ear(pen, x, y, w, h, p, fs):
    """An ear in side view, with three arcs of sound reaching it from the left: hearing, noise, listening."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.2, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    outer = [U(0.56, 0.5), U(0.53, 0.28), U(0.62, 0.1), U(0.8, 0.04), U(0.94, 0.14), U(0.97, 0.38), U(0.9, 0.6), U(0.84, 0.78), U(0.74, 0.94), U(0.62, 0.94), U(0.56, 0.8), U(0.57, 0.64)]
    o = [pen.stroke(outer, sw, closed=True, fill=SOFT),
         pen.stroke([U(0.65, 0.47), U(0.67, 0.27), U(0.78, 0.17), U(0.87, 0.27), U(0.84, 0.44), U(0.77, 0.58), U(0.7, 0.62)], 1.8, color=INK)]  # the fold inside
    cx, cy = U(0.66, 0.54)
    o.append(pen.ellipse(cx, cy, w * 0.025, h * 0.045, 1.6, fill=INK))  # the opening of the ear canal
    ox, oy = U(0.6, 0.52)
    for r in (0.2, 0.34, 0.48):  # sound arriving: arcs centred on the ear, opening to the left
        pts = [(ox - r * h * math.cos(a), oy + r * h * math.sin(a)) for a in (-0.8, -0.4, 0.0, 0.4, 0.8)]
        o.append(pen.stroke(pts, 2.2, color=INK))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def funnel(pen, x, y, w, h, p, fs):
    """A funnel: many things go in at the top and fewer come out of the spout. `items` label the input (first) and the output (second)."""
    items = p.get("items") or []
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.0, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    u0 = 0.34 if items else 0.5  # the funnel's axis moves left to leave room for the labels
    bowl = [U(u0 - 0.26, 0.34), U(u0 + 0.26, 0.34), U(u0 + 0.06, 0.66), U(u0 + 0.06, 0.8), U(u0 - 0.06, 0.8), U(u0 - 0.06, 0.66)]
    o = [pen.poly(bowl, sw, fill=SOFT, jit=0.2), pen.line(U(u0 - 0.26, 0.34), U(u0 + 0.26, 0.34), sw, amp=0.3)]
    for a, b, r in ((-0.2, 0.06, 0.035), (-0.1, 0.14, 0.03), (0.02, 0.05, 0.04), (0.12, 0.15, 0.03), (0.2, 0.07, 0.035), (-0.04, 0.24, 0.03), (0.08, 0.26, 0.035), (-0.17, 0.25, 0.03)):  # the input: a crowd
        cx, cy = U(u0 + a, b)
        o.append(pen.ellipse(cx, cy, w * r * 0.8, h * r * 0.8, 1.8, fill=PAPER))
    for a, b in ((0.0, 0.9), (0.0, 0.97)):  # the output: one or two
        cx, cy = U(u0 + a, b)
        o.append(pen.ellipse(cx, cy, w * 0.03, h * 0.03, 1.8, fill=INK))
    for k, (v0, v1) in enumerate(((0.06, 0.26), (0.84, 0.98))):
        if k < len(items) and items[k].get("label"):
            lab = wrap(items[k]["label"], w * 0.32, fsb)
            o.append(text(x + w * 0.68, y + h * (v0 + v1) / 2 - block_h(lab, fsb, 1.05) / 2, lab, fsb, lh=1.05))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def theatre(pen, x, y, w, h, p, fs):
    """A stage seen from the front: curtains drawn back at both sides, a valance across the top and boards at the foot. `spotlight: true` darkens
    the back and lights a cone from a lamp above; `screen: true` hangs a screen at the back (for a projected shadow); `audience: true` puts a row of
    heads in the dark in front. Figures stand on the boards, at about y 0.8 of this prop's box (a little higher with an audience)."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.5, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    aud = bool(p.get("audience"))
    floor = 0.74 if aud else 0.84
    lit = bool(p.get("spotlight"))
    o = [pen.rect(*U(0.0, 0.0), w, h * floor, sw * 0.8, fill=MID if lit else PAPER, over=0.6)]  # the back of the stage
    if lit:  # the cone of light, and its lamp
        o += [pen.poly([U(0.45, 0.1), U(0.55, 0.1), U(0.74, floor), U(0.26, floor)], 1.6, fill=PAPER, jit=0.2),
              pen.rect(*U(0.45, 0.08), w * 0.1, h * 0.05, 2.0, fill=INK, over=0.3)]
    if p.get("screen"):
        o.append(pen.rect(*U(0.3, 0.16), w * 0.4, h * 0.4, 2.2, fill=PAPER, over=0.5))
        o.append(pen.line(U(0.5, 0.1), U(0.5, 0.16), 1.6, amp=0.1))
    o.append(pen.rect(*U(0.0, floor), w, h * 0.07, sw * 0.8, fill=SOFT, over=0.5))  # the boards
    for a, b in ((0.0, 0.2), (1.0, 0.8)):  # the curtains, drawn back to each side
        s = 1 if a == 0.0 else -1
        o.append(pen.poly([U(a, 0.0), U(b, 0.0), U(b - s * 0.05, floor * 0.55), U(a + s * 0.07, floor)], sw * 0.8, fill=SOFT, jit=0.2))
        o += [pen.line(U(a + s * f, 0.04), U(a + s * (f - 0.02), floor - 0.04), 1.2, amp=0.3, color=MID) for f in (0.05, 0.1, 0.15)]
    o.append(pen.poly([U(0.0, 0.0), U(1.0, 0.0), U(1.0, 0.1), U(0.84, 0.13), U(0.66, 0.1), U(0.5, 0.13), U(0.34, 0.1), U(0.16, 0.13), U(0.0, 0.1)], sw * 0.8, fill=SOFT, jit=0.2))  # the valance
    if aud:  # heads and shoulders against the foot of the stage
        for k in range(7):
            u = 0.08 + 0.14 * k + (0.04 if k % 2 else 0.0)
            cx, cy = U(u, 0.94 + 0.02 * (k % 2))
            o.append(pen.ellipse(cx, cy, w * 0.035, h * 0.06, 2.0, fill=INK))
            o.append(pen.stroke([(cx - w * 0.06, cy + h * 0.1), (cx - w * 0.04, cy + h * 0.045), (cx + w * 0.04, cy + h * 0.045), (cx + w * 0.06, cy + h * 0.1)], 2.0, fill=INK, color=INK))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def blackbox(pen, x, y, w, h, p, fs):
    """A black box with a question mark: an arrow goes in, an arrow comes out, and what happens inside is not known. `items` label the input
    (first) and the output (second); `dashed: true` draws the output as a dashed arrow, for an effect that has not been shown."""
    items = p.get("items") or []
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.6, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    qs = min(h * 0.62, w * 0.42)  # the question mark fills most of the box
    o = [pen.rect(*U(0.35, 0.18), w * 0.3, h * 0.64, sw, fill=INK, over=0.4),
         text(x + w * 0.5, y + h * 0.5 - qs * 0.6, ["?"], qs, anchor="middle", fill=PAPER)]
    o.append(pen.arrow(U(0.03, 0.5), U(0.33, 0.5), 2.4))
    if p.get("dashed"):
        o.append(pen.stroke([U(0.67, 0.5), U(0.97, 0.5)], 2.4, dash="7 6"))
        o += [pen.line(U(0.92, 0.42), U(0.97, 0.5), 2.4, amp=0.2), pen.line(U(0.92, 0.58), U(0.97, 0.5), 2.4, amp=0.2)]
    else:
        o.append(pen.arrow(U(0.67, 0.5), U(0.97, 0.5), 2.4))
    for k, (u0, u1) in enumerate(((0.0, 0.33), (0.67, 1.0))):
        if k < len(items) and items[k].get("label"):
            lab = wrap(items[k]["label"], w * (u1 - u0), fsb)
            o.append(text(x + w * (u0 + u1) / 2, y + h * 0.46 - block_h(lab, fsb, 1.05) - 4, lab, fsb, anchor="middle", lh=1.05))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def _chair(pen, cx, cy, s):
    """A small chair from the front: a back, a seat and two legs, `s` wide."""
    return (pen.rect(cx - s * 0.4, cy - s * 0.9, s * 0.8, s * 0.7, 1.8, fill=PAPER, over=0.2)  # the back
            + pen.rect(cx - s * 0.5, cy - s * 0.2, s, s * 0.14, 1.8, fill=SOFT, over=0.2)  # the seat
            + pen.line((cx - s * 0.42, cy - s * 0.06), (cx - s * 0.42, cy + s * 0.5), 1.8, amp=0.1)
            + pen.line((cx + s * 0.42, cy - s * 0.06), (cx + s * 0.42, cy + s * 0.5), 1.8, amp=0.1))


def circle(pen, x, y, w, h, p, fs):
    """Chairs round a centre, seen slightly from above: a group, a circle of people, a therapy session. `chairs` (3 to 8, default 6); `centre` is
    `fire`, `easel`, `person` or empty (just a rug). A figure can stand or sit in the middle of the ellipse."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.6, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    n = int(clamp(p.get("chairs", 6), 3, 8))
    cx, cy = U(0.5, 0.52)
    o = [pen.ellipse(cx, cy + h * 0.04, w * 0.3, h * 0.26, 1.4, fill=SOFT)]  # the rug
    s = min(w * 0.1, h * 0.2)
    spots = sorted(((cx + w * 0.4 * math.cos(math.tau * k / n + 0.4), cy + h * 0.32 * math.sin(math.tau * k / n + 0.4)) for k in range(n)), key=lambda q: q[1])
    for px, py in spots[: n // 2]:  # the far chairs first, so the near ones overlap them
        o.append(_chair(pen, px, py, s))
    c = p.get("centre")
    if c == "fire":
        o += [pen.line((cx - s * 0.5, cy + s * 0.25), (cx + s * 0.5, cy - s * 0.05), 3.0, amp=0.2), pen.line((cx + s * 0.5, cy + s * 0.25), (cx - s * 0.5, cy - s * 0.05), 3.0, amp=0.2),
              pen.stroke([(cx - s * 0.3, cy), (cx - s * 0.2, cy - s * 0.5), (cx, cy - s * 0.35), (cx + s * 0.05, cy - s * 0.9), (cx + s * 0.3, cy - s * 0.3), (cx + s * 0.25, cy)], 2.2, closed=True, fill=SOFT)]
    elif c == "easel":
        o += [pen.line((cx - s * 0.3, cy - s * 0.9), (cx - s * 0.5, cy + s * 0.3), 2.0, amp=0.2), pen.line((cx + s * 0.3, cy - s * 0.9), (cx + s * 0.5, cy + s * 0.3), 2.0, amp=0.2),
              pen.rect(cx - s * 0.4, cy - s * 0.8, s * 0.8, s * 0.6, 2.0, fill=PAPER, over=0.3)]
    elif c == "person":
        o += [pen.ellipse(cx, cy - s * 0.85, s * 0.2, s * 0.2, 2.0, fill=PAPER), pen.line((cx, cy - s * 0.65), (cx, cy - s * 0.05), 2.2, amp=0.2),
              pen.line((cx, cy - s * 0.05), (cx - s * 0.2, cy + s * 0.4), 2.2, amp=0.2), pen.line((cx, cy - s * 0.05), (cx + s * 0.2, cy + s * 0.4), 2.2, amp=0.2),
              pen.line((cx - s * 0.3, cy - s * 0.45), (cx + s * 0.3, cy - s * 0.45), 2.2, amp=0.2)]
    for px, py in spots[n // 2:]:
        o.append(_chair(pen, px, py, s))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def bridge(pen, x, y, w, h, p, fs):
    """A bridge across a gap between two blocks: two sides joined, or not. `items` label the two blocks (left, right); `broken: true` leaves a gap
    in the deck, for a link that is missing."""
    items = p.get("items") or []
    x, y, w, h, lines, fsb = _under(x, y, w, h, 2.0, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = [pen.rect(*U(0.0, 0.38), w * 0.27, h * 0.58, sw, fill=SOFT, over=0.5), pen.rect(*U(0.73, 0.38), w * 0.27, h * 0.58, sw, fill=SOFT, over=0.5)]
    o += [pen.stroke([U(0.29 + 0.04 * k, 0.93), U(0.31 + 0.04 * k, 0.9), U(0.33 + 0.04 * k, 0.93)], 1.2, color=MID) for k in range(0, 10, 2)]  # water in the gap
    if p.get("broken"):
        o += [pen.poly([U(0.27, 0.38), U(0.46, 0.38), U(0.44, 0.44), U(0.27, 0.44)], sw * 0.8, fill=PAPER, jit=0.15),
              pen.poly([U(0.54, 0.38), U(0.73, 0.38), U(0.73, 0.44), U(0.56, 0.44)], sw * 0.8, fill=PAPER, jit=0.15)]
        o += [pen.line(U(0.48, 0.5), U(0.47, 0.56), 1.6, amp=0.1), pen.line(U(0.52, 0.52), U(0.53, 0.6), 1.6, amp=0.1)]  # bits falling
    else:
        o.append(pen.rect(*U(0.27, 0.38), w * 0.46, h * 0.06, sw, fill=PAPER, over=0.3))  # a plain deck, joining the two blocks
    for k, u in enumerate((0.135, 0.865)):
        if k < len(items) and items[k].get("label"):
            lab = wrap(items[k]["label"], w * 0.24, fsb)
            o.append(text(x + w * u, y + h * 0.67 - block_h(lab, fsb, 1.05) / 2, lab, fsb, anchor="middle", lh=1.05))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def eye(pen, x, y, w, h, p, fs):
    """An eye: lids, iris and pupil with a glint. `lens: true` holds a lens off to the right with two dashed sight lines running through it to the eye (seeing
    through a lens, or a tinted view); `thought` (true, or a few words) adds a thought bubble above and to the right: what is seen, or what it makes someone think."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.5, p, fs)
    thought, lens = p.get("thought"), p.get("lens")
    top = h * 0.32 if thought else 0.0
    ew = w * 0.56 if lens else (w * 0.7 if thought else w)  # the eye keeps to the left when there is a lens or a bubble to make room for
    ex, ey, eh = x, y + top, h - top
    U, sw = _u(ex, ey, ew, eh), 2.6
    cx, cy = U(0.5, 0.5)
    r = eh * 0.3
    lid = [U(0.05, 0.5), U(0.25, 0.22), U(0.5, 0.14), U(0.75, 0.22), U(0.95, 0.5), U(0.75, 0.78), U(0.5, 0.86), U(0.25, 0.78)]
    o = [pen.stroke(lid, sw, closed=True, fill=PAPER), pen.ellipse(cx, cy, r, r, 2.2, fill=SOFT), pen.ellipse(cx, cy, r * 0.45, r * 0.45, 2.0, fill=INK),
         f'<circle cx="{cx + r * 0.22:.1f}" cy="{cy - r * 0.22:.1f}" r="{r * 0.14:.1f}" fill="{PAPER}"/>']
    o += [pen.line(U(u, 0.22 - 0.04 * abs(u - 0.5)), U(u + (u - 0.5) * 0.2, 0.08), 1.8, amp=0.1) for u in (0.2, 0.35, 0.5, 0.65, 0.8)]  # lashes
    if lens:  # a round lens held away from the eye, with the view running through it
        lx, ly, lr = x + w * 0.8, ey + eh * 0.5, eh * 0.36
        for sgn in (-1, 1):
            o.append(pen.stroke([(cx + r * 1.1, cy + sgn * r * 0.5), (lx - lr * 0.95, ly + sgn * lr * 0.6)], 1.4, color=MID, dash="5 5"))
        o.append(pen.ellipse(lx, ly, lr, lr, 3.2, fill=SOFT))
        o += [pen.line((lx - lr * 0.55 + k * lr * 0.4, ly + lr * 0.55), (lx + lr * 0.05 + k * lr * 0.4, ly - lr * 0.6), 1.2, amp=0.1, color=MID) for k in range(3)]
        o.append(pen.line((lx + lr * 0.7, ly + lr * 0.7), (lx + lr * 1.15, ly + lr * 1.2), 3.6, amp=0.2))
    if thought:
        bx, by = x + w * 0.78, y + h * 0.17
        o += [pen.ellipse(x + w * 0.6, y + h * 0.4, w * 0.015, h * 0.025, 1.6, fill=PAPER), pen.ellipse(x + w * 0.65, y + h * 0.33, w * 0.025, h * 0.04, 1.6, fill=PAPER),
              pen.ellipse(bx, by, w * 0.22, h * 0.17, 2.2, fill=PAPER)]
        if isinstance(thought, str):
            lab = wrap(thought, w * 0.38, fsb * 1.15)
            o.append(text(bx, by - block_h(lab, fsb * 1.15, 1.05) / 2, lab, fsb * 1.15, anchor="middle", lh=1.05))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def bookshelf(pen, x, y, w, h, p, fs):
    """A bookcase with two shelves of books. `gap: true` leaves a slot about two books wide empty on the upper shelf, drawn dashed with a question mark
    (the books that are not there)."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.4, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    o = [pen.rect(*U(0.0, 0.02), w, h * 0.96, sw, fill=PAPER, over=0.5), pen.line(U(0.0, 0.5), U(1.0, 0.5), sw, amp=0.3)]
    spec = ((0.05, 0.62), (0.04, 0.78), (0.06, 0.55), (0.05, 0.7), (0.07, 0.64), (0.04, 0.8), (0.06, 0.58), (0.05, 0.72), (0.06, 0.66), (0.04, 0.6), (0.07, 0.75), (0.05, 0.57))
    gap_at = 5
    gap_w = 0.11  # the empty slot is about two books wide, so the break in the pattern is hard to miss
    for row, base in enumerate((0.5, 0.98)):
        u = 0.05
        for i, (bw, bh) in enumerate(spec):
            if u + bw > 0.95:
                break
            if row == 0 and p.get("gap") and i == gap_at:
                gx, gy = U(u, base - 0.4)
                o.append(pen.stroke([(gx, gy), (gx + w * gap_w, gy), (gx + w * gap_w, gy + h * 0.4), (gx, gy + h * 0.4)], 1.6, closed=True, color=MID, dash="5 4"))
                qs = min(h * 0.3, w * 0.17)  # large enough to read from across a page
                o.append(text(gx + w * gap_w / 2, gy + h * 0.2 - qs * 0.6, ["?"], qs, anchor="middle", fill=MID))
                u += gap_w + 0.012 - bw - 0.012
            else:
                bx, by = U(u, base - 0.4 * bh / 0.8 - 0.01)
                o.append(pen.rect(bx, by, w * bw, h * 0.4 * bh / 0.8, 1.8, fill=SOFT if (i + row) % 2 else PAPER, over=0.2))
                o.append(pen.line((bx + w * bw / 2, by + 6), (bx + w * bw / 2, by + h * 0.4 * bh / 0.8 - 6), 1.0, amp=0.2, color=MID))
            u += bw + 0.012
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


def spinalcord(pen, x, y, w, h, p, fs):
    """A cross-section of the spinal cord: white matter round a grey butterfly of horns (two narrow at the back, two broad at the front), a central
    canal and a notch front and back; a schematic, not an anatomical plate. `laminae: true` draws dashed layers across one dorsal horn;
    `hemisection: true` darkens the right half, for a cut or damaged side."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 1.1, p, fs)
    U, sw = _u(x, y, w, h), 2.6
    outer = [U(0.5 + 0.42 * math.cos(math.tau * k / 16), 0.5 + 0.34 * math.sin(math.tau * k / 16)) for k in range(16)]
    left = [(0.5, 0.38), (0.41, 0.37), (0.35, 0.27), (0.31, 0.2), (0.28, 0.28), (0.3, 0.41), (0.21, 0.45), (0.16, 0.55), (0.2, 0.68), (0.29, 0.7), (0.35, 0.62), (0.45, 0.6), (0.5, 0.6)]
    butterfly = left[:-1] + [(1 - u, v) for u, v in reversed(left[1:])]
    o = [pen.stroke(outer, sw, closed=True, fill=PAPER)]
    if p.get("hemisection"):
        half = [U(0.5 + 0.42 * math.cos(a), 0.5 + 0.34 * math.sin(a)) for a in [-math.pi / 2 + math.pi * k / 8 for k in range(9)]]
        o.append(pen.stroke(half, sw, closed=True, fill=MID))
    o.append(pen.stroke([U(*q) for q in butterfly], 2.2, closed=True, fill=SOFT))
    if p.get("hemisection"):
        o.append(pen.stroke([U(*q) for q in [(1 - u, v) for u, v in left[:-1]] + [(0.5, 0.6)]], 2.2, closed=True, fill=INK))
    o += [pen.line(U(0.5, 0.16), U(0.5, 0.37), 1.8, amp=0.1), pen.line(U(0.5, 0.62), U(0.5, 0.84), 1.8, amp=0.1),
          pen.ellipse(*U(0.5, 0.49), w * 0.018, h * 0.025, 1.8, fill=PAPER)]
    if p.get("laminae"):
        for k in range(3):
            o.append(pen.stroke([U(0.265 + 0.01 * k, 0.24 + 0.05 * k), U(0.31, 0.215 + 0.05 * k), U(0.36, 0.25 + 0.05 * k)], 2.0, color=INK, dash="3 2"))
    _caption(o, x, y, w, h, lines, fsb)
    return "".join(o)


_DRAW = {"stake": stake, "emsled": emsled, "fieldcamp": fieldcamp, "molecule": molecule, "iceberg": iceberg, "mixedlayer": mixedlayer, "seaice": seaice, "iceshelf": iceshelf, "map": map_, "currents": currents, "desk": desk, "phone": phone, "bowl": bowl, "bongo": bongo, "trawl": trawl, "rmt": rmt, "ctd": ctd, "satellite": satellite, "radar": radar, "radarscreen": radarscreen, "icecore": icecore, "massspec": massspec, "helicopter": helicopter, "drone": drone,
         "aquarium": aquarium, "freezer": freezer, "tag": tag, "scatter": scatter, "boxplot": boxplot, "modelgrid": modelgrid,
         "sequence": sequence, "tree": tree, "clusters": clusters, "network": network, "database": database, "filter": filter_rig, "tubes": tubes,
         "sequencer": sequencer, "cpr": cpr, "echosounder": echosounder, "venn": venn, "laptop": laptop, "microscope": microscope, "teapot": teapot, "net": net, "thermometer": thermometer, "axis": axis, "plot": plot, "pie": pie, "flow": flow, "steps": steps, "stack": stack, "ship": ship,
         "bottle": bottle, "jar": jar, "flash": flash, "cups": cups, "clay": clay, "mosaic": mosaic, "armchair": armchair, "wheelchair": wheelchair, "piano": piano, "guitar": guitar, "easel": easel, "camera": camera, "brain": brain, "headphones": headphones, "notes": notes,
         "gallery": gallery, "cycle": cycle, "book": book, "headprofile": headprofile, "cloud": cloud, "scales": scales, "door": door, "heart": heart,
         "trolley": trolley, "van": van, "skyline": skyline, "staff": staff, "livingroom": livingroom, "gears": gears, "ear": ear, "funnel": funnel, "stage": theatre, "blackbox": blackbox, "circle": circle, "bridge": bridge, "eye": eye, "bookshelf": bookshelf, "spinalcord": spinalcord}


def extra_prop(pen, x, y, w, h, p, fs):
    return _DRAW[p["kind"]](pen, x, y, w, h, p, fs)
