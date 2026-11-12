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


def test_look_ahead_fills_every_row_and_does_not_repeat_widths():
    rows = pack_rows(panels("wide", "standard", "small", "small"))
    widths = [[u for _, u in r] for r in rows]
    assert [len(r) for r in rows] == [2, 2]
    assert all(sum(w) == 12 for w in widths) and widths[0] != widths[1]


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


def _widths(rows):
    return [tuple(u for _, u in r) for r in rows]


def test_six_equal_panels_do_not_become_three_identical_rows():
    rows = _widths(pack_rows(panels(*(["standard"] * 6))))
    assert len(set(rows)) > 1


def test_no_two_adjacent_rows_have_identical_widths_when_it_can_be_avoided():
    rows = _widths(pack_rows(panels(*(["standard", "small", "wide", "standard"] * 6))))
    assert all(a != b for a, b in zip(rows, rows[1:]))


def test_a_beat_is_nudged_away_from_the_row_before_it():
    plain = _widths(pack_rows(panels("standard", "standard")))
    assert plain == [(6, 6)]
    after = _widths(pack_rows(panels("standard", "standard"), prev=(6, 6)))
    assert after != [(6, 6)]


def test_the_repeat_penalty_never_breaks_the_basic_rules():
    ps = panels(*(["small", "standard", "wide", "full", "standard"] * 7))
    rows = pack_rows(ps, prev=(6, 6))
    assert [p["id"] for r in rows for p, _ in r] == [p["id"] for p in ps]
    assert all(sum(u for _, u in r) == ROW_UNITS and len(r) <= 3 and all(u >= 4 for _, u in r) for r in rows)
