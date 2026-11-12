"""Pack panels into rows, the way a printed comic reads: left to right, then down.

A row is ROW_UNITS wide. Every row is filled exactly, so there are never blanks. A panel's
weight is a preferred width; the packer looks ahead over the whole sequence and chooses the
row breaks and widths that keep every panel as close to its preference as possible, the way a
typesetter breaks paragraphs into lines. Panels keep their order.

Limits, both adjustable:
  max_per_row  panels in one row (3 reads comfortably on A4 portrait; 4 suits a wider page)
  min_units    narrowest allowed panel (4 of 12 is a third of the row)
A 'full' panel always has a row to itself.
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


def _best_row(prefs, row_units, min_units):
    """The widths for one row of panels with these preferences, or None if none are allowed."""
    if len(prefs) > 1 and row_units in prefs:  # a full-width panel stays alone
        return None
    best = None
    for widths in _compositions(row_units, len(prefs), min_units):
        cost = sum((w - p) ** 2 for w, p in zip(widths, prefs))
        if best is None or cost < best[0]:
            best = (cost, widths)
    return best


def pack_rows(panels, max_per_row=3, row_units=ROW_UNITS, min_units=4):
    """Return rows in reading order; each row is a list of (panel, assigned_units) summing to row_units."""
    n = len(panels)
    prefs = [min(units(p), row_units) for p in panels]
    best = [(0, [])] + [None] * n  # best[i] = (cost, row sizes) for the first i panels
    for i in range(1, n + 1):
        for k in range(1, min(max_per_row, i) + 1):
            if best[i - k] is None:
                continue
            row = _best_row(tuple(prefs[i - k:i]), row_units, min_units)
            if row is None:
                continue
            cost = best[i - k][0] + row[0]
            if best[i] is None or cost < best[i][0]:
                best[i] = (cost, best[i - k][1] + [(k, row[1])])
    rows, at = [], 0
    for k, widths in best[n][1]:
        rows.append(list(zip(panels[at:at + k], widths)))
        at += k
    return rows
