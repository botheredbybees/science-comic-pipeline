"""Drawing primitives shared by the xkcd renderer: colours, a wobbly pen, and text helpers."""
import math
import random
from html import escape

INK, PAPER, SOFT, MID = "#17191e", "#ffffff", "#eceef2", "#8a909b"
FONT = '"Patrick Hand", "Comic Neue", "Comic Sans MS", cursive'
CHAR_W = 0.46  # average glyph width as a fraction of the font size, for wrapping


def esc(s):
    return escape(str(s), quote=False)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ---------------------------------------------------------------- drawing primitives
def smooth(pts, closed=False):
    """A smooth path through the points (Catmull-Rom converted to cubic curves)."""
    n = len(pts)
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    if n == 2 and not closed:
        return d + f"L{pts[1][0]:.1f} {pts[1][1]:.1f}"
    ext = (pts[-1:] + pts + pts[:2]) if closed else ([pts[0]] + pts + [pts[-1]])
    for i in range(n if closed else n - 1):
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f"C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d + ("Z" if closed else "")


class Pen:
    """Draws wobbly strokes. One Pen per panel, seeded from the panel id."""

    def __init__(self, seed):
        self.r = random.Random(seed)

    def n(self, a):
        return self.r.gauss(0, a)

    def stroke(self, pts, w=2.4, closed=False, fill="none", color=INK, dash=None):
        extra = f' stroke-dasharray="{dash}"' if dash else ""
        return (f'<path d="{smooth(pts, closed)}" fill="{fill}" stroke="{color}" stroke-width="{w:.1f}" '
                f'stroke-linecap="round" stroke-linejoin="round"{extra}/>')

    def line(self, a, b, w=2.4, amp=0.9, **kw):
        (x1, y1), (x2, y2) = a, b
        length = math.hypot(x2 - x1, y2 - y1) or 1
        px, py = -(y2 - y1) / length, (x2 - x1) / length
        steps = max(2, round(length / 22))
        pts = []
        for i in range(steps + 1):
            t = i / steps
            off = self.n(amp * 0.5 if i in (0, steps) else amp)
            pts.append((x1 + (x2 - x1) * t + px * off, y1 + (y2 - y1) * t + py * off))
        return self.stroke(pts, w, **kw)

    def rect(self, x, y, w, h, sw=2.4, fill="none", over=3):
        out = []
        if fill != "none":
            jit = [(x + self.n(0.8), y + self.n(0.8)), (x + w + self.n(0.8), y + self.n(0.8)),
                   (x + w + self.n(0.8), y + h + self.n(0.8)), (x + self.n(0.8), y + h + self.n(0.8))]
            out.append(f'<path d="M{" L".join(f"{a:.1f} {b:.1f}" for a, b in jit)}Z" fill="{fill}" stroke="none"/>')
        o = lambda: self.r.uniform(0, over)  # noqa: E731
        out += [self.line((x - o(), y), (x + w + o(), y), sw), self.line((x + w, y - o()), (x + w, y + h + o()), sw),
                self.line((x + w + o(), y + h), (x - o(), y + h), sw), self.line((x, y + h + o()), (x, y - o()), sw)]
        return "".join(out)

    def ellipse(self, cx, cy, rx, ry, sw=2.4, fill="none"):
        k = 12
        a0 = self.r.uniform(0, math.tau)
        pts = [(cx + rx * (1 + self.n(0.03)) * math.cos(a0 + math.tau * i / k),
                cy + ry * (1 + self.n(0.03)) * math.sin(a0 + math.tau * i / k)) for i in range(k)]
        return self.stroke(pts, sw, closed=True, fill=fill)

    def arrow(self, a, b, w=2.4, head=9):
        ang = math.atan2(b[1] - a[1], b[0] - a[0])
        tips = [(b[0] - head * math.cos(ang + s * 0.5), b[1] - head * math.sin(ang + s * 0.5)) for s in (-1, 1)]
        return self.line(a, b, w) + self.line(tips[0], b, w, amp=0.3) + self.line(tips[1], b, w, amp=0.3)


# ---------------------------------------------------------------- text
def wrap(text, width, fs):
    per = max(4, int(width / (fs * CHAR_W)))
    lines, cur = [], ""
    for word in str(text).split():
        if cur and len(cur) + 1 + len(word) > per:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + ([cur] if cur else [])


def text(x, y, lines, fs, anchor="start", fill=INK, lh=1.2, weight="normal", halo=False):
    """SVG text with one tspan per line; y is the top of the block."""
    if not lines:
        return ""
    spans = "".join(f'<tspan x="{x:.1f}" dy="{(fs if i == 0 else fs * lh):.1f}">{esc(t)}</tspan>' for i, t in enumerate(lines))
    glow = f' stroke="{PAPER}" stroke-width="5" stroke-linejoin="round" paint-order="stroke"' if halo else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{fs:.1f}" text-anchor="{anchor}" fill="{fill}" '
            f'font-weight="{weight}"{glow}>{spans}</text>')


def block_h(lines, fs, lh=1.2):
    return len(lines) * fs * lh


