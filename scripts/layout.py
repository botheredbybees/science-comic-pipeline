"""Pack a beat's panels into rows, the way a printed comic reads: left to right, then down.

A row holds ROW_CAPACITY units. A panel's weight says how many it takes. Order is never
changed. A panel that does not fit the room left in a row starts the next one.
"""

UNITS = {"small": 1, "standard": 2, "wide": 3, "full": 4}
ROW_CAPACITY = 4


def units(panel):
    return UNITS[panel.get("weight", "standard")]


def pack_rows(panels, capacity=ROW_CAPACITY):
    """Return a list of rows, each a list of panels, in reading order."""
    rows, row, used = [], [], 0
    for p in panels:
        u = units(p)
        if row and used + u > capacity:
            rows.append(row)
            row, used = [], 0
        row.append(p)
        used += u
    if row:
        rows.append(row)
    return rows
