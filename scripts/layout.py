"""Pack panels into rows, the way a printed comic reads: left to right, then down.

A row is ROW_UNITS wide. Every row is filled exactly, so there are never blanks. A panel's
weight is a preferred width; the packer looks ahead over the whole sequence and chooses the
row breaks and widths that keep every panel as close to its preference as possible, the way a
typesetter breaks paragraphs into lines. Panels keep their order.

Limits, both adjustable:
  max_per_row  panels in one row (3 reads comfortably on A4 portrait; 4 suits a wider page)
  min_units    narrowest allowed panel (4 of 12 is a third of the row)
A 'full' panel always has a row to itself. A row that repeats the widths of the row before it is penalised,
so a page reads as a varied layout and not a grid.
"""
from functools import lru_cache

ROW_UNITS = 12
PREFERRED = {"small": 4, "standard": 6, "wide": 8, "full": 12}  # a third, a half, two thirds, all


def units(panel):
    """The panel's preferred width in twelfths of a row."""
    return PREFERRED[panel.get("weight", "standard")]


@lru_cache(maxsize=None)
def _compositions(total, parts, min_units):
    """All ways to split `total` into `parts` integers, each at least `min_units`."""
    if parts == 1:
        return [(total,)] if total >= min_units else []
    out = []
    for first in range(min_units, total - min_units * (parts - 1) + 1):
        out += [(first,) + rest for rest in _compositions(total - first, parts - 1, min_units)]
    return out


def _row_options(prefs, row_units, min_units):
    """Every allowed way to give these panels widths, as (deviation cost, widths)."""
    if len(prefs) > 1 and row_units in prefs:  # a full-width panel stays alone
        return []
    return [(sum((w - p) ** 2 for w, p in zip(widths, prefs)), widths)
            for widths in _compositions(row_units, len(prefs), min_units)]


REPEAT_SAME, REPEAT_NEAR = 12, 2  # penalties for a row that matches, or nearly matches, the row before it


def _repeat_cost(prev, widths, same=None, near=None):
    """A penalty for a row that looks like the row before it, so the page does not become a grid."""
    same = REPEAT_SAME if same is None else same
    near = REPEAT_NEAR if near is None else near
    if prev is None or len(prev) != len(widths):
        return 0
    if prev == widths:
        return same
    return near if all(abs(a - b) <= 1 for a, b in zip(prev, widths)) else 0


def pack_rows(panels, max_per_row=3, row_units=ROW_UNITS, min_units=4, prev=None):
    """Return rows in reading order; each row is a list of (panel, assigned_units) summing to row_units.

    `prev` is the widths of the row just before the first one (for a beat that follows another), so a
    row is nudged away from repeating its neighbour's widths."""
    n = len(panels)
    prefs = [min(units(p), row_units) for p in panels]
    # best[i][last_widths] = (cost, [(panel_count, widths), ...]) for the first i panels
    best = [dict() for _ in range(n + 1)]
    best[0][prev] = (0, [])
    for i in range(1, n + 1):
        for k in range(1, min(max_per_row, i) + 1):
            options = _row_options(tuple(prefs[i - k:i]), row_units, min_units)
            for last, (base, hist) in best[i - k].items():
                for cost, widths in options:
                    total = base + cost + _repeat_cost(last, widths)
                    cur = best[i].get(widths)
                    if cur is None or total < cur[0]:
                        best[i][widths] = (total, hist + [(k, widths)])
    rows, at = [], 0
    for k, widths in min(best[n].values(), key=lambda v: v[0])[1]:
        rows.append(list(zip(panels[at:at + k], widths)))
        at += k
    return rows
