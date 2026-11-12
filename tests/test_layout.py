import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from layout import ROW_UNITS, pack_rows, units  # noqa: E402


def panels(*weights):
    return [{"id": f"B1.{i}", "weight": w} for i, w in enumerate(weights, 1)]


def shape(rows):
    return [[(p["id"], u) for p, u in r] for r in rows]


def test_default_weight_is_standard_a_half_row():
    assert units({"id": "B1.1"}) == 6


def test_exact_fits_keep_their_preferred_widths():
    assert [[u for _, u in r] for r in pack_rows(panels("small", "small", "small"))] == [[4, 4, 4]]
    assert [[u for _, u in r] for r in pack_rows(panels("standard", "standard"))] == [[6, 6]]
    assert [[u for _, u in r] for r in pack_rows(panels("wide", "small"))] == [[8, 4]]


def test_every_row_is_filled_exactly_so_there_are_no_blanks():
    ps = panels(*(["small", "standard", "wide", "standard", "small", "wide", "full", "standard"] * 9))
    for row in pack_rows(ps):
        assert sum(u for _, u in row) == ROW_UNITS


def test_order_is_kept_and_every_panel_is_placed_once():
    ps = panels(*(["small", "standard", "wide", "full"] * 25))
    flat = [p["id"] for r in pack_rows(ps) for p, _ in r]
    assert flat == [p["id"] for p in ps]


def test_limits_are_respected():
    ps = panels(*(["small"] * 40))
    for row in pack_rows(ps, max_per_row=3, min_units=4):
        assert len(row) <= 3 and all(u >= 4 for _, u in row)
    for row in pack_rows(ps, max_per_row=4, min_units=3):
        assert len(row) <= 4 and all(u >= 3 for _, u in row)


def test_full_panel_always_has_a_row_to_itself():
    rows = pack_rows(panels("small", "full", "small", "small"))
    full_row = [r for r in rows if any(p["weight"] == "full" for p, _ in r)][0]
    assert len(full_row) == 1 and full_row[0][1] == ROW_UNITS


def test_look_ahead_beats_filling_each_row_greedily():
    # A greedy packer would put wide and standard together, then squeeze two smalls into halves.
    rows = pack_rows(panels("wide", "standard", "small", "small"))
    assert [len(r) for r in rows] == [2, 2]
    assert [[u for _, u in r] for r in rows] == [[7, 5], [6, 6]]


def test_mismatched_pair_shares_the_difference():
    assert [[u for _, u in r] for r in pack_rows(panels("standard", "wide"))] == [[5, 7]]


def test_a_lone_panel_fills_its_row():
    assert shape(pack_rows(panels("small"))) == [[("B1.1", 12)]]


def test_empty_beat_has_no_rows():
    assert pack_rows([]) == []


@pytest.mark.parametrize("n", [1, 2, 3, 7, 50])
def test_any_number_of_panels_packs(n):
    rows = pack_rows(panels(*(["standard"] * n)))
    assert sum(len(r) for r in rows) == n
