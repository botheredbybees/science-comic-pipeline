"""Props for charts, diagrams and objects, drawn in the xkcd style.

Each function takes a Pen, the box (x, y, w, h) in page units, the prop's spec and the font size,
and returns SVG. Positions inside a spec (`at`, `to`, `points`, `x`, `y`) are fractions 0 to 1 of
the prop's box (y runs up in `plot`, as on a chart).
"""
import math

from draw import CHAR_W, INK, MID, PAPER, SOFT, block_h, clamp, text, wrap

EXTRA = {"sequence", "tree", "clusters", "network", "database", "filter", "tubes", "sequencer", "cpr", "echosounder", "venn", "axis", "plot", "pie", "flow", "steps", "stack", "ship", "bottle", "jar", "flash", "cups", "laptop", "microscope", "teapot", "net", "thermometer"}


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
    hull = [(x, y + h * 0.55), (x + w, y + h * 0.55), (x + w * 0.9, y + h * 0.82), (x + w * 0.08, y + h * 0.82)]
    o = [pen.stroke(hull, 2.4, closed=True, fill=PAPER)]
    o.append(pen.rect(x + w * 0.25, y + h * 0.3, w * 0.4, h * 0.25, 2.2, fill=PAPER, over=1))
    o.append(pen.rect(x + w * 0.62, y + h * 0.12, w * 0.12, h * 0.43, 2.2, fill=PAPER, over=1))
    o += [pen.rect(x + w * (0.3 + 0.1 * i), y + h * 0.36, w * 0.05, h * 0.08, 1.4, over=0) for i in range(3)]
    for i in range(4):
        wx = x + w * (0.02 + 0.26 * i)
        o.append(pen.stroke([(wx, y + h * 0.9), (wx + w * 0.07, y + h * 0.84), (wx + w * 0.14, y + h * 0.9), (wx + w * 0.21, y + h * 0.84)], 1.8))
    if p.get("label"):
        o.append(text(x + w / 2, y + h * 0.95, [p["label"]], max(11.0, fs * 0.93), anchor="middle"))
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


def cups(pen, x, y, w, h, p, fs):
    """A row of cups, each filled to its `value` (0 to 1)."""
    items = p.get("items", [])
    n = max(len(items), 1)
    cw = min(w / n * 0.7, h * 0.8)
    gap = (w - cw * n) / (n + 1)
    o = []
    for i, it in enumerate(items):
        cx = x + gap + i * (cw + gap)
        o.append(pen.stroke([(cx, y), (cx + cw * 0.12, y + h), (cx + cw * 0.88, y + h), (cx + cw, y)], 2.2, fill=PAPER))
        lvl = clamp(it.get("value", 0), 0, 1)
        if lvl:
            ty = y + h * (1 - lvl)
            o.append(pen.stroke([(cx + cw * 0.12 * (1 - lvl) + 2, ty), (cx + cw * 0.12 + 1, y + h - 2), (cx + cw * 0.88 - 1, y + h - 2), (cx + cw - cw * 0.12 * (1 - lvl) - 2, ty)], 1.6, closed=True, fill=INK))
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
    """A plankton net: a ring on a line, a long cone of mesh and a collecting bottle at the end."""
    x, y, w, h = _fit(x, y, w, h, 0.5)
    rx, ry = x + w * 0.5, y + h * 0.18
    o = [pen.line((rx, ry), (rx, y), 2.4, amp=0.2),
         pen.ellipse(rx, ry, w * 0.36, h * 0.07, 2.4, jit=0.01)]
    o += [pen.line((rx + dx * w * 0.36, ry), (rx + dx * w * 0.06, y + h * 0.85), 1.6, amp=0.3) for dx in (-1, -0.5, 0, 0.5, 1)]
    o += [pen.rect(rx - w * 0.07, y + h * 0.85, w * 0.14, h * 0.15, 2.2, fill=PAPER, over=0)]
    if p.get("label"):
        o.append(text(rx, y + h + 4, [p["label"]], max(11.0, fs * 0.93), anchor="middle"))
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
    """A database: three stacked discs, the standard picture of a store of records (a reference library)."""
    x, y, w, h, lines, fsb = _under(x, y, w, h, 0.9, p, fs)
    o = []
    ry, hh = h * 0.1, h * 0.27
    for i, top in enumerate((h * 0.62, h * 0.32, h * 0.02)):  # bottom disc first, so each one overlaps the one below
        t, b = y + top + ry, y + top + hh
        belly = [(x + w / 2 + (w / 2) * math.cos(a), b + ry * math.sin(a)) for a in [math.pi * k / 10 for k in range(11)]]  # the front half of the bottom edge
        o.append(pen.stroke([(x, t)] + belly[::-1] + [(x + w, t)], 2.4, closed=True, fill=SOFT if i % 2 == 0 else PAPER))
        o.append(pen.ellipse(x + w / 2, t, w / 2, ry, 2.4, fill=PAPER))
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


_DRAW = {"sequence": sequence, "tree": tree, "clusters": clusters, "network": network, "database": database, "filter": filter_rig, "tubes": tubes,
         "sequencer": sequencer, "cpr": cpr, "echosounder": echosounder, "venn": venn, "laptop": laptop, "microscope": microscope, "teapot": teapot, "net": net, "thermometer": thermometer, "axis": axis, "plot": plot, "pie": pie, "flow": flow, "steps": steps, "stack": stack, "ship": ship,
         "bottle": bottle, "jar": jar, "flash": flash, "cups": cups}


def extra_prop(pen, x, y, w, h, p, fs):
    return _DRAW[p["kind"]](pen, x, y, w, h, p, fs)
