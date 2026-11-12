import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from layout import ROW_CAPACITY, pack_rows, units  # noqa: E402


def panels(*weights):
    return [{"id": f"B1.{i}", "weight": w} for i, w in enumerate(weights, 1)]


def test_default_weight_is_standard():
    assert units({"id": "B1.1"}) == 2


def test_rows_fill_left_to_right_then_down():
    rows = pack_rows(panels("standard", "standard", "wide", "small"))
    assert [[p["id"] for p in r] for r in rows] == [["B1.1", "B1.2"], ["B1.3", "B1.4"]]


def test_a_panel_that_does_not_fit_starts_the_next_row():
    rows = pack_rows(panels("wide", "standard"))
    assert [len(r) for r in rows] == [1, 1]


def test_full_panel_takes_its_own_row():
    rows = pack_rows(panels("small", "full", "small"))
    assert [len(r) for r in rows] == [1, 1, 1]


def test_order_is_kept_and_every_panel_is_placed_once():
    ps = panels(*(["small", "standard", "wide", "full"] * 25))
    rows = pack_rows(ps)
    flat = [p["id"] for r in rows for p in r]
    assert flat == [p["id"] for p in ps]
    assert all(sum(units(p) for p in r) <= ROW_CAPACITY for r in rows)


def test_empty_beat_has_no_rows():
    assert pack_rows([]) == []
